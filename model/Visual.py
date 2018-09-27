#!/usr/bin/env python
# @Time    : 2018-9-16 9:21
# @Author  : LiuWei
# @Site    : 
# @File    : Visual.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
import csv

import matplotlib.pyplot as plt
import numpy as np
import pandas

from model.MongoDBUtil import MongoDBUtil


class Visual:
    def show(self, time, value):
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

    def convertCSV(self):
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


if __name__ == "__main__":
    visual = Visual()
    # visual.convertCSV()
    visual.show(1, 2)