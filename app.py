import utils

from flask import Flask
from flask.templating import render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template(
        'home.html',
        **utils.get_block_info()
    )





@app.route('/<int:block_number>')
def block(block_number=None):
    return render_template(
        'block.html',
        **utils.get_block_info(block_number)
    )
