# 天天基金相关接口使用
import json
import operator
import re
import time
import traceback
from datetime import date
from operator import itemgetter

import requests
import scipy.optimize

from model.MongoDBUtil import MongoDBUtil


def getFundDetail(fundNumber):
    url = "http://fund.eastmoney.com/pingzhongdata/%s.js?v=20160518155842" % fundNumber
    ret = requests.get(url)
    print(ret.text)
    result = str(ret.text)

    date = re.findall("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", result)[0]
    name = re.findall("/\*基金或股票信息\*/var fS_name = \"(?P<name>.*?)\";", result)[0]
    number = re.findall("var fS_code = \"(?P<number>.*?)\";", result)[0]
    print(date, name, number)

    unitValue = re.findall("/\*单位净值走势 equityReturn-净值回报 unitMoney-每份派送金\*/var Data_netWorthTrend = (.*?);"
                           "/\*累计净值走势\*/", result)[0]
    print(json.loads(unitValue))
    return json.loads(unitValue), name, number


def save():
    fundList = MongoDBUtil.query({}, "fundList")
    count = 0
    amount = fundList.count()
    for item in fundList:
        data, name, number = getFundDetail(item["number"])
        print(name, number, date)
        MongoDBUtil.replace({"number": number}, {"name": name, "number": number, "worth": data}, "worth_tt", True)

        print("save %d :: %d" % (count, amount))
        count = count + 1


def buy(style, rotia, value):
    """
    基金买入
    :param style: 买入规则（下降和上涨买入规则）
    :param rotia: 当前基金的涨幅
    :param value: 当前基金净值
    :return: 买入花费的自己，买入的份额
    """
    for item in style.keys():
        if rotia >= item:
            print("买入基金 %f：%f" % (style[item], style[item] / value), end=" ")
            return style[item], style[item] / value
    return 0, 0


def isStopProfit(value, money, amount, rule):
    """
    判断是否达到止盈的标准:盈利率=(当前基金净值*当前持仓份额-持仓投入总资金) / 持仓投入总资金
    :param value: 当前基金的净值
    :param money: 当前持仓投入总资金
    :param amount: 当前持仓份额
    :param rule: 止盈规则
    :return: 卖出的基金份额，不达标返回None
    """
    if money == 0:
        return None

    sellRatio = None
    ratio = (value * amount - money) / money
    for item in rule.keys():
        if ratio >= item and rule[item]["date"] == 0:
            print("止盈卖出，当前净值：%s，当前持仓份额：%s，当前投入资金：%s，盈利率：%s" % (value, amount, money, ratio), end=" ")
            sellRatio = rule[item]["scale"]
            break
    return sellRatio


def stopProfit(amount, value, profit):
    """
    止盈卖出
    :param amount: 当前持仓份额
    :param value: 当前基金净值
    :param profit: 卖出的比例
    :return: 卖出的份额，卖出后获得的总资金
    """
    number = amount * profit
    print("卖出比例：%f，共%f份" % (profit, number), end=" ")
    return number, value * number


def date2Stamp(date):
    # 转换成时间数组
    timeArray = time.strptime(date, "%Y-%m-%d %H:%M:%S")
    # 转换成时间戳
    timestamp = time.mktime(timeArray)
    return timestamp * 1000


