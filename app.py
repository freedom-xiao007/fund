import time

from flask import Flask, render_template, request, jsonify

from model import Fund as fund
from model.Analyze import Analyze
from model.MongoDBUtil import MongoDBUtil
from model import Spider

app = Flask(__name__)
analyze = Analyze()


@app.route('/')
def hello_world():
    data = MongoDBUtil.query({'name': 'sort_year'}, "fundAnalyze")
    fund_list = []
    for item in data[0]['data']:
        fund_list.append([item['name'], item['number'], item['year']])
    return render_template('home.html', fund_list=fund_list)


@app.route('/sortEarn')
def sort_earn():
    return render_template('sort.html', fund_list=analyze.sort_earn())


@app.route('/sortEarnYear')
def sort_earn_year():
    year_number = request.args.get('year')
    return render_template('sort.html', fund_list=analyze.sort_earn_year(int(year_number)))


@app.route('/worth')
def worth():
    return render_template('worth.html')


@app.route('/addWorthFund', methods=['POST'])
def add_worth_fund():
    number = str(request.form["number"])
    print("[", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "]:", "fund number ", number)

    ret = MongoDBUtil.query({"number": str(number)}, "fundWorth")
    try:
        print(ret[0])
        dates, values = ret[0]["dates"], ret[0]["values"]
    except Exception as e:
        print("No data")
        dates, values = Spider.get_fund_worth(str(number))
        MongoDBUtil.update({"number": number},
                           {"number": number, "dates": dates, "values": values},
                           "fundWorth")
    return jsonify({"dates": dates, "values": values})


@app.route('/fundData', methods=['POST'])
def getFundData():
    number = str(request.form["name"])
    print("[", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "]:", "fund number ", number)
    ret = MongoDBUtil.query({'number': number}, "fundDetail")
    data = ret[0]['earn']

    value_data = []
    year_data = []
    for item in data:
        for year in item:
            if item[year][2] != '':
                year_data.append(year)
                value_data.append(float(str(item[year][2]).replace('"', "").replace(";", "")))
    return jsonify({'year': year_data, 'value': value_data})


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
