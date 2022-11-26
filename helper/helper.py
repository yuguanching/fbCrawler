from inspect import Traceback
from tempfile import tempdir
from queue import Queue
import grequests
import requests
import re
import json
import time
import random 
import os 
import traceback

from typing import Union
from queue import Queue
from numpy import append
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from fake_useragent import UserAgent
from helper import proxy,Auxiliary,rawDataResolve
from webManager import webDriver
from ioService import writer,reader
from urllib3.exceptions import ConnectTimeoutError,MaxRetryError,ProtocolError
from requests.exceptions import ProxyError,ConnectTimeout,SSLError,ConnectionError,ChunkedEncodingError
from http.client import HTTPConnection


def __getHeaders__(pageurl) -> dict:
    '''
    Send a request to get cookieid as headers.
    '''
    fake_user_agent = UserAgent()
    # pageurl = re.sub('www', 'm', pageurl)
    # resp = requests.get(pageurl)
    # headers['cookie'] = '; '.join(['{}={}'.format(cookieid, resp.cookies.get_dict()[cookieid]) for cookieid in resp.cookies.get_dict()])
    # resp.close()
    headers={'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
             'accept-language': 'en'}
    headers['ec-ch-ua-platform'] = 'Windows'
    headers['user-agent'] = fake_user_agent.chrome
    headers['sec-fetch-site'] = "same-origin"
    # headers['Connection'] = 'close'
    # headers['cookie'] = headers['cookie'] + '; locale=en_US'
    return headers


def __getFriendzoneNovSection__(pageURL, customDriver :webDriver.friendzoneDriver) -> tuple[str, str, str, bool]:
    
    print("以selenium的爬蟲登入法取得userid、docid")
    is_been_banned = False
    # userid = ''
    resp = customDriver._getSource(pageURL=pageURL)
    if resp == "":
        return "", "", "", is_been_banned

    if ("目前無法查看此內容" in resp) and ("empty_states_icons" in resp):
        is_been_banned = True
        return "", "", "", is_been_banned
        
    # writer.writeTempFile(filename="sourceCode_friendzone",content=resp) 

    # # userID
    # if len(re.findall('"userID":"([0-9]{1,})",', resp)) >= 1:
    #     userid = re.findall('"userID":"([0-9]{1,})",', resp)[0]
    # else:
    #     userid = ''

    if len(re.findall('"tab_key":"friends_all","id":"(.*?)"',resp)) >=1 :
        friendzone_id = re.findall('"tab_key":"friends_all","id":"(.*?)"',resp)[0]
    else :
        friendzone_id = ''
    
    # section docid
    soup = BeautifulSoup(resp, 'lxml')
    docid = ""
    req_name = ""
    for js in soup.findAll('script'):
        if js.get('src') is None or ("x-javascript" not in js.get('src')):
            continue
        else:
            # resp_href = requests.get(js.get('src'))
            resp_href = customDriver.catchSpecialJsSource(pageURL=js.get('src'))
            for line in resp_href.split('\n', -1):
                if 'ProfileCometAppCollectionListRendererPaginationQuery_' in line:
                    docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                    req_name = 'ProfileCometAppCollectionListRendererPaginationQuery'
                    break
    # print('userid is: {}'.format(userid))
    print('friendzoneid is {}'.format(friendzone_id))
    print('docid is: {}'.format(docid))
    print(f"req_name is: {req_name}")
    return friendzone_id, docid, req_name, is_been_banned


def __getUserIDSection__(pageURL, customDriver :webDriver.postsDriver):
    
    print("以selenium的爬蟲登入法取得userid、docid")
    is_been_banned = False
    userid = ''
    resp = customDriver._getSource(pageURL=pageURL)
    if ("目前無法查看此內容" in resp) and ("empty_states_icons" in resp):
        is_been_banned = True
        return "", "", "", is_been_banned
    # userID
    if len(re.findall('"userID":"([0-9]{1,})",', resp)) >= 1:
        userid = re.findall('"userID":"([0-9]{1,})",', resp)[0]
    else:
        userid = ''
    
     # section docid
    soup = BeautifulSoup(resp, 'lxml')
    docid = ""
    req_name = ""
    for js in soup.findAll('link', {'rel': 'preload'}):
        resp_href = requests.get(js['href'])
        for line in resp_href.text.split('\n', -1):
            if 'ProfileCometAboutAppSectionQuery_' in line:
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'ProfileCometAboutAppSectionQuery'
                break

    print('userid is: {}'.format(userid))
    print('docid is: {}'.format(docid))
    print(f"req_name is: {req_name}")
    resp_href.close()
    return userid, docid, req_name, is_been_banned


