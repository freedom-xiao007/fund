#!/usr/bin/env python
# @Time    : 2018-10-22 15:57
# @Author  : LiuWei
# @Site    :
# @File    : Analyze.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
from model.MongoDBUtil import MongoDBUtil
from model import Spider


class Analyze:
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


if __name__ == "__main__":
    analyze = Analyze()
    # fund_list = analyze.check_data()
    # analyze.repair_data(fund_list)
    # analyze.sort_year()
    # analyze.sort_earn()
    # analyze.sort_earn_year(2009)
    analyze.long_earn(10)
    # analyze.count_year()
