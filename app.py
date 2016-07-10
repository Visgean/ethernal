import ethernal

from flask import Flask
from flask.templating import render_template

app = Flask(__name__)

DONATION_ADDRESS = '0x663aBdde3302C5ecCce0f31467604B03e0d9554c'


@app.route('/')
def home():
    block_obj = ethernal.BlockChain().latest_block
    return render_template(
        'home.html',
        donation_address=DONATION_ADDRESS,
        block=block_obj,
        inline_links=block_obj.get_links()
    )


@app.route('/a/<account>')
def account_detail(account):
    return render_template(
        'account.html',
        account=ethernal.Account(account)
    )


@app.route('/b/<int:block_number>')
@app.route('/b/<block_number>')
def block(block_number):
    block_obj = ethernal.Block(block_number)
    return render_template(
        'block.html',
        block=block_obj,
        inline_links=block_obj.get_links(),
    )


@app.route('/t/<t_hash>')
def transaction(t_hash):
    t = ethernal.Transaction(t_hash)
    return render_template(
        'transaction.html',
        transaction=t,
        inline_links=t.get_links(),
    )