def getSimulateResult(beginDate, endDate, fundNumber, name, dataOrigin):
    beginStamp = date2Stamp(beginDate)
    endStamp = date2Stamp(endDate)
    print(beginStamp, endStamp)

    data, _, _ = getFundDetail(fundNumber)

    # 总共投入的资金
    allInputMoney = 0
    # 止盈后的盈利总资金
    allProfitMoney = 0
    # 当前持仓投入总资金
    allHoldMoney = 0
    # 当前持仓份额
    allHoldAmount = 0
    # 基金上涨买入规则
    rise = {0.1: 0, 0.0: 100}
    # 基金下降买入规则
    decline = {2.0: 5000, 1.5: 4000, 1.0: 3000, 0.5: 2000, 0.3: 1500, 0.0: 1000}
    # 止盈规则
    surplusRule = {0.2: {"scale": 1.0, "date": 0}, 0.15: {"scale": 0.75, "date": 0}, 0.1: {"scale": 0.5, "date": 0}}

    # 最后的基金净值
    finalValue = 0
    for item in data:
        if item['x'] < beginStamp or item['x'] > endStamp:
            continue

        # 打印操作日期
        dateTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['x'] / 1000))
        dateTime = dateTime[0:10]
        print(dateTime, "::", end=" ")

        # 当前基金的净值和涨幅
        value = item['y']
        gains = item['equityReturn']
        finalValue = value

        if gains > 0:
            print("上涨 %f" % gains, end=" ")
            profit = isStopProfit(value, allHoldMoney, allHoldAmount, surplusRule)
            if profit is not None:
                # 止盈:盈利总资金上涨，持仓投入总资金和持仓份额下降
                # 止盈前的持仓平均净值
                previousValue = allHoldMoney / allHoldAmount
                sellAmount, sellMoney = stopProfit(allHoldAmount, value, profit)
                allProfitMoney = allProfitMoney + sellMoney
                allHoldAmount = allHoldAmount - sellAmount
                allHoldMoney = allHoldMoney - sellAmount * previousValue
                if allHoldMoney < 0:
                    allHoldMoney = 0
                print("总资金：%f， 持仓投入总资金：%f，持仓份额：%f，投入总资金：%f, 盈利：%f"
                      % (allProfitMoney, allHoldMoney, allHoldAmount, allInputMoney,
                         allHoldAmount * finalValue + allProfitMoney - allInputMoney))
            else:
                print("但没有达到止盈目标")
                # 上涨买入:投入总资金增加（如果止盈资金有剩余，用止盈资金进行买入），持仓总资金和持仓份额增加
                # print("基金上涨买入 %f" % gains, end=" ")
                # money, amount = buy(rise, gains, value)
        else:
            # 下降买入:投入总资金增加（如果止盈资金有剩余，用止盈资金进行买入），持仓总资金和持仓份额增加
            print("基金下降买入 %f" % gains, end=" ")
            money, amount = buy(decline, -gains, value)

            if allProfitMoney >= money:
                allProfitMoney = allProfitMoney - money
            elif allProfitMoney > 0 and allProfitMoney < money:
                allInputMoney = allInputMoney + money - allProfitMoney
                allProfitMoney = 0
            else:
                allInputMoney = allInputMoney + money

            allHoldMoney = allHoldMoney + money
            allHoldAmount = allHoldAmount + amount
            print("总投入：%f，总盈利：%f，持仓总资金：%f，持仓总份额：%f，盈利：%f"
                  % (allInputMoney, allProfitMoney, allHoldMoney, allHoldAmount,
                     allHoldAmount * finalValue + allProfitMoney - allInputMoney))

    return {"基金代码": fundNumber, "基金名称": name, "投入": allInputMoney, "卖出结余": allProfitMoney,
            "总资产": allProfitMoney + allHoldAmount * finalValue,
            "盈利": allHoldAmount * finalValue + allProfitMoney - allInputMoney,
            "盈利率": (allHoldAmount * finalValue + allProfitMoney - allInputMoney) / allInputMoney}


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
            result = getSimulateResult(beginDate, endDate, number, name, None)
            if result is not None:
                worthResult.append(result)
            count = count + 1
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('traceback.format_exc():\n%s' % traceback.format_exc())

    for item in worthResult:
        print(item)

    worthResult.sort(key=itemgetter("盈利率"))
    worthResult.reverse()
    # with open("../docs/1/worth_%s_%s_%s.json" % (beginDate, endDate, suffix), "w", encoding="utf-8") as f:
    with open("../docs/worth1.json", "w", encoding="utf-8") as f:
        json.dump(worthResult, f, ensure_ascii=False, indent=4)


