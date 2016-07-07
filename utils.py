from web3 import Web3, IPCProvider
from web3.web3.exceptions import InvalidResponseException

eth_client = Web3(IPCProvider())

SHORT_TRANSACTION_IGNORE_FIELDS = ['blockHash', 'blockNumber']


def wei_to_ether(wei):
    """Converts 0x wei value to decimal value in ether"""
    return float(eth_client.fromWei(
        eth_client.toDecimal(wei),
        'ether'
    ))


def get_short_transaction(transaction):
    """
    :param transaction: transcation hash
    :return: Returns dictionary of trans without block info
    """
    info = eth_client.eth.getTranscation(transaction)
    for field in SHORT_TRANSACTION_IGNORE_FIELDS:
        del info[field]
    info['value'] = wei_to_ether(info['value'])
    info['gasPrice'] = wei_to_ether(info['gasPrice'])
    info['gas'] = eth_client.toDecimal(info['gas'])
    info['tax'] = float(info['gas']) * float(info['gasPrice'])

    try:
        info['input'] = eth_client.toUtf8(info['input'])
    except UnicodeError:
        pass

    return info


def get_block_info(block_number=None):
    try:
        block_info = eth_client.eth.getBlock(block_number)
    except (KeyError, InvalidResponseException):
        block_number = eth_client.eth.getBlockNumber()
        block_info = eth_client.eth.getBlock(block_number)

    previous_block = block_number - 1
    next_block = block_number + 1

    # show extra data:
    try:
        block_info['extraData'] = eth_client.toUtf8(block_info['extraData'])
    except UnicodeDecodeError:
        pass

    # hide annoying bloom filter:
    block_info['logsBloom'] = block_info['logsBloom'][:20] + '..McBLOOMBLOOM'

    # unpack the transactions
    block_info['transactions'] = [
        get_short_transaction(t) for t in block_info['transactions']
    ]

    return {
        'json_info': block_info,
        'block_number': block_number,
        'previous_block': previous_block,
        'next_block': next_block,
    }
