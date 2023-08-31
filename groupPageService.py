import os
import requests
import json
import time
import traceback
import configSetting

from helper import helper, Auxiliary, proxy, idFetcher, crawlRequests, thread
from ioService import parser, writer, reader
from threading import Thread
from webManager import webDriver, getFbCSRFToken
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


def runGroupPage(jsonArrayDataSub, fbDTSG, processNum) -> str:
    # 社團的docid抓取和粉專的抓取方式與細節一樣
    """
    jsonArrayDataSub: 已經透過多行程分配過的輸入資料群
    """

    target_urls = jsonArrayDataSub["targetURL"]
    target_names = jsonArrayDataSub["targetName"]

    posts_driver = webDriver.postsDriver(driver=None, options=None, isLogin=False)
    posts_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)
    posts_driver.driverInitialize()

    feedback_driver = webDriver.feedbackDriver(driver=posts_driver.driver, options=None, isLogin=True)
    feedback_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)

    screenshot_driver = webDriver.screenshotDriver(driver=posts_driver.driver, options=None, isLogin=True)
    screenshot_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)

    for target_url, target_name in zip(target_urls, target_names):

        # 每個粉專資料有自己的子資料夾存放
        Auxiliary.checkDirAndCreate(target_name)
        proxy_ip_list = proxy.gRequestsProxyList(processNum)
        ip_list_str = json.dumps(proxy_ip_list)
        os.environ['proxy_list'] = ip_list_str

        feedback_id_list = []
        story_id_list = []
        feedback_data_list = []
        reshares = []

        print(f"開始抓取 {target_name} 的文章資料")
        group_id, group_page_docid, page_req_name, is_been_banned = idFetcher.fetchEigenvaluesAndID(
            func=idFetcher.__getGroupPageID__, customDriver=posts_driver, errString="未能取得文章的docid 或 groupid,嘗試換其他帳號試試", pageURL=target_url, checkOption=2)
        if is_been_banned:
            writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
            continue
        # group_id = "1331244804366090"
        # group_page_docid = "5390522427716337"
        # page_req_name = "GroupsCometFeedRegularStoriesPaginationQuery"

        post_list = crawlRequests.crawlGroupPosts(pageURL=target_url, groupPageID=group_id, groupDocID=group_page_docid, reqName=page_req_name,
                                                  proxyIpList=proxy_ip_list, processNum=processNum, targetName=target_name)
        parser.buildCollectData(post_list, target_name, screenshotDriver=screenshot_driver)
        for posts in post_list:
            feedback_id_list.append(posts['feedback_id'])
            story_id_list.append(posts['story_id'])
        writer.writeLogToFile(f"行程{processNum}-> {target_name} 初步統計有 {len(feedback_id_list)} 篇文章要抓分享資料")

        # 外部先取得feedback的docid,避免多線程重複抓取
        _, feedback_docid, req_name, comment_docid, comment_req_name, is_been_banned = idFetcher.fetchEigenvaluesAndID(
            func=idFetcher.__getDocIDFeedback__, customDriver=feedback_driver, errString="未能取得分享的docid,嘗試換其他帳號試試", pageURL=target_url, checkOption=1)
        if is_been_banned:
            writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
            continue

        if feedback_docid != "":
            if len(feedback_id_list) != 0:
                q_data = Queue()  # 幫助內部計數用
                q_signal = Queue()  # 信號傳遞交換區
                thread_workers = thread.generateThreadWorkers(len(feedback_id_list))
                with ThreadPoolExecutor(max_workers=thread_workers) as executor:
                    print(f"行程{processNum}-> 啟動 {target_name} 的分享數抓取線程共{thread_workers}條")
                    for posts_count, feedback_id in enumerate(feedback_id_list):
                        reshare = executor.submit(crawlRequests.crawlFeedback, target_url, posts_count, feedback_id,
                                                  feedback_docid, req_name, fbDTSG, target_name, processNum, q_data, q_signal)
                        reshares.append(reshare)
                    for reshare in as_completed(reshares):
                        try:
                            feedback_data_list.append(reshare.result())
                        except Exception as thread_e:
                            writer.writeLogToFile(f"行程{processNum}-> 運作時執行緒意外報錯: {thread_e}")
                            writer.writeLogToFile(f"行程{processNum}-> 詳細錯誤原因: {traceback.format_exc()}")
                writer.writeLogToFile(f"行程{processNum}-> {target_name} 結束後統計:{q_data.qsize()}")
                del q_data
                del q_signal
            print(f"**************************行程{processNum}-> 蒐集完成, {target_name} 共蒐集到{len(feedback_data_list)}筆分享數資料**************************")
            parser.buildDataParse(feedback_data_list, target_name, pageID=group_id, screenshotDriver=screenshot_driver)
            time.sleep(2)  # 給一個寫檔的時間
        else:
            print(f"行程{processNum}-> 沒有抓到分享資料的docid代號,故結束抓取")

    feedback_driver.clearDriver()
    posts_driver.clearDriver()
    return f"行程{processNum}-> 全部執行完成"


if __name__ == '__main__':
    Auxiliary.createIndexExcelAndRead()
    process_worker = configSetting.process_worker

    # params,cookie_xs,cookie_cUser = getFbCSRFToken.getCsrfToken()
    # fb_dtsg = params['fb_dtsg']
    # cookie_str = f";{cookie_xs['name']}={cookie_xs['value']};{cookie_cUser['name']}={cookie_cUser['value']};"
    fb_dtsg = ""

    # 按行程的數量平分工作量
    target_url_split = Auxiliary.split(configSetting.json_array_data['targetURL'], process_worker)
    target_name_split = Auxiliary.split(configSetting.json_array_data['targetName'], process_worker)
    args_list = []
    result_list = []
    process_futures = []

    for i in range(process_worker):
        json_array_data_copy_temp = configSetting.json_array_data.copy()
        json_array_data_copy_temp['targetURL'] = target_url_split[i]
        json_array_data_copy_temp['targetName'] = target_name_split[i]
        args_list.append(json_array_data_copy_temp)

    with ProcessPoolExecutor(max_workers=process_worker) as executor:
        print(f"已配置{process_worker}個處理行程等待執行")
        for i in range(len(args_list)):
            print(f"任務 {i} 植入任務列表")
            writer.writeLogToFile("process " + str(i) + " : " + json.dumps(args_list[i]['targetName'], ensure_ascii=False))
            process_future = executor.submit(runGroupPage, args_list[i], fb_dtsg, i)
            process_futures.append(process_future)
            time.sleep(i / 2)  # 避免短時間一次執行多條程序所作的緩衝
        for future in as_completed(process_futures):
            result_list.append(future.result())
    for result in result_list:
        writer.writeLogToFile(result)
    print("腳本執行完成")
