
import os
import json
import pandas as pd
import time
import configSetting

from datetime import datetime, timedelta
from ioService import writer, reader


def createIndexExcelAndRead() -> None:

    # 創建目標粉專的目錄excel
    index_df = pd.DataFrame({
        '粉專': configSetting.jsonArrayData['targetName'],
        '連結': configSetting.jsonArrayData['targetURL']
    })
    writer.pdToExcel(des='./output/index.xlsx', df=index_df, sheetName="sheet1")
    print("已完成目標粉專的目錄建置")


def checkDirAndCreate(count) -> None:
    if os.path.exists("./output/" + str(count)):
        print("subDir " + str(count) + " is already exists")
    else:
        os.mkdir("./output/" + str(count))
        os.makedirs("./output/" + str(count) + "/img/sharer")
        os.makedirs("./output/" + str(count) + "/img/been_sharer")
        os.makedirs("./output/" + str(count) + "/img/word_cloud")
        print("subDir " + str(count) + " created successfully")


def detectURL(str: str) -> str:
    return ((str.find("http://") == -1) and (str.find("https://") == -1))


def dateCompare(targetTimeStamp) -> tuple[bool, bool, str]:
    user_start_time_obj = datetime.strptime(configSetting.jsonArrayData["searchStartDate"], "%Y-%m-%d %H:%M:%S")
    user_end_time_obj = datetime.strptime(configSetting.jsonArrayData["searchEndDate"], "%Y-%m-%d %H:%M:%S")

    # 2022/10/29 加入是否從當前時間點作為起點的開關
    if configSetting.jsonArrayData['isTimeEndToCurrent']:
        user_end_time_obj = datetime.now()

    target_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(targetTimeStamp)))
    target_time_obj = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")

    arrive_first_catch_time = True
    if target_time_obj >= user_end_time_obj:
        arrive_first_catch_time = False

    if (target_time_obj > user_start_time_obj) and (target_time_obj < user_end_time_obj):
        return True, arrive_first_catch_time, target_time
    else:
        return False, arrive_first_catch_time, target_time

    # # True : 還能抓 False:不能抓
    # return targetTimeObj > userTimeObj


def makeHyperlink(value, name, index="1") -> str:
    url = "#{}!A{}"
    return '=HYPERLINK("%s", "%s")' % (url.format(value, index), name)


# 陣列分群輔助函式
def split(a, n) -> list:
    k, m = divmod(len(a), n)
    return list((a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n)))


# 嘗試透過profile個人頁連結擷取userid
def parseFBUserID(url) -> str:
    keyword = "?id="
    pos = url.find(keyword)
    if pos == -1:
        return ""
    else:
        userid = url[pos+4:]
        return userid


def checkTimeCooldown(recordTime: datetime) -> bool:
    time_now = datetime.now()

    time_delta = time_now - recordTime
    cooldown = configSetting.cooldown_timedelta

    if cooldown <= time_delta.seconds:
        return True
    else:
        return False