def shortSimulate(number, name, beginDate, endDate, worth, buyPoint, addPoint, sellPoint, maxUpPoint):
    """
    短期策略模拟:下降到指定百分比后进行一次性买入，回升到指定百分比后一次性卖出
    感觉卖点为0.02，两个百分点左右比较合适，资金能快速回流，赚的也差不多；太贪了不行，要遵守纪律
    :param number:
    :param beginDate:
    :param endDate:
    :param worth:
    :param buyPoint:初始投入点位：下降到小于这个百分点后进行初始买入
    :param addPoint:加仓投入点位：降幅不小于这个点位进行加仓
    :param sellPoint:期望最低盈利：希望最低盈利百分比
    :param maxUpPoint:最大涨幅卖出点：有仓位，且一直处于上涨状态中，出现较大幅度上涨时，进行卖出
    :return:
    """
    beginStamp = date2Stamp(beginDate)
    endStamp = date2Stamp(endDate)

    data = worth
    if worth is None:
        data, name, number = getFundDetail(number)

    downCount = {}
    currentValue = None
    currentDate = None
    currentStamp = None
    sellLog = []
    sellMoney = 0.0
    baseMoney = 10000
    holdAmount = None
    for index in range(0, len(data)):
        item = data[index]
        stamp = item["x"]
        dateTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['x'] / 1000))
        value = item["y"]
        gains = item['equityReturn']
        if stamp < beginStamp or stamp > endStamp:
            continue

        print(dateTime[0:10], gains, end=" ")
        ratio = round(gains, 1)
        if ratio <= -buyPoint and holdAmount is None:
            currentDate = dateTime
            currentValue = value
            currentStamp = item['x']
            baseMoney = 50000
            holdAmount = baseMoney / value
            print("------------------初始投入", holdAmount, baseMoney)
            continue
        elif ratio <= -addPoint and holdAmount is not None:
            currentValue = (currentValue + value) / 2
            baseMoney = baseMoney + 3000
            holdAmount = holdAmount + 3000 / value
            print("继续投入", holdAmount, baseMoney, (holdAmount * value - baseMoney) / baseMoney)
            continue

        if ratio in downCount:
            downCount[ratio] = downCount[ratio] + 1
        else:
            downCount[ratio] = 1

        if holdAmount is None:
            print(gains, value, "None")
            continue

        profit = (holdAmount * value - baseMoney) / baseMoney
        print(item["equityReturn"], value, currentValue, profit, end=" ")

        if profit >= sellPoint:
            day = (int(item['x']) - int(currentStamp)) / (24 * 60 * 60 * 1000)
            if day < 7:
                print("持有不足7天, 等一手")
                continue
            else:
                print("持有足7天", end=" ")

            sell = value * holdAmount - baseMoney
            sellMoney = sellMoney + sell
            sellLog.append((currentDate[0:10], dateTime[0:10], currentValue, value, profit, sell, baseMoney))
            print("Sell::", currentDate[0:10], dateTime[0:10], currentValue, value, profit, sell, baseMoney)
            currentValue = None
            holdAmount = None
        else:
            print()

    print(downCount)
    d2 = 0
    amount = 0
    for key in downCount.keys():
        amount = amount + downCount[key]
        if key <= -0.2:
            d2 = d2 + downCount[key]
    print("amount: %d, d2: %d" % (amount, d2))
    print(sellMoney, len(sellLog), sellLog)
    for item in sellLog:
        print(item)
    average = 0
    if len(data) > 0:
        average = sellMoney / len(data)
    return {"name": name, "number": number, "amount": len(sellLog), "average": average, "sellMoney": sellMoney, "log": sellLog}


def getShortResult(stopValue):
    data = MongoDBUtil.query({}, "worth_tt")
    result = []
    begin = "1999-11-06 00:00:00"
    end = "2028-01-01 00:00:00"
    for item in data:
        name = item["name"]
        if name.find("C") == -1:
            # print("不是C短期基金")
            continue
        print(name)

        number = item["number"]
        worth = item["worth"]
        if len(worth) < 600:
            print("基金年限不足两年，不进行模拟")
            continue
        # result.append(shortSimulate(number, name, "2018-11-06 00:00:00", "2028-01-01 00:00:00", worth, stopValue))
        r = shortSimulate(number, name, begin, end, worth, 1, 0.1, 0.02, 1)
        if r['sellMoney'] == 0:
            continue
        # if r["amount"] < 10:
        #     continue
        result.append(r)

    dataSorted = sorted(result, key=operator.itemgetter("amount"), reverse=True)
    with open("../docs/amount.json", "w", encoding="utf-8") as f:
        json.dump(dataSorted, f, ensure_ascii=False, indent=4)


