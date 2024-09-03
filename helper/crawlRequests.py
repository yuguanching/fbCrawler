import requests
import re
import json
import time
import random
import os
import traceback
import configSetting

from queue import Queue
from numpy import append
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from fake_useragent import UserAgent
from helper import proxy, Auxiliary, helper
from ioService import writer, reader
from urllib3.exceptions import ConnectTimeoutError, MaxRetryError, ProtocolError
from requests.exceptions import ProxyError, ConnectTimeout, SSLError, ConnectionError, ChunkedEncodingError
from http.client import HTTPConnection
from module.facebook_module import facebookUser, facebookFriend


def __getHeaders__(pageurl) -> dict:
    '''
    Send a request to get cookieid as headers.
    '''
    fake_user_agent = UserAgent()

    # headers['cookie'] = '; '.join(['{}={}'.format(cookieid, resp.cookies.get_dict()[cookieid]) for cookieid in resp.cookies.get_dict()])
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
               'accept-language': 'en'}
    headers['ec-ch-ua-platform'] = 'Windows'
    headers['User-Agent'] = str(fake_user_agent.chrome)
    headers['sec-fetch-site'] = "same-origin"
    headers['origin'] = "https://www.facebook.com"
    headers['referer'] = pageurl
    # headers['cookie'] = ''
    pageurl = re.sub('www', 'm', pageurl)
    resp = requests.get(pageurl)
    headers['cookie'] = '; '.join(['{}={}'.format(cookieid, resp.cookies.get_dict()[
        cookieid]) for cookieid in resp.cookies.get_dict()])
    return headers


