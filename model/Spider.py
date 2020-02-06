#! /opt/anaconda3/bin/python3.5
# Author: LiuWei
# @Time: 18-8-11 下午1:25
# @Site: 
# @File: Spider.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
import json
import re
import sys
import time
import traceback

import requests
from bs4 import BeautifulSoup

sys.path.append("/home/lw/fund/model/")
from model.MongoDBUtil import MongoDBUtil

stdout = True


def output(msg):
    if stdout:
        print(msg)


def get_html(url):
    res = requests.get(url, stream=True)
    time.sleep(20)
    return res.status_code, res.content


def get_fund_list():
    url = "http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?t=1&lx=1&letter=&gsid=&text=&sort=zdf,desc" \
          "&page=1,9999&feature=|&dt=1534241003763&atfc=&onlySale=0"
    res = requests.get(url, stream=True).text
    fund_list = re.split("datas:", res)[1]
    fund_list = re.split(",count:", fund_list)[0]
    fund_list = json.loads(fund_list)

    data = []
    for fund in fund_list:
        data.append({"name": fund[1], "number": fund[0]})
    print(data)

    for fund in data:
        MongoDBUtil.update({"number": fund["number"]}, fund, "fundList")

    return fund_list


def get_situation(fund_number):
    situation = {}
    url = "http://fundf10.eastmoney.com/jbgk_%s.html" % fund_number
    print("Get fund situation:", url)
    res_code, content = get_html(url)
    if res_code != 200:
        print("Get html failed!")
        return None, None
    html = BeautifulSoup(content, "lxml")
    table = html.find_all("table")[-1]
    trs = table.find_all("tr")
    for tr in trs:
        ths = tr.find_all("th")
        tds = tr.find_all("td")
        if ths[0].text == "销售服务费率" or ths[0].text == "最高申购费率" or ths[0].text == "业绩比较基准":
            continue
        situation[ths[0].text] = tds[0].text
        situation[ths[1].text] = tds[1].text

    url = "http://fundf10.eastmoney.com/tsdata_%s.html" % fund_number
    print("Get fund situation:", url)
    res_code, content = get_html(url)
    if res_code != 200:
        print("Get html failed!")
        return None, None
    html = BeautifulSoup(content, "lxml")
    span = html.find_all("span", class_="chooseLow")[0]
    situation["风险等级"] = span.text

    print(situation)
    return situation


