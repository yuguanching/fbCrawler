from helper import helper, Auxiliary, thread
from ioService import parser, writer,reader
from threading import Thread
from webManager import webDriver
from datetime import datetime
import pandas as pd
import os
import requests
import json
import sys
import time



targetURLs,targetNames = Auxiliary.createIndexExcelAndRead()


for targetURL,targetName in zip(targetURLs,targetNames):

    # 測速的開始時間戳記
    articleTimeStart = datetime.now()
    #每個粉專資料有自己的子資料夾存放
    Auxiliary.checkDirAndCreate(targetName)
    excel_file = './output/' + targetName + '/collectData.xlsx'
    tag_file = './output/' + targetName + '/tag.xlsx'


    print(f"開始抓取 {targetName} 的文章資料")
    postList = helper.Crawl_PagePosts(targetURL)
    feedback_id_list = parser.buildCollectData(postList,subDir=targetName)
    print(f"文章的feedback_id: {feedback_id_list}")

    articleTimeEnd = datetime.now()
    writer.writeLogToFile(f"測速: {targetName}的文章爬取執行時間為 {str(articleTimeEnd - articleTimeStart)}")

    feedbackTimeStart = datetime.now()
    req_thread_list = []
    result_list = []
    # 外部先取得feedback的docid,避免多線程重複抓取

    jsonArrayData = reader.readInputJson()
    accountsLen = len(jsonArrayData['user']['account'])
    for accountNumber in range(0,accountsLen):
        docid,req_name = helper.__get_pageid_feedback__(pageurl=targetURL,accountNumber=accountNumber)
        if docid != "":
            break
        else:
            print("未能取得分享的docid,嘗試換其他帳號試試")
            continue

    if docid != "" or req_name !="none" : 
        posts_count = 0
        for feedback_id in feedback_id_list:
            print(f"啟動 {feedback_id} 的線程...")
            req_thread = thread.ThreadWithReturnValue(target=helper.Crawl_PageFeedback,args=(targetURL,feedback_id,docid,posts_count))
            req_thread.start()
            req_thread_list.append(req_thread)
            posts_count+=1
            time.sleep(3)
        for req_thread in req_thread_list:
            res = req_thread.join()
            result_list.append(res)
        feedbackTimeEnd = datetime.now()
        writer.writeLogToFile(f"測速: {targetName}的分享者爬取執行時間為 {str(feedbackTimeEnd - feedbackTimeStart)}")

        parser.buildDataParse(result_list,subDir=targetName)
    else :
        print("沒有抓到分享者docid代號,故結束抓取")
    finalTimeEnd = datetime.now()
    writer.writeLogToFile(f"測速: {targetName}的總執行時間為 {str(finalTimeEnd - articleTimeStart)}")


print("腳本執行完成")
# testURL = "https://www.facebook.com/%E5%B8%B6%E8%91%97%E7%9B%B8%E6%A9%9F%E5%8E%BB%E6%97%85%E8%A1%8C-101983209137686/"
# docid,req_name = helper.__get_pageid_feedback__(testURL)
# test = "ZmVlZGJhY2s6MTMyOTUzMzI5Mzc0MDA3"
# req_thread_list = []
# result_list = []
# print(f"啟動 {test} 的線程...")
# req_thread = thread.ThreadWithReturnValue(target=helper.Crawl_PageFeedback,args=(testURL,test,docid))
# req_thread.start()
# req_thread_list.append(req_thread)
# for req_thread in req_thread_list:
#     res = req_thread.join()
#     result_list.append(res)

# print(f"最終結果 : {result_list}")

# results = helper.Crawl_PageFeedback("https://www.facebook.com/%E7%A5%9E%E5%A5%87%E5%AF%B6%E8%B2%9D-108610155198388/","ZmVlZGJhY2s6MTIzMTY1MjA3MDc2MjE2")

# print(results)