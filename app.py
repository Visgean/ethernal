from flask import Flask
from flask.templating import render_template
from web3 import Web3, IPCProvider

eth_client = Web3(IPCProvider())
app = Flask(__name__)


@app.route('/')
@app.route('/<int:block>')
def show_block(block=None):
    if block is None:
        block = eth_client.eth.getBlockNumber()
    details = eth_client.eth.getBlock(block)

    # hide annoying bloom filter:
    details['logsBloom'] = details['logsBloom'][:20] + '...'

    return render_template(
        'block.html',
        details=details,
        block=block,
    )

if __name__ == "__main__":
    app.run()
