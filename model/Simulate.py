# 投资模拟
import json
import traceback
from operator import itemgetter

import requests

from model.MongoDBUtil import MongoDBUtil
from model.Spider import get_fund_worth


def buy(style, rotia, value):
    for item in style.keys():
        if rotia >= item:
            print("买入基金 %f：%f" % (style[item], style[item] / value), end=" ")
            return style[item], style[item] / value
    return 0, 0


def isStopProfit(amount, value, money):
    if money == 0:
        return None

    # profit = {0.2: 1.0, 0.15: 0.75, 0.1: 0.5, 0.05: 0.25}
    profit = {0.2: 1.0, 0.15: 0.75, 0.1: 0.5}
    ratio = (amount * value - money) / money
    for item in profit.keys():
        if ratio >= item:
            print("盈利比：%s" % ratio, end=" ")
            return profit[item]
    return None


def stopProfit(amount, value, profit):
    number = amount * profit
    print("卖出 %f 百分比， 共计： %f 份" % (profit, value * number), end=" ")
    return number, value * number


def getSimulateResult(beginDate, fundNumber, name, dataOrigin):
    if dataOrigin == None:
        dataOrigin = get_fund_worth(fundNumber)
        print(dataOrigin)

    data = {}
    for item in dataOrigin.keys():
        if item >= beginDate:
            data[item] = dataOrigin[item]
    print(data)

    previous = 1.0
    if beginDate in data:
        previous = data[beginDate]

    money = 0
    amount = 0
    allSurplus = 0
    rise = {1.0: 0, 0.7: 1000, 0.5: 200, 0.4: 300, 0.3: 400, 0.0: 500}
    # rise = {0.0: 0}
    decline = {2.0: 5000, 1.5: 4000, 1.0: 3000, 0.5: 2000, 0.3: 1500, 0.0: 1000}

    for item in data:
        print(item, "::", end=" ")
        value = data[item]

        profit = isStopProfit(amount, value, money)
        if profit is not None:
            print("开始止盈了::%f->%f 投入 %f， 总资产：%f " % (previous, value, money, value * amount), end=" ")
            sellCount, surplus = stopProfit(amount, value, profit)
            amount = amount - sellCount
            allSurplus = allSurplus + surplus
        elif value >= previous:
            print("基金上涨买入:: %f->%f" % (previous, value), end=" ")
            rotia = (value - previous) / previous
            cost, number = buy(rise, rotia, value)
            if allSurplus >= cost:
                allSurplus = allSurplus - cost
            else:
                money = money + cost - allSurplus
                allSurplus = 0.0
            amount = amount + number
        else:
            print("基金下行买入:: %f->%f" % (previous, value), end=" ")
            rotia = (previous - value) / previous
            cost, number = buy(decline, rotia, value)
            if allSurplus >= cost:
                allSurplus = allSurplus - cost
            else:
                money = money + cost - allSurplus
                allSurplus = 0.0
            amount = amount + number
        previous = value
        print("::投入 %f, 卖所得: %f 总资产: %f, 盈利：%f" % (money, allSurplus, amount * value + allSurplus, amount * value + allSurplus - money))
    return {"基金代码": fundNumber, "基金名称": name, "投入": money,
            "总资产": amount * previous + allSurplus,
            "盈利": amount * previous + allSurplus - money,
            "盈利率": (amount * previous + allSurplus - money) / money}


def get_fund_worth(fund_number):
    url = "http://fund.10jqka.com.cn/" + fund_number + "/json/jsondwjz.json"
    print("get worth......", fund_number)
    res = requests.get(url, stream=True).text
    # print(res)
    res = str(res)[16:]
    res = json.loads(res)
    # print(res)

    # dates, values = [], []
    worth = {}
    for item in res:
        # dates.append(item[0])
        # values.append(float(item[1]))
        worth[item[0]] = float(item[1])
    print("Successful!!!")
    return worth


def saveFundWorth():
    collection = "worth"
    data = MongoDBUtil.query({}, "fundList")
    amount = data.count()
    skip = 0
    count = 0
    for fund in data:
        print("get %d :: %d" % (count, amount))
        count = count + 1
        if count < skip:
            continue

        number = fund["number"]
        name = fund["name"]
        try:
            MongoDBUtil.insert({"name": name, "number": number, "worth": get_fund_worth(number)}, collection)
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('traceback.format_exc():\n%s' % traceback.format_exc())


def getProfit(beginDate, suffix):
    data = MongoDBUtil.query({}, "worth")
    count = 1
    amount = data.count()
    worthResult = []
    for item in data:
        print("simulate: %d :: %d" % (count, amount))
        name = item["name"]
        number = item["number"]
        worthData = item["worth"]
        try:
            worthResult.append(getSimulateResult(beginDate, number, name, worthData))
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('traceback.format_exc():\n%s' % traceback.format_exc())

    for item in worthResult:
        print(item)

    worthResult.sort(key=itemgetter("盈利率"))
    worthResult.reverse()
    with open("../docs/worth_%s_%s.json" % (beginDate, suffix), "w", encoding="utf-8") as f:
        json.dump(worthResult, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # saveFundWorth()
    # getSimulateResult("20181106", "006401", "先锋量化优选混合A", None)
    # {1.0: 0, 0.7: 1000, 0.5: 200, 0.4: 300, 0.3: 400, 0.0: 500}
    getProfit("10000000", "addBuy1")
    getProfit("20181106", "addBuy1")

