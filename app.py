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


@app.route('/worthDetail')
def worth_detail():
    return render_template('worthDetail.html')


@app.route('/fundWorthDetail', methods=['POST'])
def fund_worth_detail():
    args = str(request.form["args"])
    print("args:", args, len(args.split(",")))
    if len(args.split(",")) == 1:
        number = args.split(",")[0]
        begin_date = 0
        end_date = -1
    else:
        number = args.split(",")[0]
        begin_date = args.split(",")[1]
        end_date = args.split(",")[2]
    print("[", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "]:", "fund number ", number, begin_date, end_date)

    ret = MongoDBUtil.query({"number": str(number)}, "fundWorth")
    try:
        print(ret[0])
        dates, values = ret[0]["dates"], ret[0]["values"]

        index_20060104 = 0
        count_20060104 = 0
        for item in dates:
            if item == "20060106":
                index_20060104 = count_20060104
                break
            count_20060104 = count_20060104 + 1

        bengin = 0
        end = 0
        count = -1
        for date in dates:
            count = count + 1
            if date == begin_date:
                bengin = count
            if date == end_date:
                end = count
                break

        date = dates[bengin:end+1]
        value = values[bengin:end+1]
        if begin_date == 0 and end_date == -1:
            date = dates[index_20060104:]
            value = values[index_20060104:]

        print(date)
        print(value)
    except Exception as e:
        print("No data")
    return jsonify({"dates": date, "values": value})


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


@app.route('/getMyFundWorthDetail', methods=["POST", "GET"])
def get_my_fund_worth_detail():
    result_dates, result_values = [], []
    fund_list = ["160106", "163801", "160505", "163302", "257020", "002011", "288002", "240004", "161706", "460001",
                 "161005", "519008", "519001", "377010"]

    for fund_number in fund_list:
        dates, values = Spider.get_fund_worth(str(fund_number))

        index_20060104 = 0
        count_20060104 = 0
        for item in dates:
            if item == "20060106":
                index_20060104 = count_20060104
                break
            count_20060104 = count_20060104 + 1

        date = dates[index_20060104:]
        value = values[index_20060104:]
        result_dates = date
        result_values.append(value)

        print(date)
        print(value)
    return jsonify({'dates': result_dates, 'values': result_values, "funds": fund_list})


@app.route('/myFundWorthDetail')
def my_fund_worth_detail():
    return render_template('myFund.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
