#!/usr/bin/env python
# @Time    : 2020/2/5 17:10
# @Author  : LiuWei
# @Site    : 
# @File    : ShortStrategy.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
"""短期C类基金买卖策略"""
import json
import operator
import time
import pp

from model import MongoDBUtil


def getAverageMean():
    """
    获取所有基金的平均收益的平均值,和购买记录长度的平均值
    :return:
    """
    with open("../docs/average.json", "r", encoding="utf-8") as f:
        data = json.load(f)

        amount = 0
        number = 0
        for item in data:
            amount = amount + item["average"]
            number = number + item["amount"]
        print(amount / len(data), number / len(data))
    return amount / len(data), number / len(data)


def getupMeanFunds(profitMean, logMean):
    """
    获取平均收益和购买记录长度在平均数上的基金列表
    :param profitMean:
    :param logMean:
    :return:
    """
    with open("../docs/amount.json", "r", encoding="utf-8") as f:
        data = json.load(f)

        count = 0
        fundList = []
        l = []
        for item in data:
            if item["average"] > profitMean * 2 and item["amount"] > logMean * 3:
                print(item["name"], item["number"], item["average"], item["amount"])
                count = count + 1
                fundList.append(item)
                l.append(item["number"])
        print(count, len(data))
        with open("../docs/mean/mean2.json", "w", encoding="utf-8") as f:
            json.dump(fundList, f, ensure_ascii=False, indent=4)
        return l