def __getDocIDFeedback__(pageURL, customDriver :webDriver.feedbackDriver) -> tuple[str, str, str, bool]:

    # *部分粉專有鎖年齡與國家,導致只能登入後才能瀏覽,故改用爬蟲登入法取得頁面資料
    print("以selenium的爬蟲登入法取得feedback 的 docid")
    is_been_banned = False
    resp = customDriver._getSource(pageURL=pageURL)

    if ("目前無法查看此內容" in resp) and ("empty_states_icons" in resp):
        is_been_banned = True
        return "", "", "", is_been_banned
    # feedbackid
    soup = BeautifulSoup(resp, 'lxml')
    docid = ""
    req_name = ""
    for js in soup.findAll('link', {'rel': 'preload'}):
        resp = requests.get(js['href'])
        for line in resp.text.split('\n', -1):
            if 'CometResharesFeedPaginationQuery_' in line:
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'CometResharesFeedPaginationQuery'
                break
            if 'ProfileCometTimelineFeedRefetchQuery_' in line:
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'ProfileCometTimelineFeedRefetchQuery'
                break
            if 'CometUFICommentsProviderQuery_' in line:
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'CometUFICommentsProviderQuery'
                break
            else :
                continue
        resp.close()
        if req_name == "CometResharesFeedPaginationQuery":
            break
    print(f'feedback docid is: {docid}, req_name is: {req_name}')
    return "", docid, req_name, is_been_banned


    

def __getPageID__(pageURL, customDriver :webDriver.postsDriver) -> tuple[str, str, str, bool]:
    
    pageid = ''
    is_been_banned = False
    pageURL = re.sub('/$', '', pageURL)

    resp = requests.get(pageURL)
    resp = resp.text
    # *部分粉專有鎖年齡與國家,導致只能登入後才能瀏覽,故改用爬蟲登入法取得頁面資料
    if "pageID" not in resp:
        print("以selenium的爬蟲登入法取得pageid、docid")
        resp = customDriver._getSource(pageURL=pageURL)
    writer.writeTempFile(filename="sourceCode", content=resp) 
    if ("目前無法查看此內容" in resp) and ("empty_states_icons" in resp):
        is_been_banned = True
        return "", "", "", is_been_banned

    # pageID
    if len(re.findall('"pageID":"([0-9]{1,})",', resp)) >= 1:
        pageid = re.findall('"pageID":"([0-9]{1,})",', resp)[0]
    elif len(re.findall(r'"identifier":(.*?),', resp)) >= 1:
        pageid = re.findall(r'"identifier":(.*?),', resp)[0]
    elif len(re.findall(r'https://www.facebook.com/profile.php\?id=([0-9]{1,}).*"', resp)) >= 1:
        pageid = re.findall(r'https://www.facebook.com/profile.php\?id=([0-9]{1,}).*"', resp)[0]
    elif len(re.findall(r'https:\\/\\/www.facebook.com\\/profile.php\?id=([0-9]{1,}).*"', resp)) >= 1:
        pageid = re.findall(r'https:\\/\\/www.facebook.com\\/profile.php\?id=([0-9]{1,}).*"', resp)[0]
    elif len(re.findall('fb://group|page|profile/([0-9]{1,})', resp)) >= 1:
        pageid = re.findall('fb://group|page|profile/([0-9]{1,})', resp)[0]
    elif len(re.findall('delegate_page":\{"id":"(.*?)"\},', resp)) >= 1:
        pageid = re.findall('delegate_page":\{"id":"(.*?)"\},', resp)[0]
    else:
        pageid = ''

    # postid
    soup = BeautifulSoup(resp, 'lxml')
    docid = ""
    req_name = ""
    for js in soup.findAll('link', {'rel': 'preload'}):
        resp_href = requests.get(js['href'])
        for line in resp_href.text.split('\n', -1):
            if 'CometResharesFeedPaginationQuery_' in line:
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'CometResharesFeedPaginationQuery'
                break
            if 'ProfileCometTimelineFeedRefetchQuery_' in line:
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'ProfileCometTimelineFeedRefetchQuery'
                # 針對此種特殊類型的粉專,重新導向抓取正確的pageid
                if len(re.findall('"userID":"(.*?)"',resp)) >= 1:
                    pageid = re.findall('"userID":"(.*?)"', resp)[0]
                break

            if 'CometModernPageFeedPaginationQuery_' in line  and docid=="":
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'CometModernPageFeedPaginationQuery'
                break

            if 'CometUFICommentsProviderQuery_' in line:
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'CometUFICommentsProviderQuery'
                break
        resp_href.close()

    print('pageid is: {}'.format(pageid))
    print('docid is: {}'.format(docid))
    print(f"req_name is: {req_name}")
    return pageid, docid, req_name, is_been_banned


