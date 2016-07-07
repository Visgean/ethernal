import ethernal

from flask import Flask
from flask.templating import render_template

app = Flask(__name__)

DONATION_ADDRESS = '0x663aBdde3302C5ecCce0f31467604B03e0d9554c'


@app.route('/')
def home():
    return render_template(
        'home.html',
        donation_address=DONATION_ADDRESS,
        block=ethernal.BlockChain().latest_block,
    )


@app.route('/a/<account>')
def account_detail(account):
    return render_template(
        'account.html',
        account_info=ethernal.BlockChain().get_account_info(account)
    )


@app.route('/b/<int:block_number>')
def block(block_number):
    return render_template(
        'block.html',
        block=ethernal.Block(block_number)
    )
