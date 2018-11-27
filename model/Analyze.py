#!/usr/bin/env python
# @Time    : 2018-10-22 15:57
# @Author  : LiuWei
# @Site    :
# @File    : Analyze.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
"""
用于数据尝试分析的模块
"""
import json
from datetime import datetime
from operator import itemgetter

from model.MongoDBUtil import MongoDBUtil
from model import Spider


class Analyze:
    """
    用于检测基金的数据是否获取到
    """

    def check_data(self):
        error_data = []

        ret = MongoDBUtil.query({}, "fundList")
        fund_list = []
        for item in ret:
            fund_list.append([item['name'], item['number']])
        print("Get fund list:", len(fund_list))

        error = 0
        for fund in fund_list:
            try:
                fund_data = MongoDBUtil.query({'number': fund[1]}, 'fundDetail')
                print(fund[0], fund_data[0]['earn'])
            except Exception as e:
                print("Error:", fund[0], fund[1])
                error = error + 1
                error_data.append([fund[0], fund[1]])
        print("Error amount:", error)
        return error_data

    def repair_data(self, fund_list):
        count = 0
        amount = len(fund_list)
        for fund in fund_list:
            count = count + 1
            try:
                number = fund[1]
                situation_data = "empty"
                earn_data = Spider.get_history_earn(number)
                MongoDBUtil.update({"number": number},
                                   {'number': number, 'situation': situation_data, 'earn': earn_data},
                                   "fundDetail")
                print("Repair %s:" % fund[0], count, amount)
            except Exception as e:
                print("Failed %s:" % fund[0], count, amount)

    def sort_year(self):
        ret = MongoDBUtil.query({}, "fundList")
        fund_list = []
        for item in ret:
            fund_list.append([item['name'], item['number']])
        print("Get fund list:", len(fund_list))

        fund_year = []
        empty_count = 0
        for fund in fund_list:
            data = MongoDBUtil.query({'number': fund[1]}, 'fundDetail')
            try:
                first_year = data[0]['earn'][1]
                first_year = eval(str(first_year))
                print(fund[0], data[0]['earn'][1], tuple(first_year.keys())[0])
                fund_year.append({'name': fund[0], 'number': fund[1], 'year': tuple(first_year.keys())[0]})
            except Exception as e:
                empty_count = empty_count + 1
                print("Empty ", fund[0], e)
        print("Empty count:", empty_count, len(fund_list))
        fund_year.sort(key=lambda k: (k.get('year', 0)))
        print(fund_year)

        MongoDBUtil.update({"name": "sort_year"},
                           {'name': "sort_year", 'data': fund_year},
                           "fundAnalyze")

    def sort_earn(self):
        ret = MongoDBUtil.query({}, "fundDetail")
        fund_list = []
        for item in ret:
            if item['earn'] == []:
                continue
            max_value = 0
            year = ""
            for value in item['earn']:
                for key in value:
                    if year == "":
                        year = "1"
                    if year == "1":
                        year = key
                    if value[key][2] == "":
                        continue
                    earn = float(str(value[key][2]).replace('"', "").replace(";", ""))
                    if earn > max_value:
                        max_value = earn
            fund_list.append({'number': item['number'], 'value': max_value, 'year': year})
        fund_list.sort(key=lambda k: (k.get('value', 0)))
        fund_list.reverse()
        print(fund_list)
        return fund_list

    def sort_earn_year(self, year_number):
        ret = MongoDBUtil.query({}, "fundDetail")
        fund_list = []
        for item in ret:
            if item['earn'] == []:
                continue
            max_value = 0
            year = ""
            for value in item['earn']:
                for key in value:
                    if year == "":
                        year = "1"
                    if year == "1":
                        year = key

                    try:
                        int(str(key).split('/')[0])
                    except:
                        continue
                    if int(str(key).split('/')[0]) != year_number:
                        continue

                    if value[key][2] == "":
                        continue
                    earn = float(str(value[key][2]).replace('"', "").replace(";", ""))
                    if earn > max_value:
                        max_value = earn
            fund_list.append({'number': item['number'], 'value': max_value, 'year': year})
        fund_list.sort(key=lambda k: (k.get('value', 0)))
        fund_list.reverse()
        print(fund_list)
        return fund_list

    def long_earn(self, number):
        fund_dict = {}
        for year in range(2015, 2020):
            fund_list = self.sort_earn_year(year)
            fund_list = fund_list[:number]
            print(year, fund_list)
            for fund in fund_list:
                if fund['number'] not in fund_dict:
                    fund_dict[fund['number']] = {}
                    fund_dict[fund['number']]['count'] = 1
                    fund_dict[fund['number']]['number'] = fund['year']
                else:
                    fund_dict[fund['number']]['count'] = fund_dict[fund['number']]['count'] + 1
        index = 0
        for fund in fund_dict:
            index = index + 1
            print(index, fund, fund_dict[fund])

    def count_year(self):
        ret = MongoDBUtil.query({}, "fundDetail")
        year_dict = {}
        for item in ret:
            if item['earn'] == []:
                continue
            try:
                print(item['earn'][5])
                for key in item['earn'][5]:
                    year = str(key).split('/')[0]
                    print(year)
                    if year not in year_dict:
                        year_dict[year] = 1
                    else:
                        year_dict[year] = year_dict[year] + 1
            except:
                continue
        for year in year_dict:
            print(year, year_dict[year])


