import re
from helper import helper, Auxiliary, thread
from ioService import parser, writer, reader
from threading import Thread
from webManager import webDriver,getFbCSRFToken
from datetime import datetime
import pandas as pd
import os 
import time

targetURLs,targetNames = Auxiliary.createIndexExcelAndRead()
# 先抓取csrf token標記,後續抓取灣於資料要用
params,cookie_xs,cookie_cUser = getFbCSRFToken.get_csrf_token()
fb_dtsg = params['fb_dtsg']
cookieStr = f" ;{cookie_xs['name']}={cookie_xs['value']}; {cookie_cUser['name']}={cookie_cUser['value']};"

os.environ['proxy_list_number'] = '0'

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

    aboutTimeStart = datetime.now()

    jsonArrayData = reader.readInputJson()
    accountsLen = len(jsonArrayData['user']['account'])
    about_docid = ""
    for accountNumber in range(0,accountsLen):
        userid,docid,req_name = helper.__get_userid_section__(pageurl=targetURL,accountNumber=accountNumber)
        if docid != "" and userid!="":
            break
        else:
            print("未能取得個人關於資訊的docid或userid,嘗試換其他帳號試試")
            continue

    about_docid = docid
    aboutContentList = helper.Crawl_Section_About(targetURL,fb_dtsg=fb_dtsg,docid=about_docid,userid=userid,req_name=req_name,targetName=targetName,friendDict=None)
    parser.buildAboutData(aboutContentList,subDir=targetName,targetURL=targetURL)

    aboutTimeEnd = datetime.now()
    writer.writeLogToFile(f"測速: {targetName}的關於資料爬取執行時間為 {str(aboutTimeEnd - aboutTimeStart)}")

    friendTimeStart = datetime.now()
    friendzoneList = helper.Crawl_friendzone(pageurl=targetURL)
    friendzoneDataList = []
    req_thread_list = []

    if about_docid != "" or req_name !="none" : 
        for friend in friendzoneList:
            print(f"啟動{targetName} 的朋友 : {friend['name']} 的線程...")
            req_thread = thread.ThreadWithReturnValue(target=helper.Crawl_Section_About,args=(friend["url"], fb_dtsg, about_docid, friend["userID"], req_name, friend['name'], friend))
            req_thread.start()
            req_thread_list.append(req_thread)
            time.sleep(3)
        for req_thread in req_thread_list:
            res = req_thread.join()
            friendzoneDataList.append(res)
        friendTimeEnd = datetime.now()
        writer.writeLogToFile(f"測速: {targetName}的朋友群資料爬取執行時間為 {str(friendTimeEnd - friendTimeStart)}")
        print("共蒐集到{}筆朋友關於資料".format(len(friendzoneDataList)))
        parser.buildFriendzoneData(friendzoneDataList,subDir=targetName,targetURL=targetURL)
    else :
        print("沒有抓到個人關於資訊的docid代號,故結束抓取")

print("腳本執行完成")
