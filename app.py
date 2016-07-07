import utils

from flask import Flask
from flask.templating import render_template

app = Flask(__name__)

DONATION_ADRESS = '0x663aBdde3302C5ecCce0f31467604B03e0d9554c'


@app.route('/')
def home():
    return render_template(
        'home.html',
        donation_adress=DONATION_ADRESS,
        **utils.get_block_info()
    )


@app.route('/t/<t_id>')
def transaction_detail(t_id):
    pass


@app.route('/b/<int:block_number>')
def block(block_number=None):
    return render_template(
        'block.html',
        **utils.get_block_info(block_number)
    )
