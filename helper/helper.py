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


def __get_headers__(pageurl):
    '''
    Send a request to get cookieid as headers.
    '''
    fake_user_agent = UserAgent()
    pageurl = re.sub('www', 'm', pageurl)
    resp = requests.get(pageurl)
    headers={'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
             'accept-language': 'en'}
    headers['cookie'] = '; '.join(['{}={}'.format(cookieid, resp.cookies.get_dict()[cookieid]) for cookieid in resp.cookies.get_dict()])
    headers['ec-ch-ua-platform'] = 'Windows'
    headers['user-agent'] = fake_user_agent.chrome
    headers['sec-fetch-site'] = "same-origin"
    # headers['Connection'] = 'close'
    # headers['cookie'] = headers['cookie'] + '; locale=en_US'
    resp.close()
    return headers


def __get_friendzone_nov_section__(pageurl,accountNumber,jsonArrayData):
    
    print("以selenium的爬蟲登入法取得userid、docid")
    userid = ''
    resp = webDriver.catchSectionFriendzoneSource(pageURL=pageurl,accountNumber=accountNumber,jsonArrayData=jsonArrayData)
    writer.writeTempFile(filename="sourceCode_friendzone",content=resp) 

    # userID
    if len(re.findall('"userID":"([0-9]{1,})",', resp)) >= 1:
        userid = re.findall('"userID":"([0-9]{1,})",', resp)[0]
    else:
        userid = ''

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
            resp_href = webDriver.catchspecialJS(js.get('src'))
            for line in resp_href.split('\n', -1):
                if 'ProfileCometAppCollectionListRendererPaginationQuery_' in line:
                    docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                    req_name = 'ProfileCometAppCollectionListRendererPaginationQuery'
                    break

    print('friendzoneid is {}'.format(friendzone_id))
    print('userid is: {}'.format(userid))
    print('docid is: {}'.format(docid))
    print(f"req_name is: {req_name}")
    return friendzone_id, userid, docid, req_name


def __get_userid_section__(pageurl,accountNumber,jsonArrayData):
    
    print("以selenium的爬蟲登入法取得userid、docid")
    userid = ''
    resp = webDriver.getPageSource(pageURL=pageurl,accountNumber=accountNumber,jsonArrayData=jsonArrayData)
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
    return userid, docid, req_name


def __get_pageid_feedback__(pageurl,accountNumber,jsonArrayData):

    # *部分粉專有鎖年齡與國家,導致只能登入後才能瀏覽,故改用爬蟲登入法取得頁面資料
    print("以selenium的爬蟲登入法取得feedback 的 docid")
    source = webDriver.catchFeedbackDynamicSource(pageurl,accountNumber,jsonArrayData=jsonArrayData)
    # feedbackid
    soup = BeautifulSoup(source, 'lxml')
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
        if req_name=="CometResharesFeedPaginationQuery":
            break
    print(f'feedback docid is: {docid}, req_name is: {req_name}')
    return docid, req_name


    

def __get_pageid__(pageurl,accountNumber,jsonArrayData):
    
    pageid = ''

    pageurl = re.sub('/$', '', pageurl)
    headers = __get_headers__(pageurl)
    time.sleep(1)

    resp = requests.get(pageurl, headers)
    resp = resp.text
    # *部分粉專有鎖年齡與國家,導致只能登入後才能瀏覽,故改用爬蟲登入法取得頁面資料
    if "pageID" not in resp:
        print("以selenium的爬蟲登入法取得pageid、docid")
        resp = webDriver.getPageSource(pageURL=pageurl,accountNumber=accountNumber,jsonArrayData=jsonArrayData)
    writer.writeTempFile(filename="sourceCode",content=resp) 

    # pageID
    if len(re.findall('"pageID":"([0-9]{1,})",', resp)) >= 1:
        pageid = re.findall('"pageID":"([0-9]{1,})",', resp)[0]
    elif len(re.findall(r'"identifier":(.*?),', resp)) >= 1:
        pageid = re.findall(r'"identifier":(.*?),', resp)[0]
    elif len(re.findall(r'https://www.facebook.com/profile.php\?id=([0-9]{1,}).*"',resp)) >= 1:
        pageid = re.findall(r'https://www.facebook.com/profile.php\?id=([0-9]{1,}).*"',resp)[0]
    elif len(re.findall(r'https:\\/\\/www.facebook.com\\/profile.php\?id=([0-9]{1,}).*"',resp)) >= 1:
        pageid = re.findall(r'https:\\/\\/www.facebook.com\\/profile.php\?id=([0-9]{1,}).*"',resp)[0]
    elif len(re.findall('fb://group|page|profile/([0-9]{1,})', resp)) >= 1:
        pageid = re.findall('fb://group|page|profile/([0-9]{1,})', resp)[0]
    elif len(re.findall('delegate_page":\{"id":"(.*?)"\},',resp)) >= 1:
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
    return pageid, docid, req_name


