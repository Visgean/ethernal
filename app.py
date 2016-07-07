import utils

from flask import Flask
from flask.templating import render_template

app = Flask(__name__)


@app.route('/')
@app.route('/<int:block_number>')
def block(block_number=None):
    return render_template(
        'block.html',
        **utils.get_block_dict(block_number)
    )