def __parsingFriendzoneNov__(resp: requests.Response) -> tuple[list, str]:
    edge_list = []
    writer.writeTempFile(filename="sourceCode_friendzone_edge", content=resp.text) 
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    temp_cursor = ""

    for edge in resp['data']['node']['pageItems']['edges']:
        try:
            edge = rawDataResolve.__resolverEdgesFriendzone__(edge)
            temp_cursor = edge["cursor"]
            edge_list.append(edge)
        except Exception as e:
            print(traceback.format_exc())
            continue
    cursor = temp_cursor
    return edge_list, cursor

def __parsingSectionAbout__(resp: requests.Response, aboutNumber) -> list:
    edge_list = []
    resps = resp.text.split('\r\n', -1)
    # writer.writeTempFile(filename="sourceCode_section_edge",content=resp.text) 
 
    for i, res in enumerate(resps):
        try:
            check =  json.loads(res)['data']['user']['about_app_sections']['nodes']      
            res_dict = rawDataResolve.__resolverEdgesSectionAbout__(check[0], aboutNumber=aboutNumber)
            edge_list.append(res_dict)
        except Exception as e:
            continue
    if len(edge_list)==0:
        raise UnboundLocalError("沒有取到關於的內容,重試")
    return edge_list

def __parsingProfileComet__(resp: requests.Response, jsonArrayData) -> tuple[list, str, bool, bool]:
    edge_list = []
    resps = resp.text.split('\r\n', -1)
    temp_cursor = ""
    is_up_to_time = True
    arrive_first_catch_time = False
    for i, res in enumerate(resps):
        check =  json.loads(res)['data']
        try:
            if len( check['node']['timeline_list_feed_units']['edges']) == 0:
                return [], "", is_up_to_time, arrive_first_catch_time
            else:
                for edge in check['node']['timeline_list_feed_units']['edges']:
                    try:
                        edge = rawDataResolve.__resolverEdgesPage__(edge)
                        temp_cursor = edge["cursor"]
                        if edge["creation_time"] != 0 :
                            is_up_to_time, arrive_first_catch_time = Auxiliary.dateCompare(edge["creation_time"], userSettingTime=jsonArrayData)
                            if is_up_to_time : 
                                edge_list.append(edge)
                    except Exception as e:
                        print(traceback.format_exc())
                        continue
        except:
            # print(traceback.format_exc())
            # print("other label data, abort")
            continue
    cursor = temp_cursor # DANGEROUS
    return edge_list, cursor, is_up_to_time, arrive_first_catch_time

def __parsingCometModern__(resp: requests.Response, jsonArrayData) -> tuple[list, str, bool, bool]:
    edge_list = []
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    temp_cursor = ""
    is_up_to_time = True
    arrive_first_catch_time = False
    for edge in resp['data']['node']['timeline_feed_units']['edges']:
        try:
            edge = rawDataResolve.__resolverEdgesPage__(edge)
            temp_cursor = edge["cursor"]
            is_up_to_time, arrive_first_catch_time = Auxiliary.dateCompare(edge["creation_time"], userSettingTime=jsonArrayData)
            if is_up_to_time : 
                edge_list.append(edge)
        except Exception as e:
            print(traceback.format_exc())
            continue
    cursor = temp_cursor # DANGEROUS
    return edge_list, cursor, is_up_to_time, arrive_first_catch_time