# 探索数据中的一点范围内的波峰和波谷规律
def find_min_max(dates, values, rate):
    result = {}
    min_value = float(values[0])
    max_value = float(values[0])
    min_date = dates[0]
    max_date = dates[0]
    find_mix = True
    max_count = 0
    worth = {}
    for (date, value_s) in zip(dates, values):
        value = float(value_s)
        worth[date] = value
        if find_mix:
            if value < min_value:
                min_value = value
                min_date = date
            else:
                find_mix = False
                max_value = value
                max_date = date
        else:
            if value > max_value:
                max_value = value
                max_date = date
            elif value < max_value and float(max_value - min_value) / float(min_value) > rate:
                days = datetime.strptime(max_date, '%Y%m%d') - datetime.strptime(min_date, '%Y%m%d')
                # r = str((days, float(max_value - min_value) / float(min_value), min_value, max_value, min_date, max_date))
                r = [days.days, float(max_value - min_value) / float(min_value), min_value, max_value, min_date, max_date]
                print(days, float(max_value - min_value) / float(min_value), min_value, max_value, min_date, max_date)
                year = max_date[:4]
                if year not in result:
                    result[year] = []
                    result[year].append(r)
                else:
                    result[year].append(r)

                max_count = max_count + 1
                min_value = value
                find_mix = True
            elif value < max_value and float(max_value - min_value) / float(min_value) < rate:
                max_value = value
                max_date = date
                if value < min_value:
                    min_value = value
                    min_date = date

    days = datetime.strptime(max_date, '%Y%m%d') - datetime.strptime(min_date, '%Y%m%d')
    print(days, float(max_value - min_value) / float(min_value), min_value, max_value, min_date, max_date)
    # r = str((days, float(max_value - min_value) / float(min_value), min_value, max_value, min_date, max_date))
    r = [days.days, float(max_value - min_value) / float(min_value), min_value, max_value, min_date, max_date]
    year = max_date[:4]
    if year not in result:
        result[year] = []
        result[year].append(r)
    else:
        result[year].append(r)

    year_count = int(dates[-1][:4]) - int(dates[0][:4])
    print(max_count, year_count, year_count * 12)
    # result["result"] = str([max_count, year_count, year_count * 12])
    result["result"] = [max_count, year_count, year_count * 12]
    return max_count, result


def get_fund_worth_data(fund_number):
    return Spider.get_fund_worth(str(fund_number))


def get_fund_rate(fund_number):
    results = {}
    dates, values = get_fund_worth_data(fund_number)
    rate = 0.05
    max_count, result = find_min_max(dates, values, rate)
    results[rate] = result
    while max_count != 0:
        rate = 0.05 + rate
        max_count, result = find_min_max(dates, values, rate)
        results[rate] = result
    with open("C:\\Temp\\fund\\json\\%s.json" % fund_number, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(max_count)


# 读取文件生成收益排序的查看文件
def create_sort_rate():
    with open("C:\\Temp\\fund\\sort.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    sort_str = {}
    for rate in data:
        rate_data = list(data[rate])
        rate_data = sorted(rate_data, key=itemgetter("amount"), reverse=True)
        sort_str["%.02f" % float(rate)] = str(rate_data)
    with open("C:\\Temp\\fund\\sort_str.json", "w", encoding="utf-8") as f:
        json.dump(sort_str, f, ensure_ascii=False, indent=4)


def generate_rate_json():
    fund_list = ["160106", "163801", "160505", "163302", "257020", "002011", "288002", "240004", "161706", "460001",
                 "161005", "519008", "519001", "519668", "377010"]
    sort_result = {}
    for fund_number in fund_list:
        # get_fund_rate(fund_number)
        with open("C:\\Temp\\fund\\json\\%s.json" % fund_number, "r") as f:
            data = json.load(f)
        for rate in data:
            print(data[rate])
            if rate not in sort_result:
                sort_result[rate] = []
                sort_result[rate].append({"fund_number": fund_number, "amount": data[rate]["result"][0],
                                          "month": data[rate]["result"][2]})
            else:
                sort_result[rate].append({"fund_number": fund_number, "amount": data[rate]["result"][0],
                                          "month": data[rate]["result"][2]})
    with open("C:\\Temp\\fund\\sort.json", "w", encoding="utf-8") as f:
        json.dump(sort_result, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    analyze = Analyze()
    # fund_list = analyze.check_data()
    # analyze.repair_data(fund_list)
    # analyze.sort_year()
    # analyze.sort_earn()
    # analyze.sort_earn_year(2009)
    # analyze.long_earn(10)
    # analyze.count_year()
