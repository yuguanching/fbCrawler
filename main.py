import grequests
import os
import json
import time
import traceback
import configSetting


from helper import Auxiliary, proxy, idFetcher, crawlRequests, thread
from ioService import parser, writer, reader
from threading import Thread
from webManager import webDriver, getFbCSRFToken
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


def runFansPage(jsonArrayDataSub, fbDTSG, processNum) -> str:
    """
    jsonArrayDataSub: 已經透過多行程分配過的輸入資料
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
        comments_data_list = []
        comments = []
        feedback_data_list = []
        reshares = []

        print(f"開始抓取 {target_name} 的文章資料")
        page_id, page_docid, page_req_name, is_been_banned = idFetcher.fetchEigenvaluesAndID(
            func=idFetcher.__getPageID__, customDriver=posts_driver, errString="未能取得文章的docid 或 pageid,嘗試換其他帳號試試", pageURL=target_url, checkOption=2)
        if is_been_banned:
            writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
            continue
        # page_id = "100050029991173"
        # page_docid = "6266011703492935"
        # page_req_name = "ProfileCometTimelineFeedRefetchQuery"

        if configSetting.feedback_manual:  # 是否手動餵檔單獨處理分享者資料
            with open('./temp/feedback_id_list.txt', 'r') as file:
                fil = file.read()
            fil = fil.replace("\'", "", -1)
            fil_res = fil.strip('][').split(', ')
            feedback_id_list = fil_res
        else:
            post_list = crawlRequests.crawlPagePosts(pageURL=target_url, pageID=page_id, docID=page_docid, reqName=page_req_name,
                                                     proxyIpList=proxy_ip_list, processNum=processNum, targetName=target_name)
            parser.buildCollectData(post_list, target_name, screenshotDriver=screenshot_driver)
            for posts in post_list:
                feedback_id_list.append(posts['feedback_id'])
                story_id_list.append(posts['story_id'])

        writer.writeLogToFile(f"行程{processNum}-> {target_name} 初步統計有 {len(feedback_id_list)} 篇文章要抓留言、分享資料")
        writer.writeLogToFile(feedback_id_list)
        writer.writeLogToFile(story_id_list)
        os.environ['feedback_id_list_len'] = str(len(feedback_id_list))
        # 外部先取得feedback的docid,避免多線程重複抓取
        _, feedback_docid, req_name, comment_docid, comment_req_name, is_been_banned = idFetcher.fetchEigenvaluesAndID(
            func=idFetcher.__getDocIDFeedback__, customDriver=feedback_driver, errString="未能取得分享的docid,嘗試換其他帳號試試", pageURL=target_url, checkOption=1)
        if is_been_banned:
            writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
            continue

        if comment_docid != "":
            if len(feedback_id_list) == len(story_id_list):
                q_data = Queue()  # 幫助內部計數用
                q_signal = Queue()  # 信號傳遞交換區
                thread_workers = thread.generateThreadWorkers(len(feedback_id_list))
                with ThreadPoolExecutor(max_workers=thread_workers) as executor:
                    print(f"行程{processNum}-> 啟動 {target_name} 的留言數抓取線程共{thread_workers}條")
                    for posts_count, (feedback_id, story_id) in enumerate(zip(feedback_id_list, story_id_list)):
                        comment = executor.submit(crawlRequests.crawlPostsComments, target_url, posts_count, feedback_id, story_id,
                                                  comment_docid, comment_req_name, fbDTSG, target_name, processNum, q_data, q_signal)
                        comments.append(comment)
                    for comment in as_completed(comments):
                        try:
                            comments_data_list.append(comment.result())
                        except Exception as thread_e:
                            writer.writeLogToFile(f"行程{processNum}-> 運作時執行緒意外報錯: {thread_e}")
                            writer.writeLogToFile(f"行程{processNum}-> 詳細錯誤原因: {traceback.format_exc()}")
                writer.writeLogToFile(f"行程{processNum}-> {target_name} 結束後統計:{q_data.qsize()}")
                del q_data
                del q_signal
            print(f"**************************行程{processNum}-> 蒐集完成, {target_name} 共蒐集到{len(comments_data_list)}筆留言數資料**************************")
            parser.extendCommentData(comments_data_list, target_name)
            time.sleep(2)  # 給一個寫檔的時間
        else:
            print(f"行程{processNum}-> 沒有抓到文章留言區資訊的docid代號,故結束抓取")

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
            print(f"{'*' * 25}行程{processNum}-> 蒐集完成, {target_name} 共蒐集到{len(feedback_data_list)}筆分享數資料{'*' * 25}")
            parser.buildDataParse(feedback_data_list, target_name, pageID=page_id, screenshotDriver=screenshot_driver)
            time.sleep(2)  # 給一個寫檔的時間
        else:
            print(f"行程{processNum}-> 沒有抓到分享資料的docid代號,故結束抓取")

    posts_driver.clearDriver()
    return f"行程{processNum}-> 全部執行完成"


if __name__ == '__main__':
    Auxiliary.createIndexExcelAndRead()
    process_worker = configSetting.process_worker

    # params, cookie_xs, cookie_cUser = getFbCSRFToken.getCsrfToken()
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
            process_future = executor.submit(runFansPage, args_list[i], fb_dtsg, i)
            process_futures.append(process_future)
            time.sleep(i / 2)  # 避免短時間一次執行多條程序所作的緩衝
        for future in as_completed(process_futures):
            result_list.append(future.result())
    for result in result_list:  # 確認各行程有完成任務
        writer.writeLogToFile(result)
    print("腳本執行完成")
