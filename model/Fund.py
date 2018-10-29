#!/usr/bin/env python
# @Time    : 2018-9-27 21:33
# @Author  : LiuWei
# @Site    : 
# @File    : Fund.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
from model.MongoDBUtil import MongoDBUtil


def fund_list():
    MongoDBUtil.connect()
    ret = MongoDBUtil.query({"fund_name": "list"})
    MongoDBUtil.close()

    funds = []
    for fund in ret[0]["data"]:
        funds.append({
            "name": fund[1],
            "number": fund[0]
        })

    return funds


def get_fund_data(number):
    MongoDBUtil.connect()

    query = {"fund_number": "%06d" % int(number)}
    if number == "":
        query = {}

    rets = MongoDBUtil.query(query)
    MongoDBUtil.close()

    return rets[0]["data"]


if __name__ == "__main__":
    get_fund_data("161725")