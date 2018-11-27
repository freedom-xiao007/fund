#!/usr/bin/env python
# @Time    : 2018-9-27 21:33
# @Author  : LiuWei
# @Site    : 
# @File    : Fund.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
from model.MongoDBUtil import MongoDBUtil
from model import Spider


def get_fund_list(update):
    if update:
        print(Spider.get_fund_list())

    ret = MongoDBUtil.query({}, "fundList")
    fund_list = []
    for item in ret:
            fund_list.append(item['number'])
    print("Get fund list:", len(fund_list), fund_list)

    return fund_list


def get_fund_data(number):
    MongoDBUtil.connect()

    query = {"fund_number": "%06d" % int(number)}
    if number == "":
        query = {}

    rets = MongoDBUtil.query(query)
    MongoDBUtil.close()

    return rets[0]["data"]


def get_fund_worth(number):
    ret = MongoDBUtil.query({"number": str(number)}, "fundWorth")
    dates, values = ret[0]["dates"], ret[0]["values"]
    print(number, dates)
    # print(values)
    return dates, values


def update_fund_worth(fund_list):
    for fund_number in fund_list:
        try:
            dates, values = Spider.get_fund_worth(str(fund_number))
            MongoDBUtil.update({"number": fund_number},
                               {"number": fund_number, "dates": dates, "values": values},
                               "fundWorth")
        except Exception as e:
            print(e)


if __name__ == "__main__":
    # get_fund_data("161725")

    # fund_list = ["160106", "163801", "160505", "163302", "257020", "002011", "288002", "240004", "161706", "460001",
    #              "161005", "519008", "519001", "519668", "377010"]
    # update_fund_worth(fund_list)

    # for fund_number in fund_list:
    #     get_fund_worth(fund_number)

    fund_list = get_fund_list(False)
    update_fund_worth(fund_list)