def get_manager(fund_number):
    manager = {}
    manager_change = []
    manager_info = {}

    url = "http://fundf10.eastmoney.com/jjjl_%s.html" % fund_number
    print("Get fund manager:", url)
    res_code, content = get_html(url)
    if res_code != 200:
        print("Get html failed!")
        return None, None

    html = BeautifulSoup(content, "lxml")

    change_div = html.find_all("div", class_="boxitem w790")[0]
    change_tbody = change_div.find_all("tbody")[0]
    change_trs = change_tbody.find_all("tr")
    for change_tr in change_trs:
        change_td = change_tr.find_all("td")
        manager_change.append(
            {
                "起始期": change_td[0].text.replace(" ", ""),
                "截止期": change_td[1].text.replace(" ", ""),
                "基金经理": change_td[2].text.replace(" ", ""),
                "任职期间": change_td[3].text.replace(" ", ""),
                "任职回报": change_td[4].text.replace(" ", ""),
            }
        )

    manager_introduce_div = html.find_all("div", class_="jl_intro")[0]
    # output(manager_introduce_div)
    # manager_introduce_div = BeautifulSoup(manager_introduce_div, "lxml")
    # manager_info_ps = manager_introduce_div.finda_all("a")
    # manager_info["name"] = manager_info_ps[0].text.replace(" ", "")
    # manager_info["assume"] = manager_info_ps[1].text.replace(" ", "")
    # manager_info["introduce"] = manager_info_ps[3].text.replace(" ", "")
    manager_info["name"] = "尤柏年"
    manager_info["assume"] = "2017-11-16"
    manager_info[
        "introduce"] = "尤柏年先生,经济学博士。历任澳大利亚BConnect公司Apex投资咨询团队分析师,华宝兴业基金管理有限公司金融工程部高级数量分析师、海外投资管理部高级分析师、基金经理助理、华宝兴业成熟市场基金和华宝兴业标普油气基金基金经理等职;2014年7月加盟鹏华基金管理有限公司,任职于国际业务部。尤柏年先生具备基金从业资格。"

    manager_experience = []
    manager_experience_div = html.find_all("div", class_="jl_office")[0]
    manager_tbody = manager_experience_div.find_all("tbody")[0]
    manager_info_trs = manager_tbody.find_all("tr")
    for manager_info_tr in manager_info_trs:
        manager_info_tds = manager_info_tr.find_all("td")
        manager_experience.append([
            manager_info_tds[0].text.replace(" ", "").replace(r"\t", ""),
            manager_info_tds[1].text.replace(" ", "").replace(r"\t", ""),
            manager_info_tds[2].text.replace(" ", "").replace(r"\t", ""),
            manager_info_tds[3].text.replace(" ", "").replace(r"\t", ""),
            manager_info_tds[4].text.replace(" ", "").replace(r"\t", ""),
            manager_info_tds[5].text.replace(" ", "").replace(r"\t", ""),
            manager_info_tds[6].text.replace(" ", "").replace(r"\t", ""),
            manager_info_tds[7].text.replace(" ", "").replace(r"\t", ""),
            manager_info_tds[8].text.replace(" ", "").replace(r"\t", ""),
        ])
    manager_info["experience"] = manager_experience

    manager["基金经理变动一览"] = manager_change
    manager["manager"] = manager_info
    return manager


def get_history_earn(fund_number):
    url = "http://fund.eastmoney.com/data/FundPicData.aspx?" \
          "bzdm=%s&n=0&dt=all&vname=ljsylSVG_PicData&r=0.8396031700373916" % fund_number
    print("get earn ......", fund_number)
    res = requests.get(url, stream=True).text

    data = []
    data_day = res.split("|")
    for day in data_day:
        d = day.split("_")
        if len(d) == 4:
            data.append({
                d[0]: [d[1], d[2], d[3]]
            })
    print("Successful!!!")
    return data


class Spider:
    pass


def get_fund_detail():
    data = MongoDBUtil.query({}, "fundList")
    count = 0
    fund_numbers = []
    for fund in data:
        print(fund)
        count = count + 1
        fund_numbers.append(fund['number'])
        print("count:", count)
    print("基金数量：", count)

    count = 0
    for fund in fund_numbers:
        count = count + 1
        try:
            number = fund
            situation_data = get_situation(number)
            earn_data = get_history_earn(number)
            worth_data = get_fund_worth(number)
            MongoDBUtil.replace({"number": number},
                                {'number': number, 'situation': situation_data, 'earn': earn_data,
                                 'worth': worth_data},
                                "fundDetail", True)
        except Exception as e:
            print(e)
            traceback.print_exc()
            print('traceback.format_exc():\n%s' % traceback.format_exc())

        time.sleep(1)
        print("count:", count, len(fund_numbers))


def get_fund_worth(fund_number):
    url = "http://fund.10jqka.com.cn/" + fund_number + "/json/jsondwjz.json"
    print("get worth......", fund_number)
    res = requests.get(url, stream=True).text
    # print(res)
    res = str(res)[16:]
    res = json.loads(res)
    # print(res)

    # dates, values = [], []
    worth = {}
    for item in res:
        # dates.append(item[0])
        # values.append(float(item[1]))
        worth[item[0]] = float(item[1])
    print("Successful!!!")
    return worth


if __name__ == "__main__":
    get_fund_list()
    # get_fund_detail()
    # get_history_earn('005506')
    # get_fund_worth("160106")
    # get_fund_worth("161107")
