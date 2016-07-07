import utils

from flask import Flask
from flask.templating import render_template

app = Flask(__name__)

DONATION_ADDRESS = '0x663aBdde3302C5ecCce0f31467604B03e0d9554c'


@app.route('/')
def home():
    return render_template(
        'home.html',
        donation_address=DONATION_ADDRESS,
        **utils.get_block_info()
    )


@app.route('/a/<a_id>')
def account_detail(a_id):
    return render_template(
        'account.html',
        **utils.get_account_info(a_id)
    )


@app.route('/b/<int:block_number>')
def block(block_number=None):
    return render_template(
        'block.html',
        **utils.get_block_info(block_number)
    )
