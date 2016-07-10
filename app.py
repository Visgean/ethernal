import ethernal

from flask import Flask
from flask.templating import render_template
from flask.helpers import url_for

app = Flask(__name__)

DONATION_ADDRESS = '0x663aBdde3302C5ecCce0f31467604B03e0d9554c'


def links_for_transactions(data):
    links = {
        str(data['hash']): url_for('block', block_number=data['hash'])
    }
    if data['from']:
        links[data['from']] = url_for('account_detail', account=data['from'])
    if data['to']:
        links[data['to']] = url_for('account_detail', account=data['to'])

    return links


def links_for_block(data):
    r = {
        data['miner']: url_for('account_detail', account=data['miner']),
    }

    for t in data['transactions']:
        r.update(links_for_transactions(t))
    for u in data['uncles_full']:
        r.update(links_for_block(u))
    return r


@app.route('/')
def home():
    block_obj = ethernal.BlockChain().latest_block
    return render_template(
        'home.html',
        donation_address=DONATION_ADDRESS,
        block=block_obj,
        inline_links=links_for_block(block_obj.content)
    )


@app.route('/a/<account>')
def account_detail(account):
    return render_template(
        'account.html',
        account_info=ethernal.BlockChain().get_account_info(account)
    )


@app.route('/b/<int:block_number>')
@app.route('/b/<block_number>')
def block(block_number):
    block_obj = ethernal.Block(block_number)
    return render_template(
        'block.html',
        block=block_obj,
        inline_links=links_for_block(block_obj.content)
    )


@app.route('/t/<t_hash>')
def transaction(t_hash):
    data = ethernal.BlockChain().get_transaction(t_hash)
    return render_template(
        'transaction.html',
        transaction_info=data,
        inline_links=links_for_transactions(data)
    )
