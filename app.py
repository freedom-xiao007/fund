from flask import Flask, render_template, request, jsonify

from model import Fund as fund

app = Flask(__name__)


@app.route('/')
def hello_world():
    funds = fund.fund_list()
    return render_template('home.html', funds=funds)


@app.route('/getFundData', methods=['GET'])
def getFundData():
    r = request.values.to_dict()
    print(r['number'])
    fund_data = fund.get_fund_data(str(r['number']))
    return jsonify({"fund_data": fund_data})


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
