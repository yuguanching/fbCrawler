import json
import os
import time
import traceback
import configSetting

from helper import Auxiliary, proxy, idFetcher, crawlRequests, thread
from ioService import parser, writer, reader
from webManager import webDriver, getFbCSRFToken
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


def runUserInfo(jsonArrayDataSub, fbDTSG, aboutDocID, friendzoneDocID, processNum) -> None:
    """
    jsonArrayDataSub: 已經透過多行程分配過的輸入資料
    """

    target_urls = jsonArrayDataSub["targetURL"]
    target_names = jsonArrayDataSub["targetName"]

    posts_driver = webDriver.postsDriver(driver=None, options=None, isLogin=False)
    posts_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)
    posts_driver.driverInitialize()

    friendzone_driver = webDriver.friendzoneDriver(driver=posts_driver.driver, options=None, isLogin=True)
    friendzone_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)

    screenshot_driver = webDriver.screenshotDriver(driver=posts_driver.driver, options=None, isLogin=True)
    screenshot_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)

    for target_url, target_name in zip(target_urls, target_names):

        # 每個粉專資料有自己的子資料夾存放
        Auxiliary.checkDirAndCreate(target_name)
        proxy_ip_list = proxy.gRequestsProxyList(processNum)
        ip_list_str = json.dumps(proxy_ip_list)
        os.environ['proxy_list'] = ip_list_str
        # # 測速的開始時間戳記
        print(f"開始抓取 {target_name} 的文章資料")

        page_id, page_docid, page_req_name, page_is_been_banned = idFetcher.fetchEigenvaluesAndID(
            func=idFetcher.__getPageID__, customDriver=posts_driver, errString="未能取得文章的docid 或 pageid,嘗試換其他帳號試試", pageURL=target_url, checkOption=2)
        if page_is_been_banned:
            writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
            continue

        feedback_id_list = []
        story_id_list = []
        futures = []
        friendzone_data_list = []

        post_list = crawlRequests.crawlPagePosts(pageURL=target_url, pageID=page_id, reqName=page_req_name, docID=page_docid,
                                                 proxyIpList=proxy_ip_list, processNum=processNum, targetName=target_name)
        feedback_id_list, story_id_list = parser.buildCollectData(post_list, target_name, screenshotDriver=screenshot_driver)
        print(f"{target_name} 文章的feedback_id數量: {len(feedback_id_list)}")

        # ----------------------------------------------------------
        # 若是可以從profile個人頁連結取到userid,就省略爬蟲的動作
        # user_id = Auxiliary.parseFBUserID(targetURL)
        # if user_id == "":
        #     user_id, about_docid_temp, about_req_name, about_isBeenBanned = idFetcher.fetchEigenvaluesAndID(func=idFetcher.__getUserIDSection__, customDriver=postsDriver, errString="未能取得個人關於資訊的docid或userid,嘗試換其他帳號試試",pageURL=targetURL, checkOption=1)
        #     if about_isBeenBanned :
        #         writer.writeLogToFile(f"目標{targetName}已被臉書封鎖,留下紀錄待處理")
        #         continue
        # else:
        #     pass
        # ----------------------------------------------------------

        user_id, _, about_req_name, about_is_been_banned = idFetcher.fetchEigenvaluesAndID(
            func=idFetcher.__getUserIDSection__, customDriver=posts_driver, errString="未能取得個人關於資訊的docid或userid,嘗試換其他帳號試試", pageURL=target_url, checkOption=1)
        if about_is_been_banned:
            writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
            continue

        print(f"開始抓取{target_name}的個人關於資料")
        about_content_list = crawlRequests.crawlSectionAbout(pageURL=target_url, usersCount=0, fbDTSG=fbDTSG, docID=aboutDocID,
                                                             userID=user_id, reqName=about_req_name, targetName=target_name, processNum=processNum, friendDict=None)
        parser.buildAboutData(about_content_list, target_name, target_url)

        friendzone_id, _, friendzone_req_name, friendzone_is_been_banned = idFetcher.fetchEigenvaluesAndID(
            func=idFetcher.__getFriendzoneNovSection__, customDriver=friendzone_driver, errString="未能取得朋友欄目的docid 或 friendzone_id,嘗試換其他帳號試試", pageURL=target_url, checkOption=0)
        if friendzone_is_been_banned:
            writer.writeLogToFile(f"目標{target_name}已被臉書封鎖,留下紀錄待處理")
            continue

        friendzone_list = crawlRequests.crawlFriendzone(pageURL=target_url, friendzoneID=friendzone_id, docID=friendzoneDocID,
                                                        reqName=friendzone_req_name, proxyIpList=proxy_ip_list, processNum=processNum, targetName=target_name)
        writer.writeLogToFile(f"行程{processNum}-> {target_name} 初步統計有 {len(friendzone_list)} 個朋友")
        if aboutDocID != "":
            if len(friendzone_list) != 0:
                q_data = Queue()  # 幫助內部計數用
                q_signal = Queue()  # 信號傳遞交換區
                thread_workers = thread.generateThreadWorkers(len(feedback_id_list))
                with ThreadPoolExecutor(max_workers=thread_workers) as executor:
                    print(f"行程{processNum}-> 啟動 {target_name} 的朋友群抓取線程共 {thread_workers} 條")
                    for friend_count, friend in enumerate(friendzone_list):
                        future = executor.submit(crawlRequests.crawlSectionAbout, friend["url"], friend_count, fbDTSG, aboutDocID,
                                                 friend["userID"], about_req_name, target_name, processNum, friend, q_data, q_signal)
                        futures.append(future)
                    for future in as_completed(futures):
                        try:
                            friendzone_data_list.append(future.result())
                        except Exception as thread_e:
                            writer.writeLogToFile(f"行程{processNum}-> 運作時執行緒意外報錯: {thread_e}")
                            writer.writeLogToFile(f"行程{processNum}-> 詳細錯誤原因: {traceback.format_exc()}")
                writer.writeLogToFile(f"行程{processNum}-> {target_name} 結束後統計:{q_data.qsize()}")
                del q_data
                del q_signal
            print(
                f"************************** <行程{processNum}-> 蒐集完成, {target_name} 共蒐集到{len(friendzone_data_list)}筆朋友關於資料> **************************")
            parser.buildFriendzoneData(friendzone_data_list, target_name, target_url)
            time.sleep(2)  # 給一個寫檔的時間
        else:
            print(f"行程{processNum}-> 沒有抓到個人關於資訊的docid代號,故結束抓取")

    posts_driver.clearDriver()
    return f"行程{processNum}-> 全部執行完成"