def crawlPagePosts(pageURL, pageID, docID, reqName, proxyIpList, processNum, targetName) -> list:

    try_count = 0  # 全任務使用各種IP重試的次數統計
    proxy_count = 0  # 單一輪proxy_ip_list的遍歷索引, 每次proxy ip 更新後都會歸零
    ult_noproxy_count = 0  # 每當出現一次exception就會累積一次,到達一定次數後就會允許使用一次本機公網ip發起呼叫,提高成功率
    record_time_cooldown = datetime.now()
    proxy_ip_list = proxyIpList
    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
    contents = []
    cursor = ''
    current_time = ''
    url = ''
    data = dict()
    page_info_obj = dict()
    headers = __getHeaders__(pageURL)

    session = requests.session()

    # 設定失敗重試策略
    retry_strategy = Retry(
        total=configSetting.retry,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    is_up_to_time = True
    while True:
        print(f"{'=' * 100}\n")
        print(
            f"行程{processNum}-> {targetName}:時間戳記: {current_time},文章網址: {url}, 當前的標記 : {cursor}")
        writer.writeLogToFile(
            f"行程{processNum}-> {targetName}:時間戳記: {current_time},文章網址: {url}, 當前的標記 : {cursor}")
        print(f"{'=' * 100}\n")
        data = {
            'variables': str(
                {
                    "count": 3,
                    "cursor": cursor,
                    "id": pageID,
                    "scale": 1,
                    "stream_count": 1,
                    "UFI2CommentsProvider_commentsKey": "ProfileCometTimelineRoute",
                    "feedLocation": "TIMELINE",
                    "privacySelectorRenderLocation": "COMET_STREAM",
                    "__relay_internal__pv__GroupsCometDelayCheckBlockedUsersrelayprovider": "false",
                    "__relay_internal__pv__IsWorkUserrelayprovider": "false",
                    "__relay_internal__pv__IsMergQAPollsrelayprovider": "false",
                    "__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider": "false",
                    "__relay_internal__pv__StoriesRingrelayprovider": "false"
                }
            ),
            'doc_id': docID,
            "__a": "1",
            "__comet_req": "15",
            "fb_api_req_friendly_name": reqName,
            "server_timestamps": "false"
        }
        try:
            # 區別在於有沒有使用proxy
            if current_time == "":
                current_time_date = datetime.now()
            else:
                current_time_date = datetime.strptime(
                    current_time, "%Y-%m-%d %H:%M:%S")
            if ((ult_noproxy_count >= configSetting.exception_max_try) and Auxiliary.checkTimeCooldown(record_time_cooldown)) or (current_time_date < configSetting.sp_time):
                print("觸發大招")
                resp = session.post(url='https://www.facebook.com/api/graphql/',
                                    data=data,
                                    headers=headers,
                                    timeout=configSetting.timeout,
                                    verify="./config/certs.pem"
                                    )
                # 使用完後,設定下新的時間,並重置發生錯誤的累積值
                ult_noproxy_count = 0
                record_time_cooldown = datetime.now()
            else:
                resp = session.post(url='https://www.facebook.com/api/graphql/',
                                    data=data,
                                    headers=headers,
                                    timeout=configSetting.timeout,
                                    proxies={'http': random_proxy_ip,
                                             "https": random_proxy_ip},
                                    verify="./config/certs.pem"
                                    )

            if reqName == 'ProfileCometTimelineFeedRefetchQuery':
                edge_list, cursor_now, is_up_to_time, arrive_first_catch_time, time_now, page_info_obj = helper.__parsingProfileComet__(
                    resp)
            elif reqName == 'CometModernPageFeedPaginationQuery':
                edge_list, cursor_now, is_up_to_time, arrive_first_catch_time, time_now = helper.__parsingCometModern__(
                    resp)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
                url = edge_list[len(edge_list)-1]['url']
            if reqName == 'ProfileCometTimelineFeedRefetchQuery':
                if not helper.hasNextPage_ProfileComet(page_info_obj):
                    raise UnboundLocalError(f"Reached the last page")
                else:
                    cursor = cursor_now
                    current_time = time_now
            elif reqName == 'CometModernPageFeedPaginationQuery':
                if not helper.hasNextPage_CometModern(resp):
                    raise UnboundLocalError(f"Reached the last page")
                else:
                    cursor = cursor_now
                    current_time = time_now
            # 超過設定的撈取日期
            if (is_up_to_time == False) and (arrive_first_catch_time == True):
                return contents

        except UnboundLocalError:
            print("Reached the last page")
            break

        except Exception as e:
            if (not isinstance(e, ProtocolError)) and (not isinstance(e, ChunkedEncodingError)) and (not isinstance(e, ConnectionError)) and (not isinstance(e, SSLError)) and (not isinstance(e, UnboundLocalError)) and (not isinstance(e, TimeoutError)) and (not isinstance(e, KeyError)) and (not isinstance(e, ConnectTimeoutError)) and (not isinstance(e, MaxRetryError)) and (not isinstance(e, ConnectionResetError)) and (not isinstance(e, ProxyError)) and (not isinstance(e, ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(
                    traceBack=f"pageid: {pageID}, docid: {docID}, cursor: {cursor}")

            ult_noproxy_count += 1
            proxy_count, try_count, proxy_ip_list = proxy.updateProxyAndStatus(
                proxy_count, try_count, proxy_ip_list, processNum)
            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
            if try_count >= configSetting.proxy_try_count:
                print(
                    f"行程{processNum}-> failed to catch posts after {try_count} times trying...")
                return contents
            else:
                continue
        finally:
            time.sleep(random.randint(1, 3))
    session.close()
    return contents


def crawlGroupPosts(pageURL, groupPageID, groupDocID, reqName, proxyIpList, processNum, targetName) -> list:

    try_count = 0  # 全任務使用各種IP重試的次數統計
    proxy_count = 0  # 單一輪proxy_ip_list的遍歷索引, 每次proxy ip 更新後都會歸零
    proxy_ip_list = proxyIpList
    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
    contents = []
    cursor = ''
    current_time = ''
    headers = __getHeaders__(pageURL)

    session = requests.session()

    # 設定失敗重試策略
    retry_strategy = Retry(
        total=configSetting.retry,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    is_up_to_time = True
    while True:
        print(
            f"行程{processNum}-> {targetName}:時間戳記: {current_time}, 當前的標記 : {cursor}")
        data = {'variables': str({"count": "3",
                                  "cursor": cursor,
                                  "id": groupPageID,
                                  "scale": "1",
                                  "stream_initial_count": "1",
                                  "useDefaultActor": "false",
                                  "renderLocation": "group",
                                  "feedLocation": "GROUP",
                                  "feedType": "DISCUSSION",
                                  "privacySelectorRenderLocation": "COMET_STREAM",
                                  "__relay_internal__pv__IsWorkUserrelayprovider": "false",
                                  "__relay_internal__pv__StoriesRingrelayprovider": "false"
                                  }),
                'doc_id': groupDocID,
                "__a": "1",
                "__comet_req": "15",
                "fb_api_req_friendly_name": reqName
                }
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                data=data,
                                headers=headers,
                                timeout=configSetting.timeout,
                                verify="./config/certs.pem",
                                proxies={'http': random_proxy_ip,
                                         "https": random_proxy_ip}
                                )

            if reqName == 'GroupsCometFeedRegularStoriesPaginationQuery':
                edge_list, cursor_now, is_up_to_time, arrive_first_catch_time, time_now = helper.__parsingGroupPosts__(
                    resp)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not helper.hasNextPageGroupPost(resp):
                raise UnboundLocalError(f"Reached the last page")
            else:
                cursor = cursor_now
                current_time = time_now
            # 超過設定的撈取日期
            if (is_up_to_time == False) and (arrive_first_catch_time == True):
                return contents

        except UnboundLocalError:
            print("Reached the last page")
            break

        except Exception as e:
            if (not isinstance(e, ProtocolError)) and (not isinstance(e, ChunkedEncodingError)) and (not isinstance(e, ConnectionError)) and (not isinstance(e, SSLError)) and (not isinstance(e, UnboundLocalError)) and (not isinstance(e, TimeoutError)) and (not isinstance(e, KeyError)) and (not isinstance(e, ConnectTimeoutError)) and (not isinstance(e, MaxRetryError)) and (not isinstance(e, ConnectionResetError)) and (not isinstance(e, ProxyError)) and (not isinstance(e, ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(
                    traceBack=f"grouppageid: {groupPageID}, docid: {groupDocID}, cursor: {cursor}")

            proxy_count, try_count, proxy_ip_list = proxy.updateProxyAndStatus(
                proxy_count, try_count, proxy_ip_list, processNum)
            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
            if try_count >= configSetting.proxy_try_count:
                print(
                    f"行程{processNum}-> failed to catch posts after {try_count} times trying...")
                return contents
            else:
                continue
        finally:
            time.sleep(random.randint(1, 2))
    session.close()
    return contents


def crawlFeedback(pageURL, article_id, postsCount, feedbackID, docID, reqName, fbDTSG, targetName, processNum, queue: Queue = None, queueSignal: Queue = None) -> list:

    try_count = 0  # 全任務使用各種IP重試的次數統計
    proxy_count = 0  # 單一輪proxy_ip_list的遍歷索引, 每次proxy ip 更新後都會歸零
    proxy_ip_list = json.loads(os.environ['proxy_list'])
    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
    contents = []
    cursor = ''
    headers = __getHeaders__(pageURL)
    session = requests.session()

    # 所有配合多執行緒的功能都要將keep-alive關閉,確保每次連線取完資料會關閉,避免連線數被吃滿導致無法開啟連線的錯誤
    headers['Connection'] = 'close'

    # 設定失敗重試策略
    retry_strategy = Retry(
        connect=5,
        total=configSetting.retry_feedback,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=100, max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    while True:
        # print(f"行程{process_num} {targetName}:當前的標記 : {cursor}")
        data = {'variables': str({
            "cursor": cursor,
            'id': feedbackID,
            "privacySelectorRenderLocation": "COMET_STREAM",
            "renderLocation": "reshares_dialog",
            "scale": "1",
            "feedLocation": "SHARE_OVERLAY",
            "__relay_internal__pv__FBReelsEnableDeferrelayprovider": "false",
            "__relay_internal__pv__GroupsCometDelayCheckBlockedUsersrelayprovider": "false",
            "__relay_internal__pv__IsWorkUserrelayprovider": "false",
            "__relay_internal__pv__IsMergQAPollsrelayprovider": "false",
            "__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider": "false"
        }),
            'doc_id': docID,
            "__a": "1",
            "__comet_req": "15",
            "fb_api_req_friendly_name": reqName
        }

        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                data=data,
                                headers=headers,
                                timeout=configSetting.timeout_feedback,
                                proxies={'http': random_proxy_ip, "https": random_proxy_ip},
                                verify="./config/certs.pem"
                                )
            edge_list, cursor_now = helper.__parsingFeedback__(resp, postsCount, feedbackID, article_id)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not helper.hasNextPageFeedback(resp):
                raise UnboundLocalError(f"Reached the last page")
            else:
                cursor = cursor_now

            try:
                resp.close()
            except AttributeError:
                pass

        except UnboundLocalError:
            print(f"文章編號{postsCount}的分享抓取 Reached the last page")
            break

        except Exception as e:
            if (not isinstance(e, ProtocolError)) and (not isinstance(e, ChunkedEncodingError)) and (not isinstance(e, ConnectionError)) and (not isinstance(e, SSLError)) and (not isinstance(e, UnboundLocalError)) and (not isinstance(e, TimeoutError)) and (not isinstance(e, KeyError)) and (not isinstance(e, ConnectTimeoutError)) and (not isinstance(e, MaxRetryError)) and (not isinstance(e, ConnectionResetError)) and (not isinstance(e, ProxyError)) and (not isinstance(e, ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"post_id:{postsCount}, feedback_id:{feedbackID}, docid:{docID}, cursor:{cursor}")

            # 沒有使用多執行緒的走這邊
            if queueSignal is None:
                proxy_count, try_count, proxy_ip_list = proxy.updateProxyAndStatus(proxy_count, try_count, proxy_ip_list, processNum)
            else:
                proxy_count, try_count, proxy_ip_list = proxy.updateMultiThreadProxyAndStatus(
                    proxy_count, try_count, proxy_ip_list, processNum, postsCount, len(contents), queueSignal)
            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
            if try_count >= configSetting.proxy_try_count:
                print(
                    f"行程{processNum}->分享者編號{postsCount} failed to catch posts after {try_count} times trying...")
                break
            else:
                continue
        finally:
            time.sleep(random.randint(1, 5))

    session.close()
    if queue is not None:
        queue.put(contents)
        fill = int(os.environ.get("feedback_id_list_len"))
        if queue.qsize() % configSetting.queue_show_interval == 0:
            print(f"行程{processNum}-> {targetName}:目前完成的任務數量為 {queue.qsize()}")
        if fill - queue.qsize() < 50:
            print(
                f"行程{processNum}-> {targetName}:還剩下 {fill - queue.qsize()} 個任務未完成")

    return contents


def crawlPostsComments(pageURL, postsCount, feedbackID, storyID, docID, reqName, fbDTSG, targetName, processNum, queue: Queue = None, queueSignal: Queue = None) -> list:

    try_count = 0  # 全任務使用各種IP重試的次數統計
    proxy_count = 0  # 單一輪proxy_ip_list的遍歷索引, 每次proxy ip 更新後都會歸零
    proxy_ip_list = json.loads(os.environ['proxy_list'])
    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
    contents = []
    headers = __getHeaders__(pageURL)

    # 所有配合多執行緒的功能都要將keep-alive關閉,確保每次連線取完資料會關閉,避免連線數被吃滿導致無法開啟連線的錯誤
    headers['Connection'] = 'close'

    session = requests.session()

    # 設定失敗重試策略
    retry_strategy = Retry(
        connect=5,
        total=configSetting.retry_feedback,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(pool_connections=20,
                          pool_maxsize=100, max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    while True:
        data = {'variables': str({
            'feedbackID': feedbackID,
            'storyID': storyID,
            "scale": "1",
            "feedbackSource": 110,
            "feedLocation": "DEDICATED_COMMENTING_SURFACE"
        }),
            'doc_id': docID,
            "__a": "1",
            "__comet_req": "15",
            "fb_api_req_friendly_name": reqName
        }

        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                data=data,
                                headers=headers,
                                timeout=configSetting.timeout_feedback,
                                proxies={'http': random_proxy_ip,
                                         "https": random_proxy_ip},
                                verify="./config/certs.pem"
                                )
            edge_list = helper.__parsingComments__(resp, postsCount)
            contents = contents + edge_list
            print(f"文章編號{postsCount}的留言抓取finished")
            break

        except Exception as e:
            if (not isinstance(e, ProtocolError)) and (not isinstance(e, ChunkedEncodingError)) and (not isinstance(e, ConnectionError)) and (not isinstance(e, SSLError)) and (not isinstance(e, UnboundLocalError)) and (not isinstance(e, TimeoutError)) and (not isinstance(e, KeyError)) and (not isinstance(e, ConnectTimeoutError)) and (not isinstance(e, MaxRetryError)) and (not isinstance(e, ConnectionResetError)) and (not isinstance(e, ProxyError)) and (not isinstance(e, ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(
                    traceBack=f"post_id:{postsCount}, feedback_id:{feedbackID}, story_id:{storyID}, docid:{docID}")

            # 沒有使用多執行緒的走這邊
            if queueSignal is None:
                proxy_count, try_count, proxy_ip_list = proxy.updateProxyAndStatus(
                    proxy_count, try_count, proxy_ip_list, processNum)
            else:
                proxy_count, try_count, proxy_ip_list = proxy.updateMultiThreadProxyAndStatus(
                    proxy_count, try_count, proxy_ip_list, processNum, postsCount, len(contents), queueSignal)
            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
            if try_count >= configSetting.proxy_try_count:
                print(
                    f"行程{processNum}-> failed to catch posts after {try_count} times trying...")
                return contents
            else:
                continue
        finally:
            time.sleep(random.randint(1, 2))
    session.close()
    if queue is not None:
        queue.put(contents)
        fill = int(os.environ.get("feedback_id_list_len"))
        if queue.qsize() % configSetting.queue_show_interval == 0:
            print(f"行程{processNum}-> {targetName}:目前完成的任務數量為 {queue.qsize()}")
        if fill - queue.qsize() < 50:
            print(
                f"行程{processNum}-> {targetName}:還剩下 {fill - queue.qsize()} 個任務未完成")

    return contents


def crawlSectionAbout(pageURL, usersCount, fbDTSG, docID, userID, reqName, targetName, processNum, friendDict, queue: Queue = None, queueSignal: Queue = None) -> list:

    try_count = 0  # 全任務使用各種IP重試的次數統計
    proxy_count = 0  # 單一輪proxy_ip_list的遍歷索引, 每次proxy ip 更新後都會歸零
    proxy_ip_list = json.loads(os.environ['proxy_list'])
    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
    contents = []
    collection_token_list = []
    edge_list = []
    headers = __getHeaders__(pageURL)

    # 所有配合多執行緒的功能都要將keep-alive關閉,確保每次連線取完資料會關閉,避免連線數被吃滿導致無法開啟連線的錯誤
    headers['Connection'] = 'close'

    session = requests.session()

    # 設定失敗重試策略
    retry_strategy = Retry(
        connect=5,
        total=configSetting.retry,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(pool_connections=20,
                          pool_maxsize=100, max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    while True:
        # print(f"開始抓取{targetName}的個人關於-總覽資料")
        # first call
        # collectionToken 不帶表示抓總覽
        data = {'variables': str({
            "pageID": userID,
            "userID": userID,
            "scale": "1",
            "__relay_internal__pv__FBReelsEnableDeferrelayprovider": "false",
            "__relay_internal__pv__FBReelsDisableBackgroundrelayprovider": "false",
            "__relay_internal__pv__FBReelsShowOverflowMenuInFeedbackBarrelayprovider": "false"
        }),
            'doc_id': docID,
            "__a": "1",
            "__comet_req": "15",
            "fb_dtsg": fbDTSG,
            "fb_api_req_friendly_name": reqName
        }
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                    data=data,
                                    headers=headers,
                                    timeout=configSetting.timeout,
                                    verify="./config/certs.pem",
                                    proxies={'http': random_proxy_ip, "https": random_proxy_ip})
            if reqName == 'ProfileCometAboutAppSectionQuery':
                edge_list = helper.__parsingSectionAbout__(resp, 0)
                break

        except Exception as e:
            if (not isinstance(e, ProtocolError)) and (not isinstance(e, ChunkedEncodingError)) and (not isinstance(e, ConnectionError)) and (not isinstance(e, SSLError)) and (not isinstance(e, UnboundLocalError)) and (not isinstance(e, TimeoutError)) and (not isinstance(e, KeyError)) and (not isinstance(e, ConnectTimeoutError)) and (not isinstance(e, MaxRetryError)) and (not isinstance(e, ConnectionResetError)) and (not isinstance(e, ProxyError)) and (not isinstance(e, ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(
                    traceBack=f"userid: {userID}, docid: {docID}, collectionToken: 0")

            # 沒有使用多執行緒的走這邊
            if queueSignal is None:
                proxy_count, try_count, proxy_ip_list = proxy.updateProxyAndStatus(
                    proxy_count, try_count, proxy_ip_list, processNum)
            else:
                proxy_count, try_count, proxy_ip_list = proxy.updateMultiThreadProxyAndStatus(
                    proxy_count, try_count, proxy_ip_list, processNum, usersCount, len(contents), queueSignal)
            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
            if try_count >= configSetting.proxy_try_count:
                print(
                    f"行程{processNum}-> failed to catch posts after {try_count} times trying...")
                return contents
            else:
                continue
        finally:
            time.sleep(random.randint(1, 2))
    contents = contents + edge_list
    collection_token_list = edge_list[0]['id_output']
    collect_id_count = 1

    while True:
        # print(f"{targetName} 的抓取進度: {collect_id_count}")
        # 關於裡面的資料不須全拿,多餘的直接略過
        if collect_id_count >= 5:
            break
        data = {'variables': str({
            "collectionToken": collection_token_list[collect_id_count],
            "pageID": userID,
            "userID": userID,
            "scale": "1",
            "__relay_internal__pv__FBReelsEnableDeferrelayprovider": "false",
            "__relay_internal__pv__FBReelsDisableBackgroundrelayprovider": "false",
            "__relay_internal__pv__FBReelsShowOverflowMenuInFeedbackBarrelayprovider": "false"
        }),
            'doc_id': docID,
            "__a": "1",
            "__comet_req": "15",
            "fb_dtsg": fbDTSG,
            "fb_api_req_friendly_name": reqName
        }
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                data=data,
                                headers=headers,
                                timeout=configSetting.timeout,
                                verify="./config/certs.pem",
                                proxies={'http': random_proxy_ip, "https": random_proxy_ip})
            if reqName == 'ProfileCometAboutAppSectionQuery':
                edge_list = helper.__parsingSectionAbout__(
                    resp, collect_id_count)

            if len(edge_list) != 0:
                contents = contents + edge_list
                collect_id_count += 1

        except Exception as e:
            if (not isinstance(e, ProtocolError)) and (not isinstance(e, ChunkedEncodingError)) and (not isinstance(e, ConnectionError)) and (not isinstance(e, SSLError)) and (not isinstance(e, UnboundLocalError)) and (not isinstance(e, TimeoutError)) and (not isinstance(e, KeyError)) and (not isinstance(e, ConnectTimeoutError)) and (not isinstance(e, MaxRetryError)) and (not isinstance(e, ConnectionResetError)) and (not isinstance(e, ProxyError)) and (not isinstance(e, ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(
                    traceBack=f"userid: {userID}, docid: {docID}, collectionToken: {collection_token_list[collect_id_count]}")

            # 沒有使用多執行緒的走這邊
            if queueSignal is None:
                proxy_count, try_count, proxy_ip_list = proxy.updateProxyAndStatus(
                    proxy_count, try_count, proxy_ip_list, processNum)
            else:
                proxy_count, try_count, proxy_ip_list = proxy.updateMultiThreadProxyAndStatus(
                    proxy_count, try_count, proxy_ip_list, processNum, usersCount, len(contents), queueSignal)
            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
            if try_count >= configSetting.proxy_try_count:
                print(
                    f"行程{processNum}-> failed to catch posts after {try_count} times trying...")
                return contents
            else:
                continue
        finally:
            time.sleep(random.randint(1, 2))
    session.close()
    # 抓朋友群資料時將該朋友的dict補進去
    if friendDict is not None:
        contents.append(friendDict)
    if queue is not None:
        queue.put(contents)
        if queue.qsize() % configSetting.queue_show_interval == 0:
            print(f"行程{processNum}-> {targetName}:目前完成的任務數量為 {queue.qsize()}")

    return contents


def crawlFriendzone(pageURL, friendzoneID, docID, reqName, proxyIpList, processNum, targetName) -> list:

    try_count = 0  # 全任務使用各種IP重試的次數統計
    proxy_count = 0  # 單一輪proxy_ip_list的遍歷索引, 每次proxy ip 更新後都會歸零
    proxy_ip_list = proxyIpList
    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
    contents = []
    cursor = ''

    headers = __getHeaders__(pageURL)
    # headers['cookie'] += cookieStr

    session = requests.session()

    # 設定失敗重試策略
    retry_strategy = Retry(
        total=configSetting.retry,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    while True:
       # print(f"行程{process_num} {targetName}:當前的標記 : {cursor}")
        data = {
            'variables': str(
                {
                    "cursor": cursor,
                    "id": friendzoneID,
                    "scale": 1
                }
            ),
            'doc_id': docID
        }
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                data=data,
                                headers=headers,
                                timeout=configSetting.timeout,
                                verify="./config/certs.pem",
                                proxies={'http': random_proxy_ip, "https": random_proxy_ip})
            if reqName == 'ProfileCometAppCollectionListRendererPaginationQuery':
                edge_list, cursor_now = helper.__parsingFriendzoneNov__(resp)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not helper.hasNextPageFriendzone(resp):
                raise UnboundLocalError("Reached the last page")
            else:
                cursor = cursor_now

        except UnboundLocalError:
            print("Reached the last page")
            break

        except Exception as e:
            if (not isinstance(e, ProtocolError)) and (not isinstance(e, ChunkedEncodingError)) and (not isinstance(e, ConnectionError)) and (not isinstance(e, SSLError)) and (not isinstance(e, UnboundLocalError)) and (not isinstance(e, TimeoutError)) and (not isinstance(e, KeyError)) and (not isinstance(e, ConnectTimeoutError)) and (not isinstance(e, MaxRetryError)) and (not isinstance(e, ConnectionResetError)) and (not isinstance(e, ProxyError)) and (not isinstance(e, ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"friendzone_id: {friendzoneID}, docid: {docID}, cursor: {cursor}")

            proxy_count, try_count, proxy_ip_list = proxy.updateProxyAndStatus(
                proxy_count, try_count, proxy_ip_list, processNum)
            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
            if try_count >= configSetting.proxy_try_count:
                print(
                    f"行程{processNum}-> failed to catch posts after {try_count} times trying...")
                return contents
            else:
                continue
        finally:
            time.sleep(random.randint(1, 2))
    session.close()
    return contents


def crawlGroupMember(pageURL, fbDTSG, cookieStr, groupID, docID, reqName, proxyIpList, processNum, targetName) -> list:

    try_count = 0  # 全任務使用各種IP重試的次數統計
    proxy_count = 0  # 單一輪proxy_ip_list的遍歷索引, 每次proxy ip 更新後都會歸零
    proxy_ip_list = proxyIpList
    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
    contents = []
    cursor = ''

    headers = __getHeaders__(pageURL)
    headers['cookie'] += cookieStr

    session = requests.session()

    # 設定失敗重試策略
    retry_strategy = Retry(
        total=configSetting.retry,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    while True:
        print(f"行程{processNum} {targetName}:當前的標記 : {cursor}")
        data = {
            'variables': str({
                'count': 10,
                'cursor': cursor,
                'id': groupID,
                'groupID': groupID,
                'scale': 1, }),

            'doc_id': docID,
            '__a': 1,
            '__comet_req': 15,
            'fb_dtsg': fbDTSG,
            'fb_api_req_friendly_name': reqName
        }

        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                data=data,
                                headers=headers,
                                timeout=configSetting.timeout,
                                verify="./config/certs.pem",
                                proxies={'http': random_proxy_ip, "https": random_proxy_ip})
            if reqName == 'GroupsCometMembersPageNewMembersSectionRefetchQuery':
                edge_list, cursor_now = helper.__parsingGroupMember__(resp)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not helper.hasNextPageGroupMember(resp):
                raise UnboundLocalError("Reached the last page")
            else:
                cursor = cursor_now

        except UnboundLocalError:
            print("Reached the last page")
            break

        except Exception as e:
            if (not isinstance(e, ProtocolError)) and (not isinstance(e, ChunkedEncodingError)) and (not isinstance(e, ConnectionError)) and (not isinstance(e, SSLError)) and (not isinstance(e, UnboundLocalError)) and (not isinstance(e, TimeoutError)) and (not isinstance(e, KeyError)) and (not isinstance(e, ConnectTimeoutError)) and (not isinstance(e, MaxRetryError)) and (not isinstance(e, ConnectionResetError)) and (not isinstance(e, ProxyError)) and (not isinstance(e, ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(
                    traceBack=f"group_id: {groupID}, docid: {docID}, cursor: {cursor}")

            proxy_count, try_count, proxy_ip_list = proxy.updateProxyAndStatus(
                proxy_count, try_count, proxy_ip_list, processNum)
            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
            if try_count >= configSetting.proxy_try_count:
                print(
                    f"行程{processNum}-> failed to catch posts after {try_count} times trying...")
                return contents
            else:
                continue
        finally:
            time.sleep(random.randint(1, 2))
    session.close()
    return contents


def crawlFriendzone_new(facebookUser: facebookUser, fb_dtsg: dict, processNum: int, queue: Queue = None, queueSignal: Queue = None) -> list:
    try_count = 0  # 全任務使用各種IP重試的次數統計
    proxy_count = 0  # 單一輪proxy_ip_list的遍歷索引, 每次proxy ip 更新後都會歸零
    proxy_ip_list = json.loads(os.environ['proxy_list'])
    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
    contents = []
    cursor = ''
    headers = __getHeaders__(facebookUser.profile_url)
    headers["cookie"] = f"{headers['cookie']};c_user={fb_dtsg['c_user']};xs={fb_dtsg['xs']};"

    session = requests.session()
    # 設定失敗重試策略
    retry_strategy = Retry(
        total=configSetting.retry,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    while True:
       # print(f"行程{process_num} {targetName}:當前的標記 : {cursor}")
        data = {
            'variables': str(
                {
                    "cursor": cursor,
                    "id": facebookUser.friendzone_id,
                    "scale": 1,
                    "count": 8
                }
            ),
            'doc_id': facebookUser.friendzone_docid,
            'fb_dtsg': fb_dtsg["fb_dtsg"]
        }
        print(f"input data:{data}")
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                data=data,
                                headers=headers,
                                timeout=configSetting.timeout,
                                verify="./config/certs.pem",
                                proxies={'http': random_proxy_ip, "https": random_proxy_ip})
            print(resp.text)
            if facebookUser.friendzone_reqname == 'ProfileCometAppCollectionListRendererPaginationQuery':
                edge_list, cursor_now = helper.__parsingFriendzoneNov__(resp)
                print(f"cursor:{cursor_now}")

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                print("A")
                contents = contents + edge_list
            if not helper.hasNextPageFriendzone(resp):
                print("rgrgrgrrgg")
                raise UnboundLocalError("Reached the last page")
            else:
                cursor = cursor_now

        except UnboundLocalError:
            print(f"{facebookUser.username}: Reached the last page")
            break

        except Exception as e:
            if (not isinstance(e, ProtocolError)) and (not isinstance(e, ChunkedEncodingError)) and (not isinstance(e, ConnectionError)) and (not isinstance(e, SSLError)) and (not isinstance(e, UnboundLocalError)) and (not isinstance(e, TimeoutError)) and (not isinstance(e, KeyError)) and (not isinstance(e, ConnectTimeoutError)) and (not isinstance(e, MaxRetryError)) and (not isinstance(e, ConnectionResetError)) and (not isinstance(e, ProxyError)) and (not isinstance(e, ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"username:{facebookUser.username}, docid:{facebookUser.friendzone_docid}, cursor:{cursor}")

            # 沒有使用多執行緒的走這邊
            if queueSignal is None:
                proxy_count, try_count, proxy_ip_list = proxy.updateProxyAndStatus(proxy_count, try_count, proxy_ip_list, processNum)
            else:
                proxy_count, try_count, proxy_ip_list = proxy.updateMultiThreadProxyAndStatus(
                    proxy_count, try_count, proxy_ip_list, processNum, facebookUser.username, len(contents), queueSignal)
            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
            if try_count >= configSetting.proxy_try_count:
                print(
                    f"行程{processNum}->分享者編號{facebookUser.username} failed to catch posts after {try_count} times trying...")
                break
            else:
                continue
        finally:
            time.sleep(random.randint(1, 5))

    session.close()
    if queue is not None:
        queue.put(contents)
        fill = int(os.environ.get("friend_id_list_len"))
        if queue.qsize() % configSetting.queue_show_interval == 0:
            print(f"行程{processNum}-> {facebookUser.username}:目前完成的任務數量為 {queue.qsize()}")
        if fill - queue.qsize() < 50:
            print(
                f"行程{processNum}-> {facebookUser.username}:還剩下 {fill - queue.qsize()} 個任務未完成")

    for content in contents:
        print(content)
        friend_instance = facebookFriend(username=content["username"], profile_url=content["profile_url"],
                                         user_id=content["user_id"], photo_url=content["photo_url"])
        facebookUser.friend_data_list.append(friend_instance)
    return
