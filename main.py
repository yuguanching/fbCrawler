from helper import helper, Auxiliary, thread, proxy
from ioService import parser, writer,reader
from threading import Thread
from webManager import webDriver,getFbCSRFToken
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor, as_completed


import pandas as pd
import os
import requests
import json
import sys
import time
import random
import traceback


def runFansPage(jsonArrayData, fb_dtsg, process_num):
    
    targetURLs = jsonArrayData["targetURL"]
    targetNames = jsonArrayData["targetName"]
    for targetURL,targetName in zip(targetURLs,targetNames):

        #每個粉專資料有自己的子資料夾存放
        Auxiliary.checkDirAndCreate(targetName)
        proxy_ip_list = proxy.gRequestsProxyList(process_num=process_num)
        ip_list_str = json.dumps(proxy_ip_list)
        os.environ['proxy_list'] = ip_list_str
        # # 測速的開始時間戳記
        articleTimeStart = datetime.now()
        print(f"開始抓取 {targetName} 的文章資料")
        postList = helper.Crawl_PagePosts(targetURL, jsonArrayData=jsonArrayData, proxy_ip_list=proxy_ip_list, process_num=process_num, targetName=targetName)
        feedback_id_list = parser.buildCollectData(postList,subDir=targetName)
        print(f"文章的feedback_id: {feedback_id_list}")

        articleTimeEnd = datetime.now()
        writer.writeLogToFile(f"測速: {targetName}的文章爬取執行時間為 {str(articleTimeEnd - articleTimeStart)}")

        feedbackTimeStart = datetime.now()

        # 外部先取得feedback的docid,避免多線程重複抓取
        feedback_docid = ""
        accountsLen = len(jsonArrayData['user']['account'])
        account_num = os.environ.get("account_number_now")
        if account_num is None:
            account_num = random.randint(0,accountsLen-1)
        else: 
            account_num = int(account_num)
        while True:
            docid,req_name = helper.__get_pageid_feedback__(pageurl=targetURL,accountNumber=account_num,jsonArrayData=jsonArrayData)
            if docid != "":
                os.environ['account_number_now'] = str(account_num)
                break
            else:
                print("未能取得分享的docid,嘗試換其他帳號試試")
                account_num+=1
                if account_num==accountsLen:
                    account_num = 0
                os.environ['account_number_now'] = str(account_num)
                continue


        feedback_docid = docid
        feedbackDataList = []
        writer.writeLogToFile(f"行程{process_num} : {targetName} 初步統計有 {len(feedback_id_list)} 篇文章要抓分享資料")
        posts_count = 0
        if feedback_docid != "" or req_name !="none" :
            if len(feedback_id_list)!=0: 
                q_data = Queue() #幫助內部計數用
                q_signal = Queue() #信號傳遞交換區
                thread_workers = int(len(feedback_id_list) ** 0.5) * 3
                if thread_workers >80:
                    thread_workers = 80
                elif thread_workers > 50:
                    thread_workers = 50
                with ThreadPoolExecutor(max_workers=thread_workers) as executor:
                    futures = []
                    print(f"行程{process_num} : 啟動 {targetName} 的分享數抓取線程共{thread_workers}條")
                    for feedback_id in feedback_id_list:
                        future = executor.submit(helper.Crawl_PageFeedback,targetURL, feedback_id, feedback_docid, posts_count, req_name, fb_dtsg,targetName, process_num, q_data, q_signal)
                        futures.append(future)
                    for future in as_completed(futures):
                        try:
                            feedbackDataList.append(future.result())
                        except Exception as thread_e :
                            writer.writeLogToFile(f"行程{process_num}運作時執行緒意外報錯: {thread_e}")
                            writer.writeLogToFile(f"行程{process_num}詳細錯誤原因: {traceback.format_exc()}")
                writer.writeLogToFile(f"行程{process_num} : {targetName} 結束後統計:{q_data.qsize()}")
                feedbackTimeEnd = datetime.now()
                writer.writeLogToFile(f"測速: {targetName}的文章分享數爬取執行時間為 {str(feedbackTimeEnd - feedbackTimeStart)}")
            print(f"**************************行程{process_num} : 蒐集完成, {targetName} 共蒐集到{len(feedbackDataList)}筆分享數資料**************************")
            parser.buildFriendzoneData(feedbackDataList,subDir=targetName,targetURL=targetURL)
            time.sleep(2) # 給一個寫檔的時間
        else :
            print("沒有抓到個人關於資訊的docid代號,故結束抓取")
    
    return f"行程{process_num}全部執行完成"

        # if docid != "" or req_name !="none" : 
        #     posts_count = 0
        #     for feedback_id in feedback_id_list:
        #         print(f"啟動 {feedback_id} 的線程...")
        #         req_thread = thread.ThreadWithReturnValue(target=helper.Crawl_PageFeedback,args=(targetURL,feedback_id,docid,posts_count,req_name,fb_dtsg,proxy_ip_list))
        #         req_thread.start()
        #         req_thread_list.append(req_thread)
        #         posts_count+=1
        #         time.sleep(3)
        #     for req_thread in req_thread_list:
        #         res = req_thread.join()
        #         result_list.append(res)
        #     feedbackTimeEnd = datetime.now()
        #     writer.writeLogToFile(f"測速: {targetName}的分享者爬取執行時間為 {str(feedbackTimeEnd - feedbackTimeStart)}")

        #     parser.buildDataParse(result_list,subDir=targetName,jsonArrayData=jsonArrayData)
        # else :
        #     print("沒有抓到分享者docid代號,故結束抓取")
        # finalTimeEnd = datetime.now()
        # writer.writeLogToFile(f"測速: {targetName}的總執行時間為 {str(finalTimeEnd - articleTimeStart)}")

if __name__ == '__main__':
    Auxiliary.createIndexExcelAndRead()
    jsonArrayData = reader.readInputJson()
    process_worker = os.cpu_count() # 16
    # process_worker = 1
    task_num = process_worker
    # params,cookie_xs,cookie_cUser = getFbCSRFToken.get_csrf_token(jsonArrayData=jsonArrayData)
    # fb_dtsg = params['fb_dtsg']
    fb_dtsg = ""

    targetURLs_split = Auxiliary.split(jsonArrayData['targetURL'],task_num)
    targetNames_split = Auxiliary.split(jsonArrayData['targetName'],task_num)
    args_list = []
    result_list = []
    for i in range(task_num):
        jsonArrayData_copy_temp = jsonArrayData.copy()
        jsonArrayData_copy_temp['targetURL'] = targetURLs_split[i]
        jsonArrayData_copy_temp['targetName'] = targetNames_split[i]
        args_list.append(jsonArrayData_copy_temp)
    
    with ProcessPoolExecutor(max_workers=process_worker) as executor:
        process_futures = []
        print(f"已配置{process_worker}個處理行程等待執行")
        for i in range(len(args_list)):
            print(f"任務 {i} 植入任務列表")
            writer.writeLogToFile("process " + str(i) + " : " + json.dumps(args_list[i]['targetName'],ensure_ascii=False))
            process_future = executor.submit(runFansPage,args_list[i], fb_dtsg, i)
            process_futures.append(process_future)
            time.sleep(i/2)    
        for future in as_completed(process_futures):
            result_list.append(future.result())
    for result in result_list:
        writer.writeLogToFile(result)
    print("腳本執行完成")