def __parsingFeedback__(resp: requests.Response, posts_count) -> tuple[list, str]:
    edge_list = []
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    temp_cursor = ""

    # 這段邏輯未來可能判斷上會用到,相關性:沒正常抓到分享者資料時
    # if "reshares" not in resp['data']['node']:
    #     raise UnboundLocalError

    # 該篇文章還沒有任何分享者,直接視作抓完資料跳出
    check = resp['data']['node']['reshares']['edges']
    if len(check) == 0:
        return [],""
        
    for edge in resp['data']['node']['reshares']['edges']:
        try:
            edge = rawDataResolve.__resolverEdgesFeedback__(edge, posts_count)
            temp_cursor = edge["cursor"]
            edge_list.append(edge)
        except Exception as e:
            print(traceback.format_exc())
            continue
        
    cursor = temp_cursor # DANGEROUS
    return edge_list, cursor



def hasNextPage(resp: requests.Response) -> bool:
    resp = json.loads(resp.text.split('\r\n', -1)[0])

    if 'timeline_feed_units' in  resp['data']['node']:
        has_next_page = resp['data']['node']['timeline_feed_units']['page_info']['has_next_page']
    elif 'timeline_list_feed_units' in resp['data']['node']:
        if len(resp['data']['node']['timeline_list_feed_units']['edges']) == 0:
            has_next_page = False
        else:
            has_next_page = True
    # elif resp.get('errors'):
    #     raise ServerException("Error from Server")

    return has_next_page


def hasNextPageFeedback(resp: requests.Response) -> bool:
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    if resp['data']['node']['reshares']:
        has_next_page = resp['data']['node']['reshares']['page_info']['has_next_page']
    # elif resp.get('errors'):
    #     raise ServerException("Error from Server")

    return has_next_page


def hasNextPageFriendzone(resp: requests.Response) -> bool:
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    if 'pageItems' in resp['data']['node']:
        has_next_page = resp['data']['node']['pageItems']['page_info']['has_next_page']
    else :
        has_next_page = False

    return has_next_page

def crawlPagePosts(pageURL, pageID, docID, reqName, jsonArrayData, proxyIpList, processNum, targetName) -> list:

    try_count = 0
    proxy_count = 0
    proxy_ip_list = proxyIpList
    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
    contents = []
    cursor = ''
    headers = __getHeaders__(pageURL)

    session = requests.session()
    # 設定失敗重試策略
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS","POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    is_up_to_time = True
    while True:
        print(f"行程{processNum}-> {targetName}:當前的標記 : {cursor}")
        data = {'variables': str({  "stream_count": "5",
                                    "cursor": cursor,
                                    "id": pageID,
                                    "scale":"1",
                                    "privacySelectorRenderLocation":"COMET_STREAM",
                                    "__relay_internal__pv__FBReelsEnableDeferrelayprovider":"false"}),
                    'doc_id': docID}
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                 data=data,
                                 headers=headers,
                                 timeout=20,
                                 verify="./config/certs.pem",
                                 proxies={'http': random_proxy_ip, "https":random_proxy_ip})
            if reqName == 'ProfileCometTimelineFeedRefetchQuery':
                edge_list, cursor_now, is_up_to_time, arrive_first_catch_time = __parsingProfileComet__(resp, jsonArrayData)
            elif reqName == 'CometModernPageFeedPaginationQuery':
                edge_list, cursor_now, is_up_to_time, arrive_first_catch_time = __parsingCometModern__(resp, jsonArrayData)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not hasNextPage(resp):
                raise UnboundLocalError(f"Reached the last page")
            else:
                cursor = cursor_now
            resp.close()
            time.sleep(random.randint(1,2))
            # 超過設定的撈取日期
            if (is_up_to_time == False) and (arrive_first_catch_time == True) :
                return contents
                
        except UnboundLocalError:
            print("Reached the last page")
            break

        except Exception as e:
            print(f"行程{processNum}-> Failed reason: {str(e)}" )
            print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,ProtocolError)) and (not isinstance(e,ChunkedEncodingError)) and (not isinstance(e,ConnectionError)) and (not isinstance(e,SSLError)) and  (not isinstance(e,UnboundLocalError)) and (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"pageid: {pageID}, docid: {docID}, cursor: {cursor}")

            proxy_count+=1
            if proxy_count >= len(proxy_ip_list):
                if try_count>=10000:
                    print(f"failed to catch posts after {try_count} times trying...")
                    return contents
                print("all proxy are down ! please refresh the proxyList")
                proxy_ip_list = proxy.gRequestsProxyList(processNum)
                proxy_count = 0
                try_count += 1
                random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
                continue
            else:
                random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
                continue
    session.close()
    return contents



