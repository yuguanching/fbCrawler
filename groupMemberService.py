from helper import helper, Auxiliary, thread, proxy, idFetcher, crawlRequests
from ioService import parser, writer, reader
from threading import Thread
from webManager import webDriver, getFbCSRFToken
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

import json
import pandas as pd
import os
import time
import traceback
import configSetting


def runGroupMember(groupMemberDocID):

    return


if __name__ == '__main__':
    # Auxiliary.createIndexExcelAndRead()
    process_worker = configSetting.process_worker

    params, cookie_xs, cookie_cUser = getFbCSRFToken.getCsrfToken()
    cookie_str = f";{cookie_xs['name']}={cookie_xs['value']};{cookie_cUser['name']}={cookie_cUser['value']};"
    fb_dtsg = params['fb_dtsg']

    # target_urls_split = Auxiliary.split(configSetting.jsonArrayData['targetURL'], process_worker)
    # target_names_split = Auxiliary.split(configSetting.jsonArrayData['targetName'], process_worker)

    target_url = "https://www.facebook.com/groups/junrenjulebu"
    target_name = "中華民國軍人俱樂部"
    args_list = []
    result_list = []
    proxy_ip_list = proxy.gRequestsProxyList(0)

    # customDriver 初始化
    group_driver = webDriver.groupMemberDriver(driver=None, options=None, isLogin=False)
    group_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)
    group_driver.driverInitialize()

    # 只為了取docid 特徵值,為避免搜索清單的項目有a.被FB封鎖的 b.沒有任何朋友的 ,故自行於配置檔設定任意一個活著且含朋友群的pofile連結
    # 先取一次profile的docid特徵值(用意是為了有效減少取特徵值的頻率),此次抓取的userid不會使用,故不檢查
    # 先取一次朋友群的docid特徵值(用意是為了有效減少取特徵值的頻率),此次抓取的friendzone_id不會使用,故不檢查
    # get_docid_profile_url = configSetting.jsonArrayData['personProfileDocidTestURL']

    group_id, group_member_docid, group_member_req_name, _ = idFetcher.fetchEigenvaluesAndID(
        func=idFetcher.__getGroupMemberSection__, customDriver=group_driver, errString="未能取得社團成員的docid,嘗試換其他帳號試試", pageURL=target_url, checkOption=1)

    os.environ.pop("account_number_now")
    group_driver.clearDriver()

    group_member_list = crawlRequests.crawlGroupMember(pageURL=target_url, fbDTSG=fb_dtsg, cookieStr=cookie_str, groupID=group_id, docID=group_member_docid,
                                                       reqName=group_member_req_name, proxyIpList=proxy_ip_list, processNum=0, targetName=target_name)

    print(len(group_member_list))
    print("--------------------------------------------")
    print(group_member_list)
    # for i in range(process_worker):
    #     jsonArrayData_copy_temp = configSetting.jsonArrayData.copy()
    #     jsonArrayData_copy_temp['targetURL'] = target_urls_split[i]
    #     jsonArrayData_copy_temp['targetName'] = target_names_split[i]
    #     args_list.append(jsonArrayData_copy_temp)

    # with ProcessPoolExecutor(max_workers=process_worker) as executor:
    #     process_futures = []
    #     print(f"已配置{process_worker}個處理行程等待執行")
    #     for i in range(len(args_list)):
    #         print(f"任務 {i} 植入任務列表")
    #         writer.writeLogToFile("process " + str(i) + " : " + json.dumps(args_list[i]['targetName'], ensure_ascii=False))
    #         process_future = executor.submit(runUserInfo, args_list[i], fb_dtsg, about_docid, friendzone_docid, i)
    #         process_futures.append(process_future)
    #         time.sleep(i/2)  # 避免短時間一次執行多條程序所作的緩衝
    #     for future in as_completed(process_futures):
    #         result_list.append(future.result())
    # for result in result_list:
    #     writer.writeLogToFile(result)

    print("腳本執行完成")
