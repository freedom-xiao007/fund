#!/usr/bin/env python
# @Time    : 2018/9/15 16:12
# @Author  : LiuWei
# @Site    : 
# @File    : MongoDBUtil.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
import time

import pymongo


def output(msg):
    print("[", time.strftime("%Y-%m-%d %H:%M:%S"), time.localtime(), "]::", msg)


class MongoDBUtil:
    @staticmethod
    def connect():
        try:
            MongoDBUtil.client = pymongo.MongoClient("mongodb://localhost:27017/")
            MongoDBUtil.db = MongoDBUtil.client["ttjj"]
            MongoDBUtil.col = MongoDBUtil.db["fund"]
            return True
        except Exception as e:
            print("err: ", e)
            return False

    @staticmethod
    def close():
        try:
            MongoDBUtil.client.close()
            return True
        except Exception as e:
            print("close error: ", e)
            return False

    @staticmethod
    def check():
        MongoDBUtil.connect()
        dblist = MongoDBUtil.client.list_database_names()
        if "fund" not in dblist:
            output("database don't exist")
            return False
        return True

    @staticmethod
    def insert(data):
       return MongoDBUtil.col.insert_one(data)

    @staticmethod
    def update(condition, data):
        ret = MongoDBUtil.query(condition)
        if ret.count() == 0:
            return MongoDBUtil.col.insert_one(data)
        return MongoDBUtil.col.update_one(condition, {"$set": data})

    @staticmethod
    def query(condition):
        return MongoDBUtil.col.find(condition)

    @staticmethod
    def delete(condition):
        return MongoDBUtil.col.delete_one(condition)


if __name__ == "__main__":
    MongoDBUtil.connect()
    query = {}
    ret = MongoDBUtil.query(query)
    for i in ret:
        print(i)
    MongoDBUtil.close()