def crawlFeedback(pageURL, feedbackID, docID, postsCount, reqName, fbDTSG, targetName, processNum, queue: Queue=None, queueSignal: Queue=None) -> list:
    try_count = 0
    proxy_count = 0
    proxy_ip_list = json.loads(os.environ['proxy_list'])
    random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
    contents = []
    cursor = ''
    headers = __getHeaders__(pageURL)
    session = requests.session()

    # 設定失敗重試策略
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS","POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    while True:
        # print(f"行程{process_num} {targetName}:當前的標記 : {cursor}")
        data = {'variables': str({
                                    "cursor": cursor,
                                    'id': feedbackID,
                                    "privacySelectorRenderLocation":"COMET_STREAM",
                                    "scale":"1",
                                    "__relay_internal__pv__FBReelsEnableDeferrelayprovider":"false"
                                    }),
                    'doc_id': docID,
                    "__a": "1",
                    "__comet_req": "15",
                    "fb_api_req_friendly_name":reqName
            }

        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                 data=data,
                                 headers=headers,
                                 timeout=20,
                                 verify="./config/certs.pem",
                                 proxies={'http': random_proxy_ip,"https":random_proxy_ip})
            edge_list, cursor_now = __parsingFeedback__(resp, postsCount)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not hasNextPageFeedback(resp):
                raise UnboundLocalError(f"Reached the last page")
            else:
                cursor = cursor_now
            resp.close()
                
        except UnboundLocalError:
            print("Reached the last page")
            break
            
        except Exception as e:
            # print(f"Failed reason : {str(e)}, feedback_id : {feedback_id}, post_id : {posts_count}" )
            # print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,ProtocolError)) and (not isinstance(e,ChunkedEncodingError)) and (not isinstance(e,ConnectionError)) and (not isinstance(e,SSLError)) and (not isinstance(e,UnboundLocalError)) and  (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack= f"post_id:{postsCount}, feedback_id:{feedbackID}, docid:{docID}, cursor:{cursor}")

            proxy_count+=1
            if proxy_count >= len(proxy_ip_list):
                if try_count >= 10000:
                    print(f"failed to catch SectionAbout after {try_count} times trying...")
                    return contents
                # 沒有使用多執行緒的走這邊
                if queueSignal is None:   
                    proxy_ip_list = proxy.gRequestsProxyList(processNum)
                    proxy_count = 0
                    try_count += 1
                    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                    continue
                else:
                    # 先比較環境變數中的proxyList有沒有更新
                    if json.dumps(proxy_ip_list) != os.environ['proxy_list']:
                        # print(f"行程{process_num} 發現環境變數已更新,直接從環境變數刷新proxyList")
                        proxy_ip_list = json.loads(os.environ['proxy_list'])
                        proxy_count = 0
                        random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                        continue
                    else:
                        #尚未有人更新,檢查當前是否有人占用更新proxyList的資格,若可以更新proxyList,執行後刷新環境變數
                        if queueSignal.qsize()==0:
                            queueSignal.put(str(processNum))
                            proxy_ip_list = proxy.gRequestsProxyList(processNum)
                            ip_list_str = json.dumps(proxy_ip_list)
                            os.environ['proxy_list'] = ip_list_str
                            proxy_count = 0
                            try_count += 1
                            random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
                            sig = queueSignal.get()
                            print(f"行程{processNum} proxyList更新完畢, 釋放queue_signal: {sig}")
                            continue
                        else:
                            # 有人占用,就先不更新proxyList, 直接取得當前環境變數中的proxyList來(等於跳空一輪)
                            # print(f"行程{process_num} 不更新proxyList,取當前的環境變數")
                            proxy_ip_list = json.loads(os.environ['proxy_list'])
                            proxy_count = 0
                            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                            continue
            else:
                random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                continue
    session.close()
    
    if queue is not None:
        queue.put(contents)
        if queue.qsize() % 50 == 0:
            print(f"行程{processNum}-> {targetName}:目前queue的長度為 {queue.qsize()}")

    return contents


