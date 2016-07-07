from flask import Flask
from flask.templating import render_template
from web3 import Web3, IPCProvider

eth_client = Web3(IPCProvider())
app = Flask(__name__)


SHORT_TRANSACTION_IGNORE_FIELDS = ['blockHash', 'blockNumber']


def get_short_transaction(transaction):
    """
    :param transaction: transcation hash
    :return: Returns dictionary of trans without block info
    """
    info = eth_client.eth.getTranscation(transaction)
    for field in SHORT_TRANSACTION_IGNORE_FIELDS:
        del info[field]
    return info


@app.route('/')
@app.route('/<int:block_number>')
def block(block_number=None):
    if block_number is None:
        block_number = eth_client.eth.getBlockNumber()
    block_info = eth_client.eth.getBlock(block_number)

    # show extra data:
    block_info['extraData'] = eth_client.toAscii(block_info['extraData'])

    # hide annoying bloom filter:
    block_info['logsBloom'] = block_info['logsBloom'][:20] + '..McBLOOMBLOOM'

    # unpack the transactions
    block_info['transactions'] = [
        get_short_transaction(t) for t in block_info['transactions']
    ]

    return render_template(
        'block.html',
        block_info=block_info,
        block_number=block_number,
    )