def ratioSimulate():
    data, name, number = getFundDetail("001630")
    name = "天弘中证计算机主题指数C"
    y2015 = "2015-01-01 00:00:00"
    y2016 = "2016-01-01 00:00:00"
    y2017 = "2017-01-01 00:00:00"
    y2018 = "2018-01-01 00:00:00"
    y2019 = "2019-01-01 00:00:00"
    y2020 = "2020-01-01 00:00:00"
    y2021 = "2021-01-01 00:00:00"

    result = {}
    count = 0
    for buyPoint in range(1, 10):
        result[buyPoint] = {}
        for addPoint in range(1, 5):
            result[buyPoint][addPoint] = {}
            for sellPoint in range(1, 10):
                r2015 = shortSimulate(number, name, y2015, y2016, data, buyPoint, addPoint/10, sellPoint/100, 1)
                r2016 = shortSimulate(number, name, y2016, y2017, data, buyPoint, addPoint/10, sellPoint/100, 1)
                r2017 = shortSimulate(number, name, y2017, y2018, data, buyPoint, addPoint/10, sellPoint/100, 1)
                r2018 = shortSimulate(number, name, y2018, y2019, data, buyPoint, addPoint/10, sellPoint/100, 1)
                r2019 = shortSimulate(number, name, y2019, y2020, data, buyPoint, addPoint/10, sellPoint/100, 1)
                result[buyPoint][addPoint][sellPoint] = []
                result[buyPoint][addPoint][sellPoint].append(r2015)
                result[buyPoint][addPoint][sellPoint].append(r2016)
                result[buyPoint][addPoint][sellPoint].append(r2017)
                result[buyPoint][addPoint][sellPoint].append(r2018)
                result[buyPoint][addPoint][sellPoint].append(r2019)
                count = count + 1
                print("*******************", 10*5*10, count, "***************************")
    with open("../docs/001630.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


def downPoint():
    """
    下降点位分析
    :return:
    """
    data, name, number = getFundDetail("001630")
    statistics = {}
    downAmount = 0
    upAmount = 0
    for item in data:
        if item['equityReturn'] < 0:
            downAmount = downAmount + 1
        else:
            upAmount = upAmount + 1

        ratio = round(item['equityReturn'], 1)
        print(ratio)
        if ratio not in statistics:
            statistics[ratio] = 1
        else:
            statistics[ratio] = statistics[ratio] + 1
    print(downAmount, upAmount)

    downS = {}
    for i in range(1, 10):
        value = i / 10
        for key in statistics:
            if key <= -value:
                if -value in downS:
                    downS[-value] = downS[-value] + 1
                else:
                    downS[-value] = 1
    for i in range(1, 10):
        value = i
        for key in statistics:
            if key <= -value:
                if -value in downS:
                    downS[-value] = downS[-value] + 1
                else:
                    downS[-value] = 1
    print(downS)


def up2Down():
    """
    分析大幅上涨后是否伴随大幅下降:保守一点，大涨1个百分点后就卖
    :return:
    """
    data, name, number = getFundDetail("001630")
    u2d = 0
    u2u = 0
    for i in range(0, len(data) - 1):
        today = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data[i]['x'] / 1000))
        tomarow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data[i+1]['x'] / 1000))
        current = data[i]['equityReturn']
        next = data[i+1]['equityReturn']
        if current > 1 and next < 0:
            print("大涨后下降", today[0:10], tomarow[0:10], current, next)
            u2d = u2d + 1
        elif current > 1 and next > 0:
            print("大涨后没下降", today[0:10], tomarow[0:10], current, next)
            u2u = u2u + 1
    print(u2d, u2u)