def crawlSectionAbout(pageURL, fbDTSG, docID, userID, reqName, targetName, processNum, friendDict, queue: Queue=None, queueSignal: Queue=None) -> list:
    try_count = 0
    proxy_count = 0
    proxy_ip_list = json.loads(os.environ['proxy_list'])
    random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
    contents = []
    collection_token_list = []
    edge_list = []
    headers = __getHeaders__(pageURL)

    session = requests.session()
    # 設定失敗重試策略
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS","POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    while True:
        # print(f"開始抓取{targetName}的個人關於-總覽資料")
        # first call
        # collectionToken 不帶表示抓總覽
        data = {'variables': str({ 
                                "pageID": userID,
                                "userID": userID,
                                "scale":"1",
                                "__relay_internal__pv__FBReelsEnableDeferrelayprovider":"false",
                                "__relay_internal__pv__FBReelsDisableBackgroundrelayprovider":"false",
                                "__relay_internal__pv__FBReelsShowOverflowMenuInFeedbackBarrelayprovider":"false"
                                }),
                'doc_id': docID,
                "__a": "1",
                "__comet_req": "15",
                "fb_dtsg":fbDTSG,
                "fb_api_req_friendly_name":reqName
                }
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                    data=data,
                                    headers=headers,
                                    timeout=20,
                                    verify="./config/certs.pem",
                                    proxies={'http': random_proxy_ip, "https":random_proxy_ip})
            if reqName == 'ProfileCometAboutAppSectionQuery':
                edge_list = __parsingSectionAbout__(resp, 0)
                resp.close()
                break
             
        except Exception as e:
            # print("Failed reason : " ,str(e))
            # print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,ProtocolError)) and (not isinstance(e,ChunkedEncodingError)) and (not isinstance(e,ConnectionError)) and (not isinstance(e,SSLError)) and  (not isinstance(e,UnboundLocalError)) and  (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"userid: {userID}, docid: {docID}, collectionToken: 0")

            proxy_count+=1
            if proxy_count >= len(proxy_ip_list):
                if try_count >= 10000:
                    print(f"行程{processNum}-> failed to catch SectionAbout after {try_count} times trying...")
                    break
                # 沒有使用多執行緒的走這邊
                if queueSignal is None:   
                    proxy_ip_list = proxy.gRequestsProxyList(processNum)
                    proxy_count = 0
                    try_count += 1
                    random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
                    continue
                else:
                    # 先比較環境變數中的proxyList有沒有更新
                    if json.dumps(proxy_ip_list) != os.environ['proxy_list']:
                        # print(f"行程{process_num} 發現環境變數已更新,直接從環境變數刷新proxyList")
                        proxy_ip_list = json.loads(os.environ['proxy_list'])
                        proxy_count = 0
                        random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                        continue
                    else:
                        #尚未有人更新,檢查當前是否有人占用更新proxyList的資格,若可以更新proxyList,執行後刷新環境變數
                        if queueSignal.qsize() == 0:
                            queueSignal.put(str(processNum))
                            proxy_ip_list = proxy.gRequestsProxyList(processNum)
                            ip_list_str = json.dumps(proxy_ip_list)
                            os.environ['proxy_list'] = ip_list_str
                            proxy_count = 0
                            try_count += 1
                            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                            sig = queueSignal.get()
                            print(f"行程{processNum}-> proxyList 更新完畢, 釋放queue_signal: {sig}")
                            continue
                        else:
                            # 有人占用,就先不更新proxyList, 直接取得當前環境變數中的proxyList來(等於跳空一輪)
                            # print(f"行程{process_num} 不更新proxyList,取當前的環境變數")
                            proxy_ip_list = json.loads(os.environ['proxy_list'])
                            proxy_count = 0
                            random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
                            continue
            else:
                random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
                continue
    
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
                                 timeout=20,
                                 verify="./config/certs.pem",
                                 proxies={'http': random_proxy_ip,"https":random_proxy_ip})
            if reqName == 'ProfileCometAboutAppSectionQuery':
                edge_list = __parsingSectionAbout__(resp, collect_id_count)

            if len(edge_list) != 0:
                contents = contents + edge_list
                collect_id_count+=1
            resp.close()


        except Exception as e:
            # print("Failed reason : " ,str(e))
            # print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,ProtocolError)) and (not isinstance(e,ChunkedEncodingError)) and (not isinstance(e,ConnectionError)) and (not isinstance(e,SSLError)) and  (not isinstance(e,UnboundLocalError)) and (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"userid: {userID}, docid: {docID}, collectionToken: {collection_token_list[collect_id_count]}")

            proxy_count+=1
            if proxy_count >= len(proxy_ip_list):
                if try_count >= 10000:
                    print(f"行程{processNum}-> failed to catch SectionAbout after {try_count} times trying...")
                    return contents
                # 沒有使用多執行緒的走這邊
                if queueSignal is None:   
                    proxy_ip_list = proxy.gRequestsProxyList(processNum)
                    proxy_count = 0
                    try_count += 1
                    random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                    continue
                else:
                    # 先比較環境變數中的proxyList有沒有更新
                    if json.dumps(proxy_ip_list) != os.environ['proxy_list']:
                        # print(f"行程{process_num} 發現環境變數已更新,直接從環境變數刷新proxyList")
                        proxy_ip_list = json.loads(os.environ['proxy_list'])
                        proxy_count = 0
                        random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                        continue
                    else:
                        #尚未有人更新,檢查當前是否有人占用更新proxyList的資格,若可以更新proxyList,執行後刷新環境變數
                        if queueSignal.qsize() == 0:
                            queueSignal.put(str(processNum))
                            proxy_ip_list = proxy.gRequestsProxyList(processNum)
                            ip_list_str = json.dumps(proxy_ip_list)
                            os.environ['proxy_list'] = ip_list_str
                            proxy_count = 0
                            try_count += 1
                            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                            sig = queueSignal.get()
                            print(f"行程{processNum}-> proxyList 更新完畢, 釋放queue_signal: {sig}")
                            continue
                        else:
                            # 有人占用,就先不更新proxyList, 直接取得當前環境變數中的proxyList來(等於跳空一輪)
                            # print(f"行程{process_num} 不更新proxyList,取當前的環境變數")
                            proxy_ip_list = json.loads(os.environ['proxy_list'])
                            proxy_count = 0
                            random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                            continue
            else:
                random_proxy_ip = "http://" + proxy_ip_list[proxy_count]
                continue
    session.close()

    # 抓朋友群資料時將該朋友的dict補進去
    if friendDict is not None:
        contents.append(friendDict)
    if queue is not None:
        queue.put(contents)
        if queue.qsize() % 50 == 0:
            print(f"行程{processNum}-> {targetName}:目前queue的長度為 {queue.qsize()}")

    return contents