def __parsing_friendzone_nov__(resp):
    edge_list = []
    writer.writeTempFile(filename="sourceCode_friendzone_edge",content=resp.text) 
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    tempCursor = ""

    for edge in resp['data']['node']['pageItems']['edges']:
        try:
            edge = rawDataResolve.__resolver_friendzone_edge__(edge)
            tempCursor = edge["cursor"]
            edge_list.append(edge)
        except Exception as e:
            print(traceback.format_exc())
            continue
    cursor = tempCursor
    return edge_list, cursor

def __parsing_SectionAbout__(resp,aboutNumber):
    edge_list = []
    resps = resp.text.split('\r\n', -1)
    # writer.writeTempFile(filename="sourceCode_section_edge",content=resp.text) 
 
    for i, res in enumerate(resps):
        try:
            check =  json.loads(res)['data']['user']['about_app_sections']['nodes']      
            res_dict = rawDataResolve.__resolver_SectionAbout_edge__(check[0],aboutNumber=aboutNumber)
            edge_list.append(res_dict)
        except Exception as e:
            continue
    if len(edge_list)==0:
        raise UnboundLocalError("沒有取到關於的內容,重試")
    return edge_list

def __parsing_ProfileComet__(resp,jsonArrayData):
    edge_list = []
    resps = resp.text.split('\r\n', -1)
    tempCursor = ""
    isUpToTime = True
    arriveFirstCatchTime = False
    for i, res in enumerate(resps):
        check =  json.loads(res)['data']
        try:
            if len( check['node']['timeline_list_feed_units']['edges']) == 0:
                return [],"",isUpToTime
            else:
                for edge in check['node']['timeline_list_feed_units']['edges']:
                    try:
                        edge = rawDataResolve.__resolver_edge__(edge)
                        tempCursor = edge["cursor"]
                        if edge["creation_time"] != 0 :
                            isUpToTime,arriveFirstCatchTime = Auxiliary.dateCompare(edge["creation_time"],userSettingTime=jsonArrayData)
                            if isUpToTime : 
                                edge_list.append(edge)
                    except Exception as e:
                        print(traceback.format_exc())
                        continue
        except:
            # print(traceback.format_exc())
            # print("other label data, abort")
            continue
    cursor = tempCursor # DANGEROUS
    return edge_list, cursor, isUpToTime, arriveFirstCatchTime

def __parsing_CometModern__(resp,jsonArrayData):
    edge_list = []
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    tempCursor = ""
    isUpToTime = True
    arriveFirstCatchTime = False
    for edge in resp['data']['node']['timeline_feed_units']['edges']:
        try:
            edge = rawDataResolve.__resolver_edge__(edge)
            tempCursor = edge["cursor"]
            isUpToTime, arriveFirstCatchTime = Auxiliary.dateCompare(edge["creation_time"],userSettingTime=jsonArrayData)
            if isUpToTime : 
                edge_list.append(edge)
        except Exception as e:
            print(traceback.format_exc())
            continue
    cursor = tempCursor # DANGEROUS
    return edge_list, cursor, isUpToTime, arriveFirstCatchTime

