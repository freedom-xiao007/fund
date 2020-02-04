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


def isStopProfit(value, costPrice):
    if costPrice == 0:
        return None

    # profit = {0.2: 1.0, 0.15: 0.75, 0.1: 0.5, 0.05: 0.25}
    profit = {0.2: 1.0, 0.15: 0.75, 0.1: 0.5}
    ratio = (value - costPrice) / costPrice
    for item in profit.keys():
        if ratio >= item:
            print("盈利比：%s" % ratio, end=" ")
            return profit[item]
    return None


def stopProfit(amount, value, profit):
    number = amount * profit
    print("卖出 %f 百分比， 共计： %f 份" % (profit, value * number), end=" ")
    return number, value * number


def getSimulateResult(beginDate, endDate, fundNumber, name, dataOrigin):
    if dataOrigin == None:
        dataOrigin = get_fund_worth(fundNumber)
        print(dataOrigin)

    # 筛选基金年份2006年前成立的
    if "20060106" not in dataOrigin.keys():
        return None

    dataOrigin = sorted(dataOrigin.items(), key=lambda k: k[1], reverse=False)

    data = {}
    for item in dataOrigin.keys():
        if item >= beginDate and item <= endDate:
            data[item] = dataOrigin[item]
    print(data)
    if len(data) == 0:
        return None

    previous = 1.0
    if beginDate in data:
        previous = data[beginDate]

    costPrice = 0
    costMoney = 0
    money = 0
    amount = 0
    allSurplus = 0
    rise = {0.1: 0, 0.0: 100}
    decline = {2.0: 5000, 1.5: 4000, 1.0: 3000, 0.5: 2000, 0.3: 1500, 0.0: 1000}

    for item in data:
        print(item, "::", end=" ")
        value = data[item]

        profit = isStopProfit(value, costPrice)
        if costPrice <= 0:
            print("计算盈利率：%f / %f" % (value, previous), end=" ")
            profit = isStopProfit(value, costPrice)

        if profit is not None:
            print("开始止盈了::%f->%f 投入 %f， 总资产：%f " % (previous, value, money, value * amount), end=" ")
            sellCount, surplus = stopProfit(amount, value, profit)
            amount = amount - sellCount
            allSurplus = allSurplus + surplus
            costMoney = costMoney - surplus
        elif value >= previous and costMoney == 0:
            # print("基金上涨不进行买入操作，进行等待")
            # continue
            print("基金上涨买入:: %f->%f" % (previous, value), end=" ")
            rotia = (value - previous) / previous
            cost, number = buy(rise, rotia, value)
            if allSurplus >= cost:
                allSurplus = allSurplus - cost
            else:
                money = money + cost - allSurplus
                allSurplus = 0.0
            amount = amount + number
            costMoney = costMoney + cost
            costPrice = costMoney / amount
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
            costMoney = costMoney + cost
            costPrice = costMoney / amount
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


def getProfit(beginDate, endDate, suffix):
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
            result = getSimulateResult(beginDate, endDate, number, name, worthData)
            if result is not None:
                worthResult.append(result)
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('traceback.format_exc():\n%s' % traceback.format_exc())

    for item in worthResult:
        print(item)

    worthResult.sort(key=itemgetter("盈利率"))
    worthResult.reverse()
    with open("../docs/X2N/worth_%s_%s_%s.json" % (beginDate, endDate, suffix), "w", encoding="utf-8") as f:
        json.dump(worthResult, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # saveFundWorth()

    # print(getSimulateResult("20001106", "20070200", "161005", "富国天惠成长混合A", None))
    print(getSimulateResult("20070200", "20080400", "161005", "富国天惠成长混合A", None))
    # print(getSimulateResult("20090000", "20160400", "161005", "富国天惠成长混合A", None))
    # print(getSimulateResult("20160300", "20190200", "161005", "富国天惠成长混合A", None))
    # print(getSimulateResult("20160200", "20260400", "161005", "富国天惠成长混合A", None))

    # {1.0: 0, 0.7: 1000, 0.5: 200, 0.4: 300, 0.3: 400, 0.0: 500}
    # getProfit("19990500", "20010600", "ANB")
    # getProfit("20010600", "20071031", "ANB")
    # getProfit("20050500", "20071031", "ANB")

    # getProfit("19990500", "20310600", "NP")
    # getProfit("20181106", "20310600", "NP")

    # 熊市到牛市计算模拟
    # getProfit("20001100", "20070131", "NP")
    # getProfit("20071100", "20090731", "NP")
    # getProfit("20090800", "20100731", "NP")
    # getProfit("20090800", "20101131", "NP")
    # getProfit("20101200", "20150631", "NP")
    # getProfit("20150700", "20550631", "NP")

    # 每年策略计算模拟
    # getProfit("20070000", "20080000", "NP")
    # getProfit("20080000", "20090000", "NP")
    # getProfit("20090000", "20100000", "NP")
    # getProfit("20100000", "20110000", "NP")
    # getProfit("20110000", "20120000", "NP")
    # getProfit("20120000", "20130000", "NP")
    # getProfit("20130000", "20140000", "NP")
    # getProfit("20140000", "20150000", "NP")
    # getProfit("20150000", "20160000", "NP")
    # getProfit("20160000", "20170000", "NP")
    # getProfit("20170000", "20180000", "NP")
    # getProfit("20180000", "20190000", "NP")
    # getProfit("20190000", "20200000", "NP")

    # 处于牛市最巅峰的基金的历史表现如何