def crawlFriendzone(pageURL, friendzoneID, docID, reqName, proxyIpList, processNum, targetName) -> list:
    try_count = 0
    proxy_count = 0
    proxy_ip_list = proxyIpList
    random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
    contents = []
    cursor = ''
    
    headers = __getHeaders__(pageURL)
    # headers['cookie'] += cookieStr

    session = requests.session()
    # 設定失敗重試策略
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS","POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    while True:
       # print(f"行程{process_num} {targetName}:當前的標記 : {cursor}")
        data = {'variables': str({  
                                    "cursor": cursor,
                                    "id": friendzoneID,
                                    "scale": "1",
                                }),
                    'doc_id': docID}
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                 data=data,
                                 headers=headers,
                                 timeout=20,
                                 verify="./config/certs.pem",
                                 proxies={'http': random_proxy_ip,"https":random_proxy_ip})
            if reqName == 'ProfileCometAppCollectionListRendererPaginationQuery':
                edge_list, cursor_now = __parsingFriendzoneNov__(resp)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not hasNextPageFriendzone(resp):
                raise UnboundLocalError("Reached the last page")
            else:
                cursor = cursor_now
            resp.close()
            time.sleep(random.randint(1,2))

                
        except UnboundLocalError:
            print("Reached the last page")
            break

        except Exception as e:
            print(f"行程{processNum}-> Failed reason : {str(e)}" )
            print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,ProtocolError)) and (not isinstance(e,ChunkedEncodingError)) and (not isinstance(e,ConnectionError)) and (not isinstance(e,SSLError)) and  (not isinstance(e,UnboundLocalError)) and (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"friendzone_id: {friendzoneID}, docid: {docID}, cursor: {cursor}")

            proxy_count += 1
            if proxy_count >= len(proxy_ip_list):
                if try_count >= 10000:
                    print(f"行程{processNum}-> failed to catch posts after {try_count} times trying...")
                    return contents
                print("all proxy are down ! please refresh the proxyList")
                proxy_ip_list = proxy.gRequestsProxyList(processNum)
                proxy_count = 0
                try_count += 1
                random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
                continue
            else:
                random_proxy_ip ="http://" + proxy_ip_list[proxy_count]
                continue
    session.close()
    return contents


