from web3 import Web3, IPCProvider


SHORT_TRANSACTION_IGNORE_FIELDS = ['blockHash', 'blockNumber']


class Block:
    def __init__(self, number, chain=None):
        if chain is None:
            chain = BlockChain()
        self.chain = chain
        self.web3 = chain.web3
        self.number = number

        self.content = self.get_content()

        # assert number <= self.chain.height

    def get_content(self):
        return self._from_ipc()


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
            return None
        return self.number - 1

    @property
    def next_block(self):
        if self.number == 1:
            return None
        return self.number + 1


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
            self.chain.transaction_full(t) for t in block_info['transactions']
        ]

        block_info['uncles_full'] = [
            Block(u, self.chain).content for u in block_info['uncles']
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

    def clean_transaction(self, data):
        data['value'] = self.wei_to_ether(data['value'])
        data['gasPrice'] = self.wei_to_ether(data['gasPrice'])
        data['gas'] = self.web3.toDecimal(data['gas'])
        data['blockNumber'] = self.web3.toDecimal(data['blockNumber'])
        data['tax'] = float(data['gas']) * float(data['gasPrice'])
        try:
            data['input'] = self.web3.toUtf8(data['input'])
        except UnicodeError:
            pass
        return data

    def transaction_full(self, transaction):
        return self.clean_transaction(
            self.web3.eth.getTranscation(transaction)
        )

    def get_account_transaction(self, account):
        """
        This method searches in block and returns all transactions that
        were either received or sent from this account.
        As so far this implementation only searches in last N blocks.
        In order to search the full blockchain some kind of advanced caching
        will have to be implemented. s
        """

        last_blocks = [
            Block(n, self) for n in range(self.height - 100, self.height)
        ]

        transactions = []

        for block in last_blocks:
            for transaction in block.content['transactions']:
                if account in (transaction['from'], transaction['to']):
                    transactions.append(transaction)
        return transactions

    def get_account_info(self, address):
        balance = self.wei_to_ether(self.web3.eth.getBalance(address))
        code = self.web3.eth.getCode(address)

        return {
            'balance': balance,
            'code': code
        }

    def get_transaction(self, t_hash):
        return self.clean_transaction(self.web3.eth.getTranscation(t_hash))