def getStagger():
    """
    分析基金的购买和卖出是否相互错开
    :return:
    """
    # initDate = datetime.datetime.strptime("2015-01-01", "%Y-%m-%d")
    with open("../docs/mean/mean2.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    buyLog = {}
    sellLog = {}
    for item in data:
        name = item["name"]
        for log in item["log"]:
            buyDate = log[0]
            sellDate = log[1]

            if buyDate in buyLog:
                if name not in buyLog[buyDate]:
                    buyLog[buyDate].append(name)
            else:
                buyLog[buyDate] = []
                buyLog[buyDate].append(name)

            if sellDate in sellLog:
                if name not in sellLog[sellDate]:
                    sellLog[sellDate].append(name)
            else:
                sellLog[sellDate] = []
                sellLog[sellDate].append(name)

    print("*******************BUY*********************************")
    buy = sorted(buyLog.items(), key=lambda k: k[0])
    for item in buy:
        print(item)

    print("*******************SELL*********************************")
    sell = sorted(sellLog.items(), key=lambda k: k[0])
    for item in sell:
        print(item)


def multipleStrategy(funds, base=10000, add=1000, beginStr="2019-01-01 00:00:00", endStr="2020-01-01 00:00:00", dump=False):
    """
    多基金短期策略模拟,默认模拟19年到20年的数据
    :return:
    """
    beginStamp = time.mktime(time.strptime(beginStr, "%Y-%m-%d %H:%M:%S")) * 1000
    endStamp = time.mktime(time.strptime(endStr, "%Y-%m-%d %H:%M:%S")) * 1000
    worthData = {}
    daysAmount = None
    for fund in funds:
        data = MongoDBUtil.MongoDBUtil.query({"number": fund}, "worth_tt")[0]
        name = data["name"]
        worthData[name] = []
        for worth in data["worth"]:
            stamp = int(worth['x'])
            if beginStamp <= stamp < endStamp:
                worthData[name].append({"gain": worth["equityReturn"], "value": worth['y'], "stamp": worth['x']})
        if daysAmount is None:
            daysAmount = len(worthData[name])
        elif daysAmount != len(worthData[name]):
            print("基金年份截取后交易日数量不相等", daysAmount, name, data["number"])
            return None

    invest = {}
    hold = "hold"
    inputMoney = "inputMoney"
    inputDate = "inputDate"
    for name in worthData:
        print(name, len(worthData[name]))
        invest[name] = {"hold": None, "inputMoney": None, "inputDate": None}

    earn = 0
    buyPoint = 1
    addPoint = 0
    sellPoint = 0.03
    baseMoney = base
    addMoney = add
    log = {}
    log["maxInput"] = 0
    log["sellTime"] = 0
    log["monthEarn"] = None
    log["allEarn"] = None
    for i in range(0, daysAmount):
        today = None
        for name in worthData.keys():
            gain = worthData[name][i]["gain"]
            value = worthData[name][i]["value"]
            stamp = worthData[name][i]['stamp'] / 1000
            date = time.strftime("%Y-%m-%d", time.localtime(stamp))
            if today is None:
                today = date
                log[today] = {}
                log[today]['sell'] = []
                log[today]['buy'] = []
            # print(date, name, value, gain)

            if gain < -buyPoint and invest[name]["hold"] is None:
                invest[name][hold] = baseMoney / value
                invest[name][inputMoney] = baseMoney
                invest[name][inputDate] = stamp
                log[today]['buy'].append(str(["初始", gain, name, baseMoney]))
                print(date, name, "初始建仓买入", invest[name][hold], invest[name][inputMoney])
                continue
            if gain < -addPoint and invest[name][hold] is not None:
                invest[name][hold] = invest[name][hold] + addMoney / value
                invest[name][inputMoney] = invest[name][inputMoney] + addMoney
                log[today]['buy'].append(str(["加仓", gain, name, addMoney]))
                print(date, name, "追加买入", invest[name][hold], invest[name][inputMoney])
                continue

            if invest[name][hold] is None:
                print(date, name, "无建仓,无操作")
                continue

            profit = (invest[name][hold] * value - invest[name][inputMoney]) / invest[name][inputMoney]
            if profit < sellPoint:
                print(date, name, "没到达到指定盈利目标,不进行操作", invest[name][inputMoney])
                continue

            day = (int(stamp) - int(invest[name][inputDate])) / (24 * 60 * 60)
            if day < 7:
                print(date, name, "达到目标,但持有不足七天", invest[name][inputMoney])
                continue

            money = invest[name][hold] * value - invest[name][inputMoney]
            earn = earn + money
            log[today]['sell'].append(str(["卖出", day, name, value, profit, invest[name][inputMoney], money]))
            log["sellTime"] = log["sellTime"] + 1
            print(date, day, "卖出 ", name, value, profit, invest[name][inputMoney], money)

            invest[name][hold] = None
            invest[name][inputMoney] = None
            invest[name][inputDate] = None

        input = 0
        for name in worthData.keys():
            if invest[name][inputMoney] is not None:
                input = input + invest[name][inputMoney]
        log[today]['allInput'] = input
        log[today]['allEarn'] = earn
        if log["maxInput"] < input:
            log["maxInput"] = input
        log["monthEarn"] = log[today]["allEarn"] / 12
        log["allEarn"] = earn

    print("总共赚取", earn, "最大投入", log["maxInput"], "交易次数", log["sellTime"])
    if dump:
        with open("../docs/simulate.json", "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=4)
    return log


def simulate(baseFund, funds, index):
    """
    配合多核多线程multiTheadSimulate
    :param baseFund:
    :param funds:
    :param index:
    :return:
    """
    t = []
    for i in range(index + 1, len(funds)):
        for j in range(i + 1, len(funds)):
            group = [baseFund, funds[i], funds[j]]
            r = multipleStrategy(group)
            t.append(str([group, r["allEarn"], r["maxInput"], r["sellTime"]]))
    return t


def multiTheadSimulate():
    """
    使用多核多线程计算三基金组合策略,节省时间
    :return:
    """
    ppservers = ()
    job_server = pp.Server(ppservers=ppservers)

    profitMean, logMean = getAverageMean()
    funds = getupMeanFunds(profitMean, logMean)
    t = []
    jobs = {}
    for i in range(0, len(funds)):
        jobs[funds[i]] = job_server.submit(simulate, (funds[i], funds, i,), (multipleStrategy,), ("time", "MongoDBUtil"))
    job_server.wait()

    for key in jobs.keys():
        r = jobs[key]()
        for item in r:
            t.append(item)
    with open("../docs/multi/3.json", "w", encoding='utf-8') as f:
        json.dump(t, f, ensure_ascii=False, indent=4)


def getFundInfo(funds):
    info = ""
    for number in funds:
        worth = MongoDBUtil.MongoDBUtil.query({"number": number}, "worth_tt")[0]
        name = worth['name']
        stamp = int(worth["worth"][0]['x']) / 1000
        birthday = time.strftime("%Y-%m-%d", time.localtime(int(stamp)))
        info = info + "%s::%s, " % (name, birthday)
    return info


if __name__ == "__main__":
    # multiTheadSimulate()
    # exit(0)

    funds = ["000313", "000241", "001559", "000879", "001618", "000796", "001632", "004231", "001638"]
    # multipleStrategy(funds, dump=True, beginStr="2018-01-01 00:00:00", endStr="2019-01-01 00:00:00")
    multipleStrategy(funds, dump=True, beginStr="2019-01-01 00:00:00", endStr="2020-01-01 00:00:00")
    # multipleStrategy(funds, dump=True, beginStr="2020-02-03 00:00:00", endStr="2020-03-01 00:00:00")


    # profitMean, logMean = getAverageMean()
    # funds = getupMeanFunds(profitMean, logMean)
    # multipleStrategy(funds)

    # t = []
    # earnAverage = 0
    # maxAverage = 0
    # for i in range(0, len(funds)):
    #     group = [funds[i]]
    #     r = multipleStrategy(group, 30000, 3000)
    #     t.append(str([group, r["allEarn"], r["maxInput"], r["sellTime"]]))
    #     earnAverage = earnAverage + r["allEarn"]
    #     maxAverage = maxAverage + r["maxInput"]
    # t.append([earnAverage/len(t), maxAverage/len(t)])
    # with open("../docs/multi/1.json", "w", encoding='utf-8') as f:
    #     json.dump(t, f, ensure_ascii=False, indent=4)
    #
    # t = []
    # earnAverage = 0
    # maxAverage = 0
    # for i in range(0, len(funds)):
    #     for j in range(i+1, len(funds)):
    #         group = [funds[i], funds[j]]
    #         r = multipleStrategy(group, 15000, 1500)
    #         t.append(str([group, r["allEarn"], r["maxInput"], r["sellTime"]]))
    #         earnAverage = earnAverage + r["allEarn"]
    #         maxAverage = maxAverage + r["maxInput"]
    # t.append([earnAverage/len(t), maxAverage/len(t)])
    # with open("../docs/multi/2.json", "w", encoding='utf-8') as f:
    #     json.dump(t, f, ensure_ascii=False, indent=4)

    # t = []
    # earnAverage = 0
    # maxAverage = 0
    # for i in range(0, len(funds)):
    #     for j in range(i+1, len(funds)):
    #         for k in range(j+1, len(funds)):
    #             group = [funds[i], funds[j], funds[k]]
    #             r = multipleStrategy(group)
    #             t.append(str([group, r["allEarn"], r["maxInput"]]))
    #             earnAverage = earnAverage + r["allEarn"]
    #             maxAverage = maxAverage + r["maxInput"]
    # t.append([earnAverage/len(t), maxAverage/len(t)])
    # with open("../docs/3.json", "w", encoding='utf-8') as f:
    #     json.dump(t, f, ensure_ascii=False, indent=4)


    # with open('../docs/multi/3.json', 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    # groupList = []
    # sortBefore = []
    # for item in data:
    #     print(item)
    #     l = list(json.loads(str(item).replace("'", '"')))
    #     if l[1] > 22000:
    #         sortBefore.append({'earn': l[1], 'log': item, 'name': getFundInfo(l[0])})
    #         groupList.append(l[0])
    #
    # sortEnd = sorted(sortBefore, key=operator.itemgetter('earn'), reverse=True)
    # for item in sortEnd:
    #     print(item)
    # print(len(sortEnd))
    # with open("../docs/multi/3sort19000.json", "w", encoding='utf-8') as f:
    #     json.dump(sortEnd, f, ensure_ascii=False, indent=4)
    # with open("../docs/multi/greater19000.json", "w", encoding='utf-8') as f:
    #     json.dump(groupList, f, ensure_ascii=False, indent=4)
    #
    # result = []
    # for funds in groupList:
    #     r = multipleStrategy(funds, beginStr="2018-01-01 00:00:00", endStr="2020-01-01 00:00:00")
    #     result.append(r)
    # sortData = sorted(result, key=operator.itemgetter('allEarn'), reverse=True)
    # with open("../docs/multi/19000simulate.json", "w", encoding='utf-8') as f:
    #     json.dump(sortData, f, ensure_ascii=False, indent=4)


    # getStagger()
