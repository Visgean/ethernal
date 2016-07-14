from flask.helpers import url_for

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
    a = ethernal.Account(account)
    return render_template(
        'account.html',
        account=a,
        inline_links=a.get_links()
    )


@app.route('/a/<account>/received/<int:page>')
def transaction_received(account, page):
    return render_template(
        'json_view.html',
        json_info=ethernal.Account(account).transactions_received(page),
        next=url_for('transaction_received', account=account, page=page+1),
        previous=url_for('transaction_received', account=account, page=max((page-1, 1)))
    )


@app.route('/a/<account>/sent/<int:page>')
def transaction_sent(account, page):
    return render_template(
        'json_view.html',
        json_info=ethernal.Account(account).transactions_sent(page),
        next=url_for('transaction_sent', account=account, page=page+1),
        previous=url_for('transaction_sent', account=account, page=max((page-1, 1)))
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
