import cached_tools
import rethinkdb as r

from web3 import Web3, IPCProvider
from flask.helpers import url_for


class Transaction:
    def __init__(self, t_hash, chain=None):
        self.t_hash = t_hash
        self.chain = chain or BlockChain()
        self.web3 = self.chain.web3

        self.content_raw = self.web3.eth.getTranscation(t_hash)
        self.content = self._clean_data(self.content_raw)

    def _clean_data(self, data):
        data['value'] = self.chain.wei_to_ether(data['value'])
        data['gasPrice'] = self.chain.wei_to_ether(data['gasPrice'])
        data['gas'] = self.web3.toDecimal(data['gas'])
        data['blockNumber'] = self.web3.toDecimal(data['blockNumber'])
        data['tax'] = float(data['gas']) * float(data['gasPrice'])
        try:
            data['input'] = self.web3.toUtf8(data['input'])
        except UnicodeError:
            pass
        return data

    def get_links(self):
        """
        Inline links for the highlight js. String replacing will be used
        to create the links.
        """
        links = {
            self.content['hash']:
                url_for('transaction', t_hash=self.content['hash']),
            self.content['blockHash']:
                url_for('block', block_number=self.content['blockHash'])
        }
        if self.content['from']:
            links[self.content['from']] = url_for(
                'account_detail', account=self.content['from']
            )
        if self.content['to']:
            links[self.content['to']] = url_for(
                'account_detail', account=self.content['to']
            )
        return links


class Account:
    def __init__(self, account, chain=None):
        self.account = account
        self.chain = chain or BlockChain()
        self.web3 = self.chain.web3
        self.content = self._get_account_info(self.account)

    def get_full_info(self):
        partial = self.content.copy()
        partial.update({
            'blocks_mined': cached_tools.mined_blocks(self.account),
            'sent': cached_tools.transactions_sent(self.account),
            'received': cached_tools.transactions_received(self.account)
        })
        return partial

    def _get_account_info(self, address):
        balance = self.chain.wei_to_ether(self.web3.eth.getBalance(address))
        code = self.web3.eth.getCode(address)

        return {
            'balance': balance,
            'code': code,
        }


class Block:
    def __init__(self, block_id, chain=None):
        self.chain = chain or BlockChain()
        self.web3 = self.chain.web3

        self.content_raw = self._from_ipc(block_id)
        self.transactions = [
            Transaction(t, self.chain)
            for t in self.content_raw['transactions']
        ]

        try:
            self.uncles = [
                Block(u, self.chain) for u in self.content_raw['uncles']
            ]
        except KeyError:
            self.uncles = []

        self.content = self.clean(self.content_raw)
        self.number = self.content['number']

    def get_links(self):
        links = {
            self.content['miner']:
                url_for('account_detail', account=self.content['miner']),
            self.content['parentHash']:
                url_for('block', block_number=self.content['parentHash'])
        }

        for t in self.transactions:
            links.update(t.get_links())
        for u in self.uncles:
            links.update(u.get_links())
        return links

    @property
    def is_fresh(self):
        """
        Is block deep enough in the chain to trust that the chain consensus
        will not change in time?
        """
        return (self.chain.height - self.number) <= 100

    @property
    def previous_block(self):
        if self.number == 1:
            return 1
        return self.number - 1

    @property
    def next_block(self):
        return min(self.chain.height, self.number + 1)

    def _from_ipc(self, block_id):
        return self.web3.eth.getBlock(block_id)

    def clean(self, data):
        # show extra data:
        try:
            data['extraData'] = self.web3.toUtf8(data['extraData'])
        except UnicodeDecodeError:
            pass

        # hide annoying bloom filter:
        data['logsBloom'] = data['logsBloom'][:20] + '...'

        # unpack the transactions
        data['transactions'] = [t.content for t in self.transactions]

        try:
            data['uncles_full'] = [
                Block(u, self.chain).content for u in data['uncles']
            ]
        except KeyError:
            data['uncles_full'] = []
        return data


# noinspection PyBroadException
class BlockChain:
    def __init__(self):
        self.web3 = Web3(IPCProvider())
        self.height = self.web3.eth.getBlockNumber()
        self.db_conn = r.connect("localhost", 28015, 'ethernal')

    def get_sync_work(self):
        """
        Returns range of blocks that need to be added to db
        """
        try:
            last_synced = r.table('blocks').max('number').run(self.db_conn)
            last_block = last_synced['number'] - 100

            # delete all blocks that could be part of shorter chain
            r.table('blocks').filter(
                r.row['number'] > last_block
            ).delete().run(self.db_conn)
        except:
            last_block = 1

        return last_block, self.height

    def sync_block(self, block_n):
        block = Block(block_n, self)
        r.table('blocks').insert(block.content).run(self.db_conn)

    def sync_range(self, start, stop, print_debug=True):
        errors = []

        for block_n in range(start, stop):
            if print_debug and block_n % 100 == 0:
                print(block_n)
            try:
                self.sync_block(block_n)
            except:
                errors.append(block_n)
        return errors

    def sync_simple(self):
        """
        Synchronizes the chain to db in one process
        """
        self.sync_range(*self.get_sync_work())

    @classmethod
    def sync_chunk(cls, chunk):
        chain = cls()
        errors = chain.sync_range(chunk.start, chunk.stop, print_debug=False)
        chain.db_conn.close()

        for block_n in errors:
            for t in range(3):
                try:
                    chain.sync_block(block_n)
                    errors.remove(block_n)
                    break
                except:
                    continue

        del chain
        print(chunk)
        return errors

    def sync_multiprocess(self, processes=None):
        """
        Synchronizes the chain using multiple processes digging trough
        task pool. Task are ranges of blocks that needs to be synced.

        Danger of this approach is that if you interrupt it you will have to
        delete the whole table and create it afterwards.

        Each process has its own IPC and DB connection.
        """

        from multiprocessing import Pool

        pool = Pool(processes=processes)
        chunk_size = 1000

        start, end = self.get_sync_work()
        full_jobs = range(start, end)
        job_chunks = [
            full_jobs[i:i+chunk_size]
            for i in range(start, len(full_jobs), chunk_size)
        ]

        error_lists = pool.map(BlockChain.sync_chunk, job_chunks, chunksize=1)
        print(error_lists)

        print('Sync complete.')

    @property
    def latest_block(self):
        return Block(self.height, chain=self)

    def wei_to_ether(self, wei):
        """Converts 0x wei value to decimal value in ether"""
        return float(self.web3.fromWei(
            self.web3.toDecimal(wei),
            'ether'
        ))
