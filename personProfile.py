import re
import threading
from helper import helper, Auxiliary, thread, proxy
from ioService import parser, writer, reader
from threading import Thread
from webManager import webDriver,getFbCSRFToken
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor, as_completed

import json
import pandas as pd
import os 
import time
import traceback
import random


def runUserInfo(jsonArrayData, fb_dtsg, process_num):
    
    targetURLs = jsonArrayData["targetURL"]
    targetNames = jsonArrayData["targetName"]
    for targetURL,targetName in zip(targetURLs,targetNames):


        #每個粉專資料有自己的子資料夾存放
        Auxiliary.checkDirAndCreate(targetName)
        proxy_ip_list = proxy.gRequestsProxyList(process_num=process_num)
        ip_list_str = json.dumps(proxy_ip_list)
        os.environ['proxy_list'] = ip_list_str
        # # 測速的開始時間戳記
        # articleTimeStart = datetime.now()
        # print(f"開始抓取 {targetName} 的文章資料")
        # postList = helper.Crawl_PagePosts(targetURL, jsonArrayData=jsonArrayData, proxy_ip_list=proxy_ip_list, process_num=process_num, targetName=targetName)
        # feedback_id_list = parser.buildCollectData(postList,subDir=targetName)
        # print(f"文章的feedback_id: {feedback_id_list}")

        # articleTimeEnd = datetime.now()
        # writer.writeLogToFile(f"測速: {targetName}的文章爬取執行時間為 {str(articleTimeEnd - articleTimeStart)}")

        about_docid = ""
        accountsLen = len(jsonArrayData['user']['account'])
        account_num = os.environ.get("account_number_now")
        if account_num is None:
            account_num = random.randint(0,accountsLen-1)
        else: 
            account_num = int(account_num)
        while True:
            userid,docid,req_name = helper.__get_userid_section__(pageurl=targetURL,accountNumber=account_num,jsonArrayData=jsonArrayData)
            if docid != "" and userid!="":
                os.environ['account_number_now'] = str(account_num)
                break
            else:
                print("未能取得個人關於資訊的docid或userid,嘗試換其他帳號試試")
                account_num+=1
                if account_num==accountsLen:
                    account_num = 0
                os.environ['account_number_now'] = str(account_num)
                continue



        about_docid = docid
        # aboutTimeStart = datetime.now()
        # aboutContentList = helper.Crawl_Section_About(targetURL,fb_dtsg=fb_dtsg,docid=about_docid,userid=userid,req_name=req_name,targetName=targetName,friendDict=None,proxy_ip_list=proxy_ip_list)
        # parser.buildAboutData(aboutContentList,subDir=targetName,targetURL=targetURL)

        # aboutTimeEnd = datetime.now()
        # writer.writeLogToFile(f"測速: {targetName}的關於資料爬取執行時間為 {str(aboutTimeEnd - aboutTimeStart)}")

        friendTimeStart = datetime.now()
        friendzoneList = helper.Crawl_friendzone(pageurl=targetURL,jsonArrayData=jsonArrayData,proxy_ip_list=proxy_ip_list, process_num=process_num, targetName=targetName)
        friendzoneDataList = []
        writer.writeLogToFile(f"行程{process_num} : {targetName} 初步統計有 {len(friendzoneList)} 個朋友")
        if about_docid != "" or req_name !="none" :
            if len(friendzoneList)!=0: 
                q_data = Queue() #幫助內部計數用
                q_signal = Queue() #信號傳遞交換區
                thread_workers = int(len(friendzoneList) ** 0.5) * 3
                if thread_workers >80:
                    thread_workers = 80
                elif thread_workers > 50:
                    thread_workers = 50
                with ThreadPoolExecutor(max_workers=thread_workers) as executor:
                    futures = []
                    print(f"行程{process_num} : 啟動 {targetName} 的朋友群抓取線程共 {thread_workers} 條")
                    for friend in friendzoneList:
                        future = executor.submit(helper.Crawl_Section_About,friend["url"], fb_dtsg, about_docid, friend["userID"], req_name, targetName, friend, process_num, q_data, q_signal)
                        futures.append(future)
                    for future in as_completed(futures):
                        try:
                            friendzoneDataList.append(future.result())
                        except Exception as thread_e :
                            writer.writeLogToFile(f"行程{process_num}運作時執行緒意外報錯: {thread_e}")
                            writer.writeLogToFile(f"行程{process_num}詳細錯誤原因: {traceback.format_exc()}")
                writer.writeLogToFile(f"行程{process_num} : {targetName} 結束後統計:{q_data.qsize()}")
                friendTimeEnd = datetime.now()
                writer.writeLogToFile(f"測速: {targetName}的朋友群資料爬取執行時間為 {str(friendTimeEnd - friendTimeStart)}")
                del q_data
            print(f"************************** <行程{process_num} : 蒐集完成, {targetName} 共蒐集到{len(friendzoneDataList)}筆朋友關於資料> **************************")
            parser.buildFriendzoneData(friendzoneDataList,subDir=targetName,targetURL=targetURL)
            time.sleep(2) # 給一個寫檔的時間
        else :
            print("沒有抓到個人關於資訊的docid代號,故結束抓取")
    
    return f"行程{process_num}全部執行完成"




if __name__ == '__main__':
    Auxiliary.createIndexExcelAndRead()
    jsonArrayData = reader.readInputJson()
    process_worker = os.cpu_count() # 16
    # process_worker = 1
    task_num = process_worker
    # 先抓取csrf token標記,後續抓取關於資料要用
    params,cookie_xs,cookie_cUser = getFbCSRFToken.get_csrf_token(jsonArrayData=jsonArrayData)
    cookieStr = f" ;{cookie_xs['name']}={cookie_xs['value']}; {cookie_cUser['name']}={cookie_cUser['value']};"
    fb_dtsg = params['fb_dtsg']

    targetURLs_split = Auxiliary.split(jsonArrayData['targetURL'], task_num)
    targetNames_split = Auxiliary.split(jsonArrayData['targetName'], task_num)
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
            process_future = executor.submit(runUserInfo,args_list[i], fb_dtsg, i)
            process_futures.append(process_future)
            time.sleep(i/2)
        for future in as_completed(process_futures):
            result_list.append(future.result())
    for result in result_list:
        writer.writeLogToFile(result)
    print("腳本執行完成")
