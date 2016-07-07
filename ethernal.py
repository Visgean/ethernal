import json
import os

from web3 import Web3, IPCProvider


SHORT_TRANSACTION_IGNORE_FIELDS = ['blockHash', 'blockNumber']


class Block:
    """
    Simple cache-balancer:
    - load block from json file if it exist
    - if it is not in cache load it from node and save to cache
    - for last 100 blocks always load from node

    It also does some cleaning and post-processing on the block data
    """

    CACHE_FOLDER = 'blocks/'
    CACHE_FILENAME = '{}.json'

    def __init__(self, number, chain=None):
        # this architecture is still bit messy, block should not rely on chain
        if chain is None:
            chain = BlockChain()
        self.chain = chain
        self.web3 = chain.web3
        self.number = number
        self.number = number

        self.content = self.get_content()

        assert number in range(1, self.chain.height)

    def get_content(self):
        # always reload fresh block numbers - the head is changing on consensus
        if self.is_fresh:
            return self._from_ipc()

        cached = self.get_cache()
        if cached:
            return cached

        data = self._from_ipc()
        self.write_cache(data)
        return data

    def get_cache(self):
        if os.path.exists(self.cache_filename):
            with open(self.cache_filename) as cache:
                return json.loads(cache.read())
        return None

    def write_cache(self, data):
        if os.path.exists(self.cache_filename):
            with open(self.cache_filename, 'w') as cache:
                return cache.write(json.dumps(data))

    @property
    def is_fresh(self):
        """
        Is block deep enough in the chain to trust that the chain consensus
        will not change in time?
        """
        return self.chain.height - self.number <= 100

    @property
    def previous_block(self):
        if self.number == 1:
            return None
        return self.number - 1

    @property
    def next_block(self):
        if self.number == 1:
            return None
        return self.number - 1

    @property
    def cache_filename(self):
        return os.path.join(
            self.CACHE_FOLDER,
            self.CACHE_FILENAME.format(self.number)
        )

    @property
    def cache_exists(self):
        return os.path.exists(self.cache_filename)

    def _from_ipc(self):
        block_info = self.web3.eth.getBlock(self.number)

        # show extra data:
        try:
            block_info['extraData'] = self.web3.toUtf8(block_info['extraData'])
        except UnicodeDecodeError:
            pass

        # hide annoying bloom filter:
        block_info['logsBloom'] = block_info['logsBloom'][:20] + '...'

        # unpack the transactions
        block_info['transactions'] = [
            self.chain.transaction_short(t) for t in block_info['transactions']
        ]

        return block_info


class BlockChain:
    def __init__(self):
        self.web3 = Web3(IPCProvider())
        self.height = self.web3.eth.getBlockNumber()

    @property
    def latest_block(self):
        return Block(self.height, chain=self)

    def wei_to_ether(self, wei):
        """Converts 0x wei value to decimal value in ether"""
        return float(self.web3.fromWei(
            self.web3.toDecimal(wei),
            'ether'
        ))

    def transaction_short(self, transaction):
        """
        :param transaction: transcation hash
        :return: Returns dictionary of trans without block info
        """
        info = self.web3.eth.getTranscation(transaction)
        for field in SHORT_TRANSACTION_IGNORE_FIELDS:
            del info[field]
        info['value'] = self.wei_to_ether(info['value'])
        info['gasPrice'] = self.wei_to_ether(info['gasPrice'])
        info['gas'] = self.web3.toDecimal(info['gas'])
        info['tax'] = float(info['gas']) * float(info['gasPrice'])

        try:
            info['input'] = self.web3.toUtf8(info['input'])
        except UnicodeError:
            pass

        return info

    def get_account_info(self, address):
        balance = self.wei_to_ether(self.web3.eth.getBalance(address))
        code = self.web3.eth.getCode(address)

        return {
            'json_info': {
                'balance': balance,
                'code': code,
            }
        }