def fetchEigenvaluesAndID(func, customDriver: Union[webDriver.postsDriver, webDriver.feedbackDriver, webDriver.friendzoneDriver], pageURL, jsonArrayData, errString, checkOption=2) -> tuple[str, str, str, bool]:
    # checkOption-> 0: 只檢查id , 1:只檢查docid , 2: 兩個都檢查(預設值為2)
    accounts_len = len(jsonArrayData['user']['account'])
    account_num = os.environ.get("account_number_now")
    id = ""
    docid = ""
    req_name = ""
    if account_num is None:
        account_num = random.randint(0, accounts_len-1)
    else: 
        account_num = int(account_num)

    # 先檢查登入狀態,若未登入則先完成首次登入
    # 下方的判斷中,只要發現有取不到必要資料的情形,則捨棄當前的driver實體,重新創立一個並重新登入
    if customDriver.isLogin :
        pass
    else:
        customDriver.login(account_num, jsonArrayData)
        customDriver.isLogin = True 
    
    while True:
        id, docid, req_name, is_been_banned = func(pageURL=pageURL, customDriver=customDriver)

        # 若發現該頁面被臉書封鎖,則直接回傳空值與標記,由外部判斷處理
        if is_been_banned :
            return id, docid, req_name, is_been_banned

        match checkOption:
            case 0:
                if id != "":
                    os.environ['account_number_now'] = str(account_num)
                    return id, docid, req_name, is_been_banned
                else:
                    print(errString)
                    account_num += 1
                    if account_num == accounts_len:
                        account_num = 0
                    os.environ['account_number_now'] = str(account_num)
                    customDriver.clearDriver()
                    customDriver.driverInitialize()
                    customDriver.login(account_num, jsonArrayData)
                    customDriver.isLogin = True 
                    continue
            case 1:
                if docid != "":
                    os.environ['account_number_now'] = str(account_num)
                    return id, docid, req_name, is_been_banned
                else:
                    print(errString)
                    account_num += 1
                    if account_num == accounts_len:
                        account_num = 0
                    os.environ['account_number_now'] = str(account_num)
                    customDriver.clearDriver()
                    customDriver.driverInitialize()
                    customDriver.login(account_num, jsonArrayData)
                    customDriver.isLogin = True 
                    continue
            case 2:
                if docid != "" and id != "":
                    os.environ['account_number_now'] = str(account_num)
                    return id, docid, req_name, is_been_banned
                else:
                    print(errString)
                    account_num += 1
                    if account_num == accounts_len:
                        account_num = 0
                    os.environ['account_number_now'] = str(account_num)
                    customDriver.clearDriver()
                    customDriver.driverInitialize()
                    customDriver.login(account_num, jsonArrayData)
                    customDriver.isLogin = True 
                    continue