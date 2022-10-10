
import os
import json
import pandas as pd
import time 

from datetime import datetime
from ioService import writer,reader


def createIndexExcelAndRead():

    jsonArrayData = reader.readInputJson()

    # 創建目標粉專的目錄excel
    index_df = pd.DataFrame({
        '粉專':jsonArrayData['targetName'],
        '連結':jsonArrayData['targetURL']
    })
    writer.pdToExcel(des='./output/index.xlsx',df=index_df,sheetName="sheet1")
    print("已完成目標粉專的目錄建置")

    return jsonArrayData['targetURL'],jsonArrayData['targetName']



def checkDirAndCreate(count):
    if os.path.exists("./output/" + str(count)):
        print("subDir " + str(count) + " is already exists")
    else : 
        os.mkdir("./output/" +str(count))
        os.makedirs("./output/" +str(count) + "/img/sharer")
        os.makedirs("./output/" +str(count) + "/img/been_sharer")
        os.makedirs("./output/" +str(count) + "/img/word_cloud")
        print("subDir " + str(count) + " created successfully")


def detectURL(str):
    return ((str.find("http://")== -1 ) and (str.find("https://") == -1))



def dateCompare(targetTimeStamp):
    userSettingTime = reader.readInputJson()
    userTimeObj = datetime.strptime(userSettingTime["searchDate"],"%Y-%m-%d")

    targetTime = time.strftime("%Y-%m-%d",time.localtime(int(targetTimeStamp)))
    targetTimeObj = datetime.strptime(targetTime,"%Y-%m-%d")
    
    # True : 還能抓 False:不能抓
    return targetTimeObj > userTimeObj



def make_hyperlink(value,name,index = "1"):
    url = "#{}!A{}"
    return '=HYPERLINK("%s", "%s")' % (url.format(value,index), name) 