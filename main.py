from helper import helper, Auxiliary, proxy
from ioService import parser, writer, reader
from threading import Thread
from webManager import webDriver, getFbCSRFToken
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

import os
import requests
import json
import time
import traceback
import configSetting


def runFansPage(jsonArrayDataSub, fbDTSG, processNum) -> str:
    """
    jsonArrayDataSub: 已經透過多行程分配過的輸入資料
    """

    target_urls = jsonArrayDataSub["targetURL"]
    target_names = jsonArrayDataSub["targetName"]

    posts_driver = webDriver.postsDriver(driver=None, options=None, isLogin=False)
    posts_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)
    posts_driver.driverInitialize()

    feedback_driver = webDriver.feedbackDriver(driver=None, options=None, isLogin=False)
    feedback_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)
    feedback_driver.driverInitialize()

    for target_url, target_name in zip(target_urls, target_names):

        # 每個粉專資料有自己的子資料夾存放
        Auxiliary.checkDirAndCreate(target_name)
        proxy_ip_list = proxy.gRequestsProxyList(processNum)
        ip_list_str = json.dumps(proxy_ip_list)
        os.environ['proxy_list'] = ip_list_str

        print(f"開始抓取 {target_name} 的文章資料")
        page_id, page_docid, page_req_name, is_been_banned = helper.fetchEigenvaluesAndID(
            func=helper.__getPageID__, customDriver=posts_driver, errString="未能取得文章的docid 或 pageid,嘗試換其他帳號試試", pageURL=target_url, checkOption=2)
        if is_been_banned:
            writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
            continue

        post_list = helper.crawlPagePosts(pageURL=target_url, pageID=page_id, docID=page_docid, reqName=page_req_name,
                                          proxyIpList=proxy_ip_list, processNum=processNum, targetName=target_name)
        feedback_id_list = parser.buildCollectData(post_list, target_name)
        print(f"{target_name}的feedback_id總數: {len(feedback_id_list)}")

        # 外部先取得feedback的docid,避免多線程重複抓取
        _, feedback_docid, req_name, is_been_banned = helper.fetchEigenvaluesAndID(
            func=helper.__getDocIDFeedback__, customDriver=feedback_driver, errString="未能取得分享的docid,嘗試換其他帳號試試", pageURL=target_url, checkOption=1)
        if is_been_banned:
            writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
            continue

        feedback_data_list = []
        writer.writeLogToFile(
            f"行程{processNum}-> {target_name} 初步統計有 {len(feedback_id_list)} 篇文章要抓分享資料")
        posts_count = 0
        if feedback_docid != "":
            if len(feedback_id_list) != 0:
                q_data = Queue()  # 幫助內部計數用
                q_signal = Queue()  # 信號傳遞交換區
                thread_workers = int(len(feedback_id_list) ** 0.5) * 3
                if thread_workers > 80:
                    thread_workers = 80
                elif thread_workers > 50:
                    thread_workers = 50
                with ThreadPoolExecutor(max_workers=thread_workers) as executor:
                    futures = []
                    print(
                        f"行程{processNum}-> 啟動 {target_name} 的分享數抓取線程共{thread_workers}條")
                    for feedback_id in feedback_id_list:
                        future = executor.submit(helper.crawlFeedback, target_url, feedback_id, feedback_docid,
                                                 posts_count, req_name, fbDTSG, target_name, processNum, q_data, q_signal)
                        futures.append(future)
                    for future in as_completed(futures):
                        try:
                            feedback_data_list.append(future.result())
                        except Exception as thread_e:
                            writer.writeLogToFile(f"行程{processNum}-> 運作時執行緒意外報錯: {thread_e}")
                            writer.writeLogToFile(f"行程{processNum}-> 詳細錯誤原因: {traceback.format_exc()}")
                writer.writeLogToFile(f"行程{processNum}-> {target_name} 結束後統計:{q_data.qsize()}")
            print(
                f"**************************行程{processNum}-> 蒐集完成, {target_name} 共蒐集到{len(feedback_data_list)}筆分享數資料**************************")
            parser.buildDataParse(feedback_data_list, target_name)
            time.sleep(2)  # 給一個寫檔的時間
        else:
            print(f"行程{processNum}-> 沒有抓到個人關於資訊的docid代號,故結束抓取")

    posts_driver.clearDriver()
    feedback_driver.clearDriver()
    return f"行程{processNum}-> 全部執行完成"


if __name__ == '__main__':
    Auxiliary.createIndexExcelAndRead()
    process_worker = configSetting.process_worker

    # params,cookie_xs,cookie_cUser = getFbCSRFToken.getCsrfToken()
    # fb_dtsg = params['fb_dtsg']
    fb_dtsg = ""

    # 按行程的數量平分工作量
    target_url_split = Auxiliary.split(configSetting.jsonArrayData['targetURL'], process_worker)
    target_name_split = Auxiliary.split(configSetting.jsonArrayData['targetName'], process_worker)
    args_list = []
    result_list = []
    for i in range(process_worker):
        jsonArrayData_copy_temp = configSetting.jsonArrayData.copy()
        jsonArrayData_copy_temp['targetURL'] = target_url_split[i]
        jsonArrayData_copy_temp['targetName'] = target_name_split[i]
        args_list.append(jsonArrayData_copy_temp)

    with ProcessPoolExecutor(max_workers=process_worker) as executor:
        process_futures = []
        print(f"已配置{process_worker}個處理行程等待執行")
        for i in range(len(args_list)):
            print(f"任務 {i} 植入任務列表")
            writer.writeLogToFile("process " + str(i) + " : " + json.dumps(args_list[i]['targetName'], ensure_ascii=False))
            process_future = executor.submit(runFansPage, args_list[i], fb_dtsg, i)
            process_futures.append(process_future)
            time.sleep(i/2)  # 避免短時間一次執行多條程序所作的緩衝
        for future in as_completed(process_futures):
            result_list.append(future.result())
    for result in result_list:
        writer.writeLogToFile(result)
    print("腳本執行完成")