def __parsing_Feedback__(resp,posts_count):
    edge_list = []
    resp = json.loads(resp.text.split('\r\n', -1)[0])

    # 這段邏輯未來可能判斷上會用到,相關性:沒正常抓到分享者資料時
    # if "reshares" not in resp['data']['node']:
    #     raise UnboundLocalError

    # 該篇文章還沒有任何分享者,直接視作抓完資料跳出
    check = resp['data']['node']['reshares']['edges']
    if len(check) == 0:
        return [],""
        
    for edge in resp['data']['node']['reshares']['edges']:
        try:
            edge = rawDataResolve.resolver_edges_feedback(edge,posts_count)
            edge_list.append(edge)
        except Exception as e:
            print(traceback.format_exc())
            continue
        
    cursor = edge_list[-1]["cursor"] # DANGEROUS
    return edge_list, cursor



def has_next_page(resp):
    resp = json.loads(resp.text.split('\r\n', -1)[0])

    if 'timeline_feed_units' in  resp['data']['node']:
        has_next_page = resp['data']['node']['timeline_feed_units']['page_info']['has_next_page']
    elif 'timeline_list_feed_units' in resp['data']['node']:
        if len(resp['data']['node']['timeline_list_feed_units']['edges'])==0:
            has_next_page = False
        else:
            has_next_page = True
    # elif resp.get('errors'):
    #     raise ServerException("Error from Server")

    return has_next_page


def has_next_page_feedback(resp):
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    if resp['data']['node']['reshares']:
        has_next_page = resp['data']['node']['reshares']['page_info']['has_next_page']
    # elif resp.get('errors'):
    #     raise ServerException("Error from Server")

    return has_next_page


def has_next_page_friendzone(resp):
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    if 'pageItems' in resp['data']['node']:
        has_next_page = resp['data']['node']['pageItems']['page_info']['has_next_page']
    else :
        has_next_page = False

    return has_next_page

def Crawl_PagePosts(pageurl,jsonArrayData,proxy_ip_list, process_num, targetName):

    tryCount = 0
    proxyCount = 0
    proxyIPList = proxy_ip_list
    randomProxyIP ="http://" + proxyIPList[proxyCount]
    contents = []
    cursor = ''
    headers = __get_headers__(pageurl)
    # Get pageid, postid and reqname

    accountsLen = len(jsonArrayData['user']['account'])
    account_num = os.environ.get("account_number_now")
    if account_num is None:
        account_num = random.randint(0,accountsLen-1)
    else: 
        account_num = int(account_num)
    while True:
        pageid, docid, req_name = __get_pageid__(pageurl=pageurl,accountNumber=account_num,jsonArrayData=jsonArrayData)
        if docid != "":
            os.environ['account_number_now'] = str(account_num)
            break
        else:
            print("未能取得文章的docid,嘗試換其他帳號試試")
            account_num+=1
            if account_num==accountsLen:
                account_num = 0
            os.environ['account_number_now'] = str(account_num)
            continue


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

    # # test
    # cursor = "AQHRvxZQu9-qubSB88HSiqoDq8XZh7czCjVQ__BKOSVKgR92RY-jYDigMBLRru8feLGQKVQ0oUluDuypfAYKGvQOhtylFy4RYowx0GQXak6CkEYl7lyj_ZahYl6s4syqOawH"
    # pageid = "100002814720095"
    # docid = "5511844245541805"

    isUpToTime = True
    while True:
        print(f"行程{process_num} {targetName}:當前的標記 : {cursor}")
        data = {'variables': str({  "stream_count": "5",
                                    "cursor": cursor,
                                    "id": pageid,
                                    "scale":"1",
                                    "privacySelectorRenderLocation":"COMET_STREAM",
                                    "__relay_internal__pv__FBReelsEnableDeferrelayprovider":"false"}),
                    'doc_id': docid}
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                 data=data,
                                 headers=headers,timeout=20,verify="./config/certs.pem",proxies={'http': randomProxyIP,"https":randomProxyIP})
            if req_name == 'ProfileCometTimelineFeedRefetchQuery':
                edge_list, cursor_now,isUpToTime, arriveFirstCatchTime = __parsing_ProfileComet__(resp,jsonArrayData)
            elif req_name == 'CometModernPageFeedPaginationQuery':
                edge_list, cursor_now,isUpToTime, arriveFirstCatchTime = __parsing_CometModern__(resp,jsonArrayData)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not has_next_page(resp=resp):
                raise UnboundLocalError(f"Reached the last page")
            else:
                cursor = cursor_now
            resp.close()
            time.sleep(random.randint(1,2))
            # 超過設定的撈取日期
            if (isUpToTime == False) and (arriveFirstCatchTime == True) :
                return contents
                
        except UnboundLocalError:
            print("Reached the last page")
            break

        except Exception as e:
            print(f"行程{process_num} :Failed reason : {str(e)}" )
            print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,ProtocolError)) and (not isinstance(e,ChunkedEncodingError)) and (not isinstance(e,ConnectionError)) and (not isinstance(e,SSLError)) and  (not isinstance(e,UnboundLocalError)) and (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"pageid: {pageid}, docid: {docid}, cursor: {cursor}")

            proxyCount+=1
            if proxyCount >= len(proxyIPList):
                if tryCount>=10000:
                    print(f"failed to catch posts after {tryCount} times trying...")
                    return contents
                print("all proxy are down ! please refresh the proxyList")
                proxyIPList = proxy.gRequestsProxyList(process_num=process_num)
                proxyCount = 0
                tryCount+=1
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
            else:
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
    session.close()
    return contents



