import os
import json
import time
import traceback
import configSetting

from queue import Queue
from threading import Thread
from datetime import datetime
from ioService import parser, writer, reader
from webManager import webDriver
from helper import Auxiliary, proxy, idFetcher, crawlRequests, thread
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


def runFansPage(jsonArrayDataSub, fbDTSG, feedback_docid, processNum) -> str:
    """
    jsonArrayDataSub: 已經透過多行程分配過的輸入資料
    """
    target_urls = jsonArrayDataSub["targetURL"]
    target_names = jsonArrayDataSub["targetName"]

    posts_driver = webDriver.postsDriver(driver=None, options=None, isLogin=False)
    posts_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)
    posts_driver.driverInitialize()
    posts_driver.isLogin = True

    screenshot_driver = webDriver.screenshotDriver(driver=None, options=None, isLogin=True)
    screenshot_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)
    screenshot_driver.driverInitialize()

    for target_url, target_name in zip(target_urls, target_names):

        # 每個粉專資料有自己的子資料夾存放
        Auxiliary.checkDirAndCreate(target_name)

        feedback_id_list = []
        story_id_list = []
        article_id_list = []
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
        # page_id, page_docid, page_req_name = "100067712156019", "8699154896879027", "ProfileCometTimelineFeedRefetchQuery"
        # 蒐集粉專基本資料，並將基本資料寫入DB，含截圖
        profile_photo_url, found_date, transparency_img_path, homepage_img_path = screenshot_driver.fetch_fanspage_basic_data(
            url=target_url, subDir=target_name)
        db_input_data = list()
        db_input_data.append((str(page_id), target_name, found_date, 2, target_url, profile_photo_url))
        configSetting.db_adapter.insert_user_info(db_input_data)

        with open(transparency_img_path, "rb") as f:
            image = f.read()
        configSetting.db_adapter.update_user_image(user_id=page_id, image_field="transparency_image", image=image)

        with open(homepage_img_path, "rb") as f:
            image = f.read()
        configSetting.db_adapter.update_user_image(user_id=page_id, image_field="homepage_image", image=image)
        print(f"已插入粉專資料: {db_input_data}")

        if configSetting.post_operate_by_loading_db:
            id_data_from_db = configSetting.db_adapter.get_article_id_info(user_id=page_id)
            # theDate = configSetting.json_array_data["searchStartDate"]
            # id_data_from_db = configSetting.db_adapter.get_article_id_info_by_date(user_id=page_id, deadline=theDate)
            for data in id_data_from_db:
                article_id_list.append(data[0])
                story_id_list.append(data[1])
                feedback_id_list.append(data[2])
        else:
            post_list = crawlRequests.crawlPagePosts(pageURL=target_url, pageID=page_id, docID=page_docid,
                                                     reqName=page_req_name, processNum=processNum, targetName=target_name)
            feedback_id_list, story_id_list, article_id_list = parser.buildCollectData(
                post_list, target_name, page_id, screenshotDriver=screenshot_driver)

        writer.writeLogToFile(f"行程{processNum}-> {target_name} 初步統計有 {len(feedback_id_list)} 篇文章要抓留言、分享資料")
        os.environ['feedback_id_list_len'] = str(len(feedback_id_list))

        # if is_been_banned:
        #     writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
        #     continue

        # if comment_docid != "":
        #     if len(feedback_id_list) == len(story_id_list):
        #         q_data = Queue()  # 幫助內部計數用
        #         q_signal = Queue()  # 信號傳遞交換區
        #         thread_workers = thread.generateThreadWorkers(
        #             len(feedback_id_list))
        #         with ThreadPoolExecutor(max_workers=thread_workers) as executor:
        #             print(
        #                 f"行程{processNum}-> 啟動 {target_name} 的留言數抓取線程共{thread_workers}條")
        #             for posts_count, (feedback_id, story_id) in enumerate(zip(feedback_id_list, story_id_list)):
        #                 comment = executor.submit(crawlRequests.crawlPostsComments, target_url, posts_count, feedback_id, story_id,
        #                                           comment_docid, comment_req_name, fbDTSG, target_name, processNum, q_data, q_signal)
        #                 comments.append(comment)
        #             for comment in as_completed(comments):
        #                 try:
        #                     comments_data_list.append(comment.result())
        #                 except Exception as thread_e:
        #                     writer.writeLogToFile(
        #                         f"行程{processNum}-> 運作時執行緒意外報錯: {thread_e}")
        #                     writer.writeLogToFile(
        #                         f"行程{processNum}-> 詳細錯誤原因: {traceback.format_exc()}")
        #         writer.writeLogToFile(
        #             f"行程{processNum}-> {target_name} 結束後統計:{q_data.qsize()}")
        #         del q_data
        #         del q_signal
        #     print(
        #         f"**************************行程{processNum}-> 蒐集完成, {target_name} 共蒐集到{len(comments_data_list)}筆留言數資料**************************")
        #     parser.extendCommentData(comments_data_list, target_name)
        #     time.sleep(2)  # 給一個寫檔的時間
        # else:
        #     print(f"行程{processNum}-> 沒有抓到文章留言區資訊的docid代號,故結束抓取")
        if configSetting.share_operate_by_loading_db is False:
            # 外部先取得feedback的docid,避免多線程重複抓取
            # feedback_docid = "9069466813142103"
            req_name = "CometResharesFeedPaginationQuery"

            if feedback_docid != "":
                if len(feedback_id_list) != 0:
                    q_data = Queue()  # 幫助內部計數用
                    q_signal = Queue()  # 信號傳遞交換區
                    thread_workers = thread.generateThreadWorkers(len(feedback_id_list))
                    with ThreadPoolExecutor(max_workers=thread_workers) as executor:
                        print(f"行程{processNum}-> 啟動 {target_name} 的分享數抓取線程共{thread_workers}條")
                        for posts_count, (feedback_id, article_id) in enumerate(zip(feedback_id_list, article_id_list)):
                            reshare = executor.submit(crawlRequests.crawlFeedback, target_url, article_id, posts_count, feedback_id,
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
            else:
                print(f"行程{processNum}-> 沒有抓到分享資料的docid代號,故結束抓取")
                return f"行程{processNum}-> 全部執行完成"
        parser.buildDataParse(feedback_data_list, target_name, pageID=page_id, screenshotDriver=screenshot_driver)
        time.sleep(2)  # 給一個寫檔的時間

    posts_driver.clearDriver()
    screenshot_driver.clearDriver()
    return f"行程{processNum}-> 全部執行完成"


if __name__ == '__main__':
    Auxiliary.createIndexExcelAndRead()
    process_worker = configSetting.process_worker
    # process_worker = 1

    proxy_ip_list = proxy.gRequestsProxyList(None)
    ip_list_str = json.dumps(proxy_ip_list)
    os.environ['proxy_list'] = ip_list_str

    feedback_driver = webDriver.feedbackDriver(driver=None, options=None, isLogin=True)
    feedback_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)
    feedback_driver.driverInitialize()
    feedback_driver.isLogin = True

    fb_dtsg = ""
    feedback_docid_fetch_refer = configSetting.feedback_docID_fetch_refer_url
    _, feedback_docid, _, comment_docid, comment_req_name, is_been_banned = idFetcher.fetchEigenvaluesAndID(
        func=idFetcher.__getDocIDFeedback__, customDriver=feedback_driver, errString="未能取得分享的docid,嘗試換其他帳號試試", pageURL=feedback_docid_fetch_refer, checkOption=1)

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
            writer.writeLogToFile("process " + str(i) + " : " +
                                  json.dumps(args_list[i]['targetName'], ensure_ascii=False))
            process_future = executor.submit(runFansPage, args_list[i], fb_dtsg, feedback_docid, i)
            process_futures.append(process_future)
            time.sleep(i / 2)  # 避免短時間一次執行多條程序所作的緩衝
        for future in as_completed(process_futures):
            result_list.append(future.result())
    for result in result_list:  # 確認各行程有完成任務
        writer.writeLogToFile(result)
    print("腳本執行完成")
