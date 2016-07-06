"""
Playground script to connect to geth node and print out last node information.
"""

from web3 import Web3, IPCProvider

client = Web3(IPCProvider())

latest_block_id = client.eth.getBlockNumber()

latest_block = client.eth.getBlock(latest_block_id)
print(latest_block)