def Crawl_PageFeedback(pageurl,feedback_id,docid,posts_count,req_name,fb_dtsg,targetName, process_num, queue=None, queue_signal=None):
    tryCount = 0
    proxyCount = 0
    proxyIPList = json.loads(os.environ['proxy_list'])
    randomProxyIP ="http://" + proxyIPList[proxyCount]
    contents = []
    cursor = ''
    headers = __get_headers__(pageurl)
    # Get postid and reqname
    session = requests.session()

    # 設定失敗重試策略
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS","POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(pool_connections=10,pool_maxsize=20,max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    while True:
        print(f"行程{process_num} {targetName}:當前的標記 : {cursor}")
        data = {'variables': str({
                                    "cursor": cursor,
                                    'id': feedback_id,
                                    "privacySelectorRenderLocation":"COMET_STREAM",
                                    "scale":"1",
                                    "__relay_internal__pv__FBReelsEnableDeferrelayprovider":"false"
                                    }),
                    'doc_id': docid,
                    "__a": "1",
                    "__comet_req": "15",
                    "fb_api_req_friendly_name":req_name
            }
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                 data=data,
                                 headers=headers,timeout=20,verify="./config/certs.pem",proxies={'http': randomProxyIP,"https":randomProxyIP})
            edge_list, cursor_now = __parsing_Feedback__(resp,posts_count)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not has_next_page_feedback(resp=resp):
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
                writer.writeLogToFile(traceBack=f"post_id: {posts_count},feedback_id : {feedback_id}, docid: {docid}, cursor: {cursor}")

            proxyCount+=1
            if proxyCount >= len(proxyIPList):
                if tryCount>=10000:
                    print(f"failed to catch SectionAbout after {tryCount} times trying...")
                    return contents
                # 沒有使用多執行緒的走這邊
                if queue_signal is None:   
                    proxyIPList = proxy.gRequestsProxyList(process_num=process_num)
                    proxyCount = 0
                    tryCount+=1
                    randomProxyIP ="http://" + proxyIPList[proxyCount]
                    continue
                else:
                    # 先比較環境變數中的proxyList有沒有更新
                    if json.dumps(proxyIPList) != os.environ['proxy_list']:
                        # print(f"行程{process_num} 發現環境變數已更新,直接從環境變數刷新proxyList")
                        proxyIPList = json.loads(os.environ['proxy_list'])
                        proxyCount = 0
                        randomProxyIP ="http://" + proxyIPList[proxyCount]
                        continue
                    else:
                        #尚未有人更新,檢查當前是否有人占用更新proxyList的資格,若可以更新proxyList,執行後刷新環境變數
                        if queue_signal.qsize()==0:
                            queue_signal.put(str(process_num))
                            proxyIPList = proxy.gRequestsProxyList(process_num=process_num)
                            ip_list_str = json.dumps(proxyIPList)
                            os.environ['proxy_list'] = ip_list_str
                            proxyCount = 0
                            tryCount+=1
                            randomProxyIP ="http://" + proxyIPList[proxyCount]
                            sig = queue_signal.get()
                            print(f"行程{process_num} proxyList 更新完畢, 釋放queue_signal: {sig}")
                            continue
                        else:
                            # 有人占用,就先不更新proxyList, 直接取得當前環境變數中的proxyList來(等於跳空一輪)
                            # print(f"行程{process_num} 不更新proxyList,取當前的環境變數")
                            proxyIPList = json.loads(os.environ['proxy_list'])
                            proxyCount = 0
                            randomProxyIP ="http://" + proxyIPList[proxyCount]
                            continue
            else:
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
    session.close()
    
    if queue is not None:
        queue.put(contents)
        if queue.qsize() % 50 == 0:
            print(f"行程{process_num} {targetName}:目前queue的長度:{queue.qsize()}")

    return contents


