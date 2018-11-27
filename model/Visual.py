#!/usr/bin/env python
# @Time    : 2018-9-16 9:21
# @Author  : LiuWei
# @Site    : 
# @File    : Visual.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
import csv
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas
from pyecharts import Scatter

from model.MongoDBUtil import MongoDBUtil


def convert_csv():
    MongoDBUtil.connect()

    query = {}
    rets = MongoDBUtil.query(query)

    for ret in rets:
        print(ret)
        if ret["fund_name"] == "list":
            continue

        with open("D:\\临时文件\\基金数据\\%s.csv" % ret["fund_number"], 'w', newline='') as csvfile:
            fieldnames = ["time", "earn", "IF", "SSE"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for data in ret["data"]:
                for key in data:
                    print("write ", str(key).replace('/', '-'), " ", data[key][0], " ", data[key][1], " ",
                          data[key][2])
                    writer.writerow({
                        "time": str(key).replace('/', '-'),
                        "earn": data[key][0],
                        "IF": data[key][1],
                        "SSE": data[key][2],
                    })

    MongoDBUtil.close()


def show(time, value):
    # x = [1, 2, 3, 4]
    # y = [5, 4, 3, 2]
    # figure()
    # plot(np.random.normal(10, .1, len(time)), value)
    # show()

    data = pandas.read_csv("D:\\temp\\160644.csv")
    data.set_index("time")
    print(data.head())
    data["earn"].plot(figsize=(16, 6))
    plt.show()

    return True


def scanter():
    v1, v2 = [], []
    with open("C:\\Temp\\fund\\257020_detail.json", "r") as f:
        data = json.load(f)
    for year in data["0.05"]:
        for item in data["0.05"][year]:
            if len(item) != 1:
                r = str(item).split(",")
                print(r)
                v1.append(float(r[2].replace(" ", "")))
                v1.append(float(r[3].replace(" ", "")))
                v2.append(int(r[4].replace("'", "")))
                v2.append(int(r[5][:-1].replace("'", "")))
    print(v1)
    print(v2)
    # v1 = [10, 20, 30, 40, 50, 60]
    # v2 = [10, 20, 30, 40, 50, 60]
    fund_scanter = Scatter("Fund")
    fund_scanter.add("A", v2, v1, xaxis_min=2000000, xaxis_max=20200000)
    # fund_scanter.add("B", v1[::-1], v2)
    fund_scanter.render()


# 生成总体的单位净值总体图
def create_worth_picture(fund_list):
    pass


if __name__ == "__main__":
    scanter()