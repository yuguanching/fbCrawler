
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
        '粉專': configSetting.json_array_data['targetName'],
        '連結': configSetting.json_array_data['targetURL']
    })
    writer.pdToExcel(des=f'{configSetting.output_root}index.xlsx', df=index_df, sheetName="sheet1")
    print("已完成目標粉專的目錄建置")


def checkDirAndCreate(targetName) -> None:
    if os.path.exists(f"{configSetting.output_root}" + str(targetName)):
        print("subDir " + str(targetName) + " is already exists")
    else:
        os.mkdir(f"{configSetting.output_root}" + str(targetName))
        os.makedirs(f"{configSetting.output_root}" + str(targetName) + "/img/sharer")
        os.makedirs(f"{configSetting.output_root}" + str(targetName) + "/img/been_sharer")
        os.makedirs(f"{configSetting.output_root}" + str(targetName) + "/img/word_cloud")
        os.makedirs(f"{configSetting.output_root}" + str(targetName) + "/img/report")
        print("subDir " + str(targetName) + " created successfully")


def detectURL(str: str) -> str:
    return ((str.find("http://") == -1) and (str.find("https://") == -1))


def dateCompare(targetTimeStamp) -> tuple[bool, bool, str]:
    user_start_time_obj = datetime.strptime(configSetting.json_array_data["searchStartDate"], "%Y-%m-%d %H:%M:%S")
    user_end_time_obj = datetime.strptime(configSetting.json_array_data["searchEndDate"], "%Y-%m-%d %H:%M:%S")

    # 2022/10/29 加入是否從當前時間點作為起點的開關
    if configSetting.json_array_data['isTimeEndToCurrent']:
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
    return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))


# 嘗試透過profile個人頁連結擷取userid
def parseFBUserID(url) -> str:
    keyword = "?id="
    pos = url.find(keyword)
    if pos == -1:
        return ""
    else:
        userid = url[pos + 4:]
        return userid


def checkTimeCooldown(recordTime: datetime) -> bool:
    time_now = datetime.now()

    time_delta = time_now - recordTime
    cooldown = configSetting.cooldown_timedelta

    if cooldown <= time_delta.seconds:
        return True
    else:
        return False


def convert_xls_datetime(xls_date):
    return (datetime(1899, 12, 30)
            + timedelta(days=xls_date))