def Crawl_Section_About(pageurl,fb_dtsg,docid,userid,req_name,targetName,friendDict,process_num ,queue=None, queue_signal=None):
    tryCount = 0
    proxyCount = 0
    proxyIPList = json.loads(os.environ['proxy_list'])
    randomProxyIP ="http://" + proxyIPList[proxyCount]
    contents = []
    collectionTokenList = []
    edge_list = []
    headers = __get_headers__(pageurl)

    session = requests.session()
    # 設定失敗重試策略
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS","POST"],
        backoff_factor=0.5
    )
    adapter = HTTPAdapter(pool_connections=10,pool_maxsize=20,max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    while True:
        # print(f"開始抓取{targetName}的個人關於-總覽資料")
        # first call
        # collectionToken 不帶表示抓總覽
        data = {'variables': str({ 
                                "pageID": userid,
                                "userID": userid,
                                "scale":"1",
                                "__relay_internal__pv__FBReelsEnableDeferrelayprovider":"false",
                                "__relay_internal__pv__FBReelsDisableBackgroundrelayprovider":"false",
                                "__relay_internal__pv__FBReelsShowOverflowMenuInFeedbackBarrelayprovider":"false"
                                }),
                'doc_id': docid,
                "__a": "1",
                "__comet_req": "15",
                "fb_dtsg":fb_dtsg,
                "fb_api_req_friendly_name":req_name
                }
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                    data=data,
                                    headers=headers,timeout=20,verify="./config/certs.pem",proxies={'http': randomProxyIP,"https":randomProxyIP})
            if req_name == 'ProfileCometAboutAppSectionQuery':
                edge_list = __parsing_SectionAbout__(resp,0)
                resp.close()
                break
             
        except Exception as e:
            # print("Failed reason : " ,str(e))
            # print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,ProtocolError)) and (not isinstance(e,ChunkedEncodingError)) and (not isinstance(e,ConnectionError)) and (not isinstance(e,SSLError)) and  (not isinstance(e,UnboundLocalError)) and  (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"userid: {userid}, docid: {docid}, collectionToken: 0")

            proxyCount+=1
            if proxyCount >= len(proxyIPList):
                if tryCount>=10000:
                    print(f"failed to catch SectionAbout after {tryCount} times trying...")
                    break
                # 沒有使用多執行緒的走這邊
                if queue_signal is None:   
                    proxyIPList = proxy.gRequestsProxyList(process_num=process_num)
                    proxyCount = 0
                    tryCount+=1
                    randomProxyIP ="http://" + proxyIPList[proxyCount]
                    continue
                else:
                    # 先比較環境變數中的proxyList有沒有更新
                    if json.dumps(proxyIPList) != os.environ['proxy_list']:
                        # print(f"行程{process_num} 發現環境變數已更新,直接從環境變數刷新proxyList")
                        proxyIPList = json.loads(os.environ['proxy_list'])
                        proxyCount = 0
                        randomProxyIP ="http://" + proxyIPList[proxyCount]
                        continue
                    else:
                        #尚未有人更新,檢查當前是否有人占用更新proxyList的資格,若可以更新proxyList,執行後刷新環境變數
                        if queue_signal.qsize()==0:
                            queue_signal.put(str(process_num))
                            proxyIPList = proxy.gRequestsProxyList(process_num=process_num)
                            ip_list_str = json.dumps(proxyIPList)
                            os.environ['proxy_list'] = ip_list_str
                            proxyCount = 0
                            tryCount+=1
                            randomProxyIP ="http://" + proxyIPList[proxyCount]
                            sig = queue_signal.get()
                            print(f"行程{process_num} proxyList 更新完畢, 釋放queue_signal: {sig}")
                            continue
                        else:
                            # 有人占用,就先不更新proxyList, 直接取得當前環境變數中的proxyList來(等於跳空一輪)
                            # print(f"行程{process_num} 不更新proxyList,取當前的環境變數")
                            proxyIPList = json.loads(os.environ['proxy_list'])
                            proxyCount = 0
                            randomProxyIP ="http://" + proxyIPList[proxyCount]
                            continue
            else:
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
    
    contents = contents + edge_list
    collectionTokenList = edge_list[0]['id_output']
    collectIDCount = 1

    while True:
        # print(f"{targetName} 的抓取進度: {collectIDCount}")
        # 關於裡面的資料不須全拿,多餘的直接略過
        if collectIDCount >= 5:
            break
        data = {'variables': str({ 
                                    "collectionToken":collectionTokenList[collectIDCount],
                                    "pageID": userid,
                                    "userID": userid,
                                    "scale":"1",
                                    "__relay_internal__pv__FBReelsEnableDeferrelayprovider":"false",
                                    "__relay_internal__pv__FBReelsDisableBackgroundrelayprovider":"false",
                                    "__relay_internal__pv__FBReelsShowOverflowMenuInFeedbackBarrelayprovider":"false"
                                    }),
                    'doc_id': docid,
                    "__a": "1",
                    "__comet_req": "15",
                    "fb_dtsg":fb_dtsg,
                    "fb_api_req_friendly_name":req_name
                    }
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                 data=data,
                                 headers=headers,timeout=20,verify="./config/certs.pem",proxies={'http': randomProxyIP,"https":randomProxyIP})
            if req_name == 'ProfileCometAboutAppSectionQuery':
                edge_list = __parsing_SectionAbout__(resp,collectIDCount)

            if len(edge_list)!=0:
                contents = contents + edge_list
                collectIDCount+=1
            resp.close()


        except Exception as e:
            # print("Failed reason : " ,str(e))
            # print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,ProtocolError)) and (not isinstance(e,ChunkedEncodingError)) and (not isinstance(e,ConnectionError)) and (not isinstance(e,SSLError)) and  (not isinstance(e,UnboundLocalError)) and (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"userid: {userid}, docid: {docid}, collectionToken: {collectionTokenList[collectIDCount]}")

            proxyCount+=1
            if proxyCount >= len(proxyIPList):
                if tryCount>=10000:
                    print(f"failed to catch SectionAbout after {tryCount} times trying...")
                    return contents
                # 沒有使用多執行緒的走這邊
                if queue_signal is None:   
                    proxyIPList = proxy.gRequestsProxyList(process_num=process_num)
                    proxyCount = 0
                    tryCount+=1
                    randomProxyIP ="http://" + proxyIPList[proxyCount]
                    continue
                else:
                    # 先比較環境變數中的proxyList有沒有更新
                    if json.dumps(proxyIPList) != os.environ['proxy_list']:
                        # print(f"行程{process_num} 發現環境變數已更新,直接從環境變數刷新proxyList")
                        proxyIPList = json.loads(os.environ['proxy_list'])
                        proxyCount = 0
                        randomProxyIP ="http://" + proxyIPList[proxyCount]
                        continue
                    else:
                        #尚未有人更新,檢查當前是否有人占用更新proxyList的資格,若可以更新proxyList,執行後刷新環境變數
                        if queue_signal.qsize()==0:
                            queue_signal.put(str(process_num))
                            proxyIPList = proxy.gRequestsProxyList(process_num=process_num)
                            ip_list_str = json.dumps(proxyIPList)
                            os.environ['proxy_list'] = ip_list_str
                            proxyCount = 0
                            tryCount+=1
                            randomProxyIP ="http://" + proxyIPList[proxyCount]
                            sig = queue_signal.get()
                            print(f"行程{process_num} proxyList 更新完畢, 釋放queue_signal: {sig}")
                            continue
                        else:
                            # 有人占用,就先不更新proxyList, 直接取得當前環境變數中的proxyList來(等於跳空一輪)
                            # print(f"行程{process_num} 不更新proxyList,取當前的環境變數")
                            proxyIPList = json.loads(os.environ['proxy_list'])
                            proxyCount = 0
                            randomProxyIP ="http://" + proxyIPList[proxyCount]
                            continue
            else:
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
    session.close()

    # 抓朋友群資料時將該朋友的dict補進去
    if friendDict is not None:
        contents.append(friendDict)
    if queue is not None:
        queue.put(contents)
        if queue.qsize() % 50 == 0:
            print(f"行程{process_num} {targetName}:目前queue的長度:{queue.qsize()}")

    return contents


