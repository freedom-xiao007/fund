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
    isConnect = False
    client = None
    db = None

    @staticmethod
    def get_db():
        if MongoDBUtil.isConnect:
            return MongoDBUtil.db
        else:
            MongoDBUtil.connect()

    @staticmethod
    def connect():
        try:
            MongoDBUtil.client = pymongo.MongoClient("mongodb://localhost:27017/")
            MongoDBUtil.db = MongoDBUtil.client["fund"]
            # MongoDBUtil.col = MongoDBUtil.db["fund"]
            MongoDBUtil.isConnect = True
            print("MongoDB连接成功")
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
        MongoDBUtil.col.insert_one(data)
        print("插入成功:", data)

    @staticmethod
    def update(condition, data, collection):
        if not MongoDBUtil.isConnect:
            MongoDBUtil.connect()
        col = MongoDBUtil.db[collection]

        ret = col.find(condition)
        if ret.count() == 0:
            col.insert_one(data)
            print("插入成功:", data)
        else:
            col.update_one(condition, {"$set": data})
            print("更新成功:", data)

    @staticmethod
    def query(condition, collection):
        if not MongoDBUtil.isConnect:
            MongoDBUtil.connect()
        col = MongoDBUtil.db[collection]

        result = col.find(condition)
        return result

    @staticmethod
    def delete(condition):
        return MongoDBUtil.col.delete_one(condition)


if __name__ == "__main__":
    MongoDBUtil.connect()
    # query = {}
    # ret = MongoDBUtil.query(query)
    # for i in ret:
    #     print(i)
    MongoDBUtil.close()