if __name__ == '__main__':
    Auxiliary.createIndexExcelAndRead()
    process_worker = configSetting.process_worker

    # 先抓取csrf token標記,後續抓取關於資料要用
    params, cookie_xs, cookie_cUser = getFbCSRFToken.getCsrfToken()
    cookie_str = f" ;{cookie_xs['name']}={cookie_xs['value']}; {cookie_cUser['name']}={cookie_cUser['value']};"
    fb_dtsg = params['fb_dtsg']

    target_urls_split = Auxiliary.split(configSetting.json_array_data['targetURL'], process_worker)
    target_names_split = Auxiliary.split(configSetting.json_array_data['targetName'], process_worker)
    args_list = []
    result_list = []
    process_futures = []

    # customDriver 初始化
    posts_driver = webDriver.postsDriver(driver=None, options=None, isLogin=False)
    posts_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)
    posts_driver.driverInitialize()

    friendzone_driver = webDriver.friendzoneDriver(driver=posts_driver.driver, options=None, isLogin=True)
    friendzone_driver.setOptions(needHeadless=configSetting.need_headless, needImage=False)

    # 只為了取docid 特徵值,為避免搜索清單的項目有a.被FB封鎖的 b.沒有任何朋友的 ,故自行於配置檔設定任意一個活著且含朋友群的pofile連結
    # 先取一次profile的docid特徵值(用意是為了有效減少取特徵值的頻率),此次抓取的userid不會使用,故不檢查
    # 先取一次朋友群的docid特徵值(用意是為了有效減少取特徵值的頻率),此次抓取的friendzone_id不會使用,故不檢查
    get_docid_profile_url = configSetting.json_array_data['personProfileDocidTestURL']
    user_id, about_docid, _, _ = idFetcher.fetchEigenvaluesAndID(
        func=idFetcher.__getUserIDSection__, customDriver=posts_driver, errString="未能取得個人關於資訊的docid,嘗試換其他帳號試試", pageURL=get_docid_profile_url, checkOption=1)
    friendzone_id, friendzone_docid, friendzone_req_name, _ = idFetcher.fetchEigenvaluesAndID(
        func=idFetcher.__getFriendzoneNovSection__, customDriver=friendzone_driver, errString="未能取得朋友欄目的docid,嘗試換其他帳號試試", pageURL=get_docid_profile_url, checkOption=1)

    os.environ.pop("account_number_now")
    posts_driver.clearDriver()

    for i in range(process_worker):
        json_array_data_copy_temp = configSetting.json_array_data.copy()
        json_array_data_copy_temp['targetURL'] = target_urls_split[i]
        json_array_data_copy_temp['targetName'] = target_names_split[i]
        args_list.append(json_array_data_copy_temp)

    with ProcessPoolExecutor(max_workers=process_worker) as executor:
        print(f"已配置{process_worker}個處理行程等待執行")
        for i in range(len(args_list)):
            print(f"任務 {i} 植入任務列表")
            writer.writeLogToFile("process " + str(i) + " : " + json.dumps(args_list[i]['targetName'], ensure_ascii=False))
            process_future = executor.submit(runUserInfo, args_list[i], fb_dtsg, about_docid, friendzone_docid, i)
            process_futures.append(process_future)
            time.sleep(i / 2)  # 避免短時間一次執行多條程序所作的緩衝
        for future in as_completed(process_futures):
            result_list.append(future.result())
    for result in result_list:
        writer.writeLogToFile(result)
    print("腳本執行完成")