def Crawl_friendzone(pageurl,jsonArrayData,proxy_ip_list, process_num, targetName):
    tryCount = 0
    proxyCount = 0
    proxyIPList = proxy_ip_list
    randomProxyIP ="http://" + proxyIPList[proxyCount]
    contents = []
    cursor = ''
    
    headers = __get_headers__(pageurl)
    # headers['cookie'] += cookieStr

    # Get pageid, postid and reqname

    accountsLen = len(jsonArrayData['user']['account'])
    account_num = os.environ.get("account_number_now")
    if account_num is None:
        account_num = random.randint(0,accountsLen-1)
    else: 
        account_num = int(account_num)
    while True:
        friendzone_id,userid, docid, req_name = __get_friendzone_nov_section__(pageurl,account_num,jsonArrayData=jsonArrayData)
        if docid != "" and friendzone_id!= "":
            os.environ['account_number_now'] = str(account_num)
            break
        else:
            print("未能取得朋友欄目的docid 或 friendzone_id,嘗試換其他帳號試試")
            account_num+=1
            if account_num==accountsLen:
                account_num = 0
            os.environ['account_number_now'] = str(account_num)
            continue




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

    # # test
    # cursor = "AQHRvxZQu9-qubSB88HSiqoDq8XZh7czCjVQ__BKOSVKgR92RY-jYDigMBLRru8feLGQKVQ0oUluDuypfAYKGvQOhtylFy4RYowx0GQXak6CkEYl7lyj_ZahYl6s4syqOawH"
    # pageid = "100002814720095"
    # docid = "5511844245541805"

    while True:
       # print(f"行程{process_num} {targetName}:當前的標記 : {cursor}")
        data = {'variables': str({  
                                    "cursor": cursor,
                                    "id": friendzone_id,
                                    "scale":"1",
                                }),
                    'doc_id': docid}
        try:
            resp = session.post(url='https://www.facebook.com/api/graphql/',
                                 data=data,
                                 headers=headers,timeout=20,verify="./config/certs.pem",proxies={'http': randomProxyIP,"https":randomProxyIP})
            if req_name == 'ProfileCometAppCollectionListRendererPaginationQuery':
                edge_list, cursor_now = __parsing_friendzone_nov__(resp)

            # 文章有分享的資料才做處理
            if len(edge_list) != 0:
                contents = contents + edge_list
            if not has_next_page_friendzone(resp=resp):
                raise UnboundLocalError("Reached the last page")
            else:
                cursor = cursor_now
            resp.close()
            time.sleep(random.randint(1,2))

                
        except UnboundLocalError:
            print("Reached the last page")
            break

        except Exception as e:
            print(f"行程{process_num} :Failed reason : {str(e)}" )
            print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,ProtocolError)) and (not isinstance(e,ChunkedEncodingError)) and (not isinstance(e,ConnectionError)) and (not isinstance(e,SSLError)) and  (not isinstance(e,UnboundLocalError)) and (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"friendzone_id: {friendzone_id}, docid: {docid}, cursor: {cursor}")

            proxyCount+=1
            if proxyCount >= len(proxyIPList):
                if tryCount>=10000:
                    print(f"failed to catch posts after {tryCount} times trying...")
                    return contents
                print("all proxy are down ! please refresh the proxyList")
                proxyIPList = proxy.gRequestsProxyList(process_num=process_num)
                proxyCount = 0
                tryCount+=1
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
            else:
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
    session.close()
    return contents