def printResult():
    """
    好像最佳的点位是：初始买点为1，加仓点位0.1，卖点再看哈
    :return:
    """
    with open("../docs/001630.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for buyPoint in data:
            print()
            for addPoint in data[buyPoint]:
                print()
                for sellPoint in data[buyPoint][addPoint]:
                    print("买点:", buyPoint, "加仓点:", int(addPoint)/10, "买点:", int(sellPoint)/100, end=" ")
                    log = data[buyPoint][addPoint][sellPoint]
                    amount = 0
                    sellAmount = 0
                    for item in log:
                        # print(item["sellMoney"], end=" ")
                        amount = item["sellMoney"] + amount
                        sellAmount = sellAmount + len(item['log'])
                    print(sellAmount, amount)


if __name__ == "__main__":
    # save()
    # downPoint()
    # up2Down()
    # ratioSimulate()
    # printResult()

    # print(shortSimulate("001630", "天弘中证计算机主题指数C", "2000-01-01 00:00:00", "2030-01-01 00:00:00", None, 1, 0.2, 0.02, 1))
    # shortSimulate("001630", "天弘中证计算机主题指数C", "2019-01-01 00:00:00", "2020-01-01 00:00:00", None, 2, 0.2, 0.03, 1)

    # r2015 = shortSimulate("001630", "天弘中证计算机主题指数C", "2015-01-01 00:00:00", "2016-01-01 00:00:00", None, 1, 0.2, 0.02, 1)
    # r2016 = shortSimulate("001630", "天弘中证计算机主题指数C", "2016-01-01 00:00:00", "2017-01-01 00:00:00", None, 1, 0.2, 0.02, 1)
    # r2017 = shortSimulate("001630", "天弘中证计算机主题指数C", "2017-01-01 00:00:00", "2018-01-01 00:00:00", None, 1, 0.2, 0.02, 1)
    # r2018 = shortSimulate("001630", "天弘中证计算机主题指数C", "2018-01-01 00:00:00", "2019-01-01 00:00:00", None, 1, 0.2, 0.02, 1)
    # r2019 = shortSimulate("001630", "天弘中证计算机主题指数C", "2019-01-01 00:00:00", "2020-01-01 00:00:00", None, 1, 0.2, 0.02, 1)
    # shortSimulate("001630", "天弘中证计算机主题指数C", "2020-01-01 00:00:00", "2021-01-01 00:00:00", None, 1, 0.2, 0.02, 1)
    # print(r2015)
    # print(r2016)
    # print(r2017)
    # print(r2018)
    # print(r2019)

    r2019 = shortSimulate("001630", "天弘中证计算机主题指数C", "2019-01-01 00:00:00", "2020-01-01 00:00:00", None, 1, 0.2, 0.02, 1)
    # r2019 = shortSimulate("000313", "天弘中证计算机主题指数C", "2019-01-01 00:00:00", "2020-01-01 00:00:00", None, 1, 0.2, 0.02, 1)
    # r2019 = shortSimulate("519665", "天弘中证计算机主题指数C", "2019-01-01 00:00:00", "2020-01-01 00:00:00", None, 1, 0.2, 0.02, 1)

    # getShortResult(0.025)

    # getFundDetail("161005")
    # print(getSimulateResult("2005-10-01 00:00:00", "2007-02-01 00:00:00", "161005", "富国天惠成长混合A", None))
    # print(getSimulateResult("2018-11-06 00:00:00", "2077-02-01 00:00:00", "161005", "富国天惠成长混合A", None))
    # print(getSimulateResult("2018-11-06 00:00:00", "2077-02-01 00:00:00", "000011", "华夏大盘精选混合", None))
    # print(getSimulateResult("2000-11-06 00:00:00", "2077-02-01 00:00:00", "000011", "华夏大盘精选混合", None))
    # print(getSimulateResult("2018-11-06 00:00:00", "2077-02-01 00:00:00", "110011", "易方达中小盘混合", None))

    # getProfit("2000-06-01 00:00:00", "2027-10-31 00:00:00", "ANB")
