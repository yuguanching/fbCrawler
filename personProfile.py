from helper import helper, Auxiliary, thread
from ioService import parser, writer
from threading import Thread
from webManager import webDriver,getFbCSRFToken
from datetime import datetime
import pandas as pd
import os 

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
    aboutContentList = helper.Crawl_Section_About(targetURL,fb_dtsg=fb_dtsg,cookieStr=cookieStr)
    parser.buildAboutData(aboutContentList,subDir=targetName)

    aboutTimeEnd = datetime.now()
    writer.writeLogToFile(f"測速: {targetName}的關於資料爬取執行時間為 {str(aboutTimeEnd - aboutTimeStart)}")


print("腳本執行完成")
