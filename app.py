from flask import Flask, render_template

from model.Fund import fund_list

app = Flask(__name__)


@app.route('/')
def hello_world():
    funds = fund_list()
    return render_template('home.html', funds=funds)


if __name__ == '__main__':
    app.run()
