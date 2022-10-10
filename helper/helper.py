from inspect import Traceback
from tempfile import tempdir
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
from helper import proxy,Auxiliary
from webManager import webDriver
from ioService import writer,reader
from urllib3.exceptions import ConnectTimeoutError,MaxRetryError
from requests.exceptions import ProxyError,ConnectTimeout


def __get_cookieid__(pageurl):
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


def __get_userid_section__(pageurl,accountNumber):
    
    print("以selenium的爬蟲登入法取得userid、docid")
    userid = ''
    resp = webDriver.getPageSource(pageURL=pageurl,accountNumber=accountNumber)
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


def __get_pageid_feedback__(pageurl,accountNumber):

    # *部分粉專有鎖年齡與國家,導致只能登入後才能瀏覽,故改用爬蟲登入法取得頁面資料
    print("以selenium的爬蟲登入法取得feedback 的 docid")
    source = webDriver.catchFeedbackDynamicSource(pageurl,accountNumber)
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
        if req_name=="CometResharesFeedPaginationQuery":
            break
    print(f'feedback docid is: {docid}, req_name is: {req_name}')
    resp.close()
    return docid, req_name


    

def __get_pageid__(pageurl,accountNumber):

    # pageurl = re.sub('/$', '', pageurl)
    # headers = __get_cookieid__(pageurl)
    # time.sleep(1)

    # resp = requests.get(pageurl, headers)
    # resp = resp.text
    # print(resp)
    # *部分粉專有鎖年齡與國家,導致只能登入後才能瀏覽,故改用爬蟲登入法取得頁面資料
    print("以selenium的爬蟲登入法取得pageid、docid")
    pageid = ''
    resp = webDriver.getPageSource(pageURL=pageurl,accountNumber=accountNumber)
    f = open("./temp/sourceCode.txt", "w",encoding='utf_8')
    f.write(resp)
    f.close()
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
                # 針對此種特殊類行的粉專,重新導向抓取正確的pageid
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

    print('pageid is: {}'.format(pageid))
    print('docid is: {}'.format(docid))
    print(f"req_name is: {req_name}")
    resp_href.close()
    return pageid, docid, req_name


def __parsing_edge__(edge):

    ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')

    # name
    try:
        comet_sections_ = edge['node']['comet_sections']
        name = comet_sections_['context_layout']['story']['comet_sections']['actor_photo']['story']['actors'][0]['name']
        # creation_time
        creation_time = comet_sections_['context_layout']['story']['comet_sections']['metadata'][0]['story']['creation_time']
        # message
        message = comet_sections_['content']['story']['comet_sections'].get('message','').get('story','').get('message','').get('text','') if comet_sections_['content']['story']['comet_sections'].get('message','') else ''
        message= ILLEGAL_CHARACTERS_RE.sub(r'', message)
        # postid
        postid = comet_sections_['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['subscription_target_id']
        # actorid
        pageid = comet_sections_['context_layout']['story']['comet_sections']['actor_photo']['story']['actors'][0]['id']
        # comment_count
        comment_count = comet_sections_['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comment_count']['total_count']
        # reaction_count
        reaction_count = comet_sections_['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comet_ufi_summary_and_actions_renderer']['feedback']['reaction_count']['count']
        # share_count
        share_count = comet_sections_['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comet_ufi_summary_and_actions_renderer']['feedback']['share_count']['count']
        # toplevel_comment_count
        toplevel_comment_count = comet_sections_['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['toplevel_comment_count']['count']
        # top_reactions
        top_reactions = comet_sections_['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comet_ufi_summary_and_actions_renderer']['feedback']['cannot_see_top_custom_reactions']['top_reactions']['edges']
        
        #feedback_id 
        feedback_id = comet_sections_['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['id']
        # url
        url = comet_sections_['context_layout']['story']['comet_sections']['metadata'][0]['story']['url']         
        # cursor
    except:
        print("此篇文章格式不可抓取")
        writer.writeLogToFile(traceBack=traceback.format_exc())
        name = ""
        creation_time = 0
        message = ""
        postid = ""
        pageid = ""
        comment_count = ""
        reaction_count = ""
        share_count = ""
        toplevel_comment_count = ""
        top_reactions = ""
        feedback_id = ""
        url = ""
        


    # image url 
    if len(comet_sections_['content']['story']['attachments']) == 0:
        image_url = ""
    else:
        try :
            attachObj = comet_sections_['content']['story']['attachments'][0]['styles']['attachment']
            # 單張圖片
            if "media" in attachObj:
                if "photo_image" in attachObj['media']:
                    image_url =  attachObj['media']['photo_image']['uri']
                elif "image" in  attachObj['media']:
                    image_url =  attachObj['media']['image']['uri']
                else :
                    image_url = ""
            # 多張圖片
            elif "all_subattachments" in attachObj:
                try : 
                    image_url = attachObj['all_subattachments']['nodes'][0]['media']['image']['uri']
                except:
                    writer.writeLogToFile(traceBack=traceback.format_exc())
                finally:
                    image_url = ""
            else:
                image_url = ""
        except:
            print("這篇文章不含圖片格式供抓取,可能是分享影片格式")
            writer.writeLogToFile(traceBack=traceback.format_exc())
            image_url = ""

    cursor = edge['cursor']

    dict_output = {
        "name":name,
        "creation_time":creation_time,
        "message":message,
        "postid":postid,
        "pageid":pageid,
        "feedback_id":feedback_id,
        "comment_count":comment_count,
        "reaction_count":reaction_count,
        "share_count":share_count,
        "toplevel_comment_count":toplevel_comment_count,
        "top_reactions":top_reactions,
        "url":url,
        "image_url":image_url,
        "cursor":cursor
    }

    return dict_output
    # return [name, creation_time, message, postid, pageid,feedback_id, comment_count, reaction_count, share_count, toplevel_comment_count, top_reactions,url,image_url, cursor]


def parsing_edges_feedback(edge,posts_count):
    comet_sections_ = edge['node']['comet_sections']

    # 分享者名稱
    sharer_name = comet_sections_['content']['story']['comet_sections']['context_layout']['story']['comet_sections']['title']['story']['actors'][0]['name']
    
    # 分享時間
    create_time = comet_sections_['context_layout']['story']['comet_sections']['metadata'][0]['story']['creation_time']

    # 分享者id
    sharer_id = comet_sections_['content']['story']['comet_sections']['context_layout']['story']['comet_sections']['title']['story']['actors'][0]['id']
    # 內容
    contents_checkPoint = comet_sections_['content']['story']['message']
    if not contents_checkPoint is None:
        contents = contents_checkPoint['text']
    else:
        contents = ""
    
    #被分享者可能不存在
    #被分享者名稱(需另外處理)
    been_sharer_checkPoint = comet_sections_['content']['story']['comet_sections']['context_layout']['story']['comet_sections']['title']['story']['title']
    if not been_sharer_checkPoint is None:
        been_sharer_raw_name = been_sharer_checkPoint['text']
        #被分享者網址
        been_sharer_id = edge['node']['feedback']['associated_group']['id']
    else:
        been_sharer_raw_name = ""
        been_sharer_id = ""

    # cursor
    cursor = edge['cursor']

    dict_output = {
        "posts_count":str(posts_count),
        "sharer_name":sharer_name,
        "create_time":create_time,
        "sharer_id":sharer_id,
        "contents":contents,
        "been_sharer_raw_name":been_sharer_raw_name,
        "been_sharer_id":been_sharer_id,
        "cursor":cursor
    }

    return dict_output
    # return [str(posts_count),sharer_name,create_time,sharer_id,contents,been_sharer_raw_name,been_sharer_id,cursor]

def _parsing_SectionAbout_edge__(edge,aboutNumber):
    # 0:總覽，1:學歷與工作經歷，2:住過的地方，3:聯絡和基本資料，4:家人和感情狀況
    match aboutNumber:
        case 0:
            about_id_list = []
            name = "總覽"
            for obj in edge['all_collections']['nodes']:
                id = obj['id']
                about_id_list.append(id)
            dict_output = {
                "id_output":about_id_list,
                "name":name
            }
            return dict_output
        case 1:
            startPoint = edge['activeCollections']['nodes'][0]['style_renderer']['profile_field_sections']
            name = "學經歷"
            work_name_list = []
            work_link_list = []
            work_date_list = []
            college_name_list = []
            college_link_list = []
            college_date_list = []
            highSchool_name_list = []
            highSchool_link_list = []
            highSchool_date_list = []

            for number in range(0,len(startPoint)):
                profile_fields = startPoint[number]["profile_fields"]["nodes"]
                for innerNumber in range(0,len(profile_fields)):
                    if profile_fields[innerNumber]['field_type'] == "null_state":
                        break
                    else:
                        match number:
                            case 0: #工作
                                work_name_list.append(profile_fields[innerNumber]['title']['text'])
                                if len(profile_fields[innerNumber]['list_item_groups'])!=0:
                                    work_date_list.append(profile_fields[innerNumber]['list_item_groups'][0]['list_items'][0]['text']['text'])
                                else:
                                    work_date_list.append("")
                                if len(profile_fields[innerNumber]['title']['ranges'])!=0:
                                    work_link_list.append(profile_fields[innerNumber]['title']['ranges'][0]['entity']['url'])
                                else:
                                    work_link_list.append("")
                            case 1: #大專院校
                                college_name_list.append(profile_fields[innerNumber]['title']['text'])
                                if len(profile_fields[innerNumber]['list_item_groups'])!=0:
                                    college_date_list.append(profile_fields[innerNumber]['list_item_groups'][0]['list_items'][0]['text']['text'])
                                else:
                                    college_date_list.append("")
                                if len(profile_fields[innerNumber]['title']['ranges'])!=0:
                                    college_link_list.append(profile_fields[innerNumber]['title']['ranges'][0]['entity']['url'])
                                else:
                                    college_link_list.append("")
                            case 2: #高中
                                highSchool_name_list.append(profile_fields[innerNumber]['title']['text'])
                                if len(profile_fields[innerNumber]['list_item_groups'])!=0:
                                    highSchool_date_list.append(profile_fields[innerNumber]['list_item_groups'][0]['list_items'][0]['text']['text'])
                                else:
                                    highSchool_date_list.append("")
                                if len(profile_fields[innerNumber]['title']['ranges'])!=0:
                                    highSchool_link_list.append(profile_fields[innerNumber]['title']['ranges'][0]['entity']['url'])
                                else:
                                    highSchool_link_list.append("")

            about_work_dict = {
                "name":work_name_list,
                "link":work_link_list,
                "date":work_date_list
            }
            about_college_dict = {
                "name":college_name_list,
                "link":college_link_list,
                "date":college_date_list
            }
            about_highSchool_dict = {
                "name":highSchool_name_list,
                "link":highSchool_link_list,
                "date":highSchool_date_list
            }
            dict_output = {
                "name":name,
                "work":about_work_dict,
                "college":about_college_dict,
                "highSchool":about_highSchool_dict
            }
            return dict_output
        case 2:
            startPoint = edge['activeCollections']['nodes'][0]['style_renderer']['profile_field_sections']
            name = "居住"
            live_name_list = []
            live_type_list = []
            live_link_list = []
            for number in range(0,len(startPoint)):
                profile_fields = startPoint[number]["profile_fields"]["nodes"]
                for innerNumber in range(0,len(profile_fields)):
                        if profile_fields[innerNumber]['field_type'] == "null_state":
                            break
                        else:
                            live_name_list.append(profile_fields[innerNumber]['title']['text'])
                            live_type_list.append(profile_fields[innerNumber]['field_type']) # current_city、hometown
                            if len(profile_fields[innerNumber]['title']['ranges'])!=0:
                                live_link_list.append(profile_fields[innerNumber]['title']['ranges'][0]['entity']['url'])
                            else:
                                live_link_list.append("")

            about_live_dict = {
                "name":live_name_list,
                "link":live_link_list,
                "type":live_type_list
            }

            dict_output = {
                "name":name,
                "live":about_live_dict
            }
            return dict_output
        case 3:
            startPoint = edge['activeCollections']['nodes'][0]['style_renderer']['profile_field_sections']
            name = "社群"
            phone = ""
            email = ""
            address = ""
            gender = ""
            birthday_date = ""
            birthday_year = ""
            social_name_list = []
            social_link_list = []
            social_type_list = []

            for number in range(0,len(startPoint)):
                profile_fields = startPoint[number]["profile_fields"]["nodes"]
                for innerNumber in range(0,len(profile_fields)):
                    if profile_fields[innerNumber]['field_type'] == "null_state":
                        break
                    else:
                        match number:
                            case 0: #聯絡
                                match profile_fields[innerNumber]['field_type']:
                                    case "other_phone":
                                        phone =  profile_fields[innerNumber]['title']['text']
                                    case "address":
                                        address = profile_fields[innerNumber]['title']['text']
                                    case "email":
                                        email = profile_fields[innerNumber]['title']['text']
                                    case _:
                                        print(f"{profile_fields[innerNumber]['field_type']} 不是欲收集的聯絡資料")
                            case 1: #社群
                                social_name_list.append(profile_fields[innerNumber]['title']['text'])
                                social_type_list.append(profile_fields[innerNumber]['list_item_groups'][0]['list_items'][0]['text']['text'])
                                if profile_fields[innerNumber]['link_url'] is None:
                                    social_link_list.append(profile_fields[innerNumber]['title']['text'])
                                else :
                                    social_link_list.append(profile_fields[innerNumber]['link_url'])
                            case 2: #基本資料
                                match profile_fields[innerNumber]['field_type']:
                                    case "gender":
                                        gender =  profile_fields[innerNumber]['title']['text']
                                    case "birthday":
                                        if profile_fields[innerNumber]['list_item_groups'][0]['list_items'][0]['text']['text'] == "Birth date":
                                            birthday_date = profile_fields[innerNumber]['title']['text']
                                        else :
                                            birthday_year = profile_fields[innerNumber]['title']['text']
                                    case _:
                                        print(f"{profile_fields[innerNumber]['field_type']} 不是欲收集的聯絡資料")
            about_social_dict = {
                "name":social_name_list,
                "link":social_link_list,
                "type":social_type_list
            }
            dict_output = {
                "name":name,
                "phone":phone,
                "email":email,
                "gender":gender,
                "address":address,
                "birthday_date":birthday_date,
                "birthday_year":birthday_year,
                "social":about_social_dict
            }

            return dict_output
        case 4:
            startPoint = edge['activeCollections']['nodes'][0]['style_renderer']['profile_field_sections']
            name = "人際"
            relationship_name_list=  []
            relationship_link_list = []
            relationship_type_list = []

            for number in range(0,len(startPoint)):
                profile_fields = startPoint[number]["profile_fields"]["nodes"]
                for innerNumber in range(0,len(profile_fields)):
                    if profile_fields[innerNumber]['field_type'] == "null_state":
                        break
                    else:
                        match number:
                            case 0: #感情狀況
                                if len(profile_fields[innerNumber]['list_item_groups'])!=0: # 單身
                                    relationship_name_list.append(profile_fields[innerNumber]['title']['text'])
                                    relationship_type_list.append("情侶")
                                    if len(profile_fields[innerNumber]['title']['ranges'])!=0:
                                        relationship_link_list.append(profile_fields[innerNumber]['title']['ranges'][0]['entity']['url'])
                                    else:
                                        relationship_link_list.append("")                            
                            case 1: #家人與親屬
                                relationship_name_list.append(profile_fields[innerNumber]['title']['text'])

                                if len(profile_fields[innerNumber]['list_item_groups'])!=0:
                                    relationship_type_list.append(profile_fields[innerNumber]['list_item_groups'][0]['list_items'][0]['text']['text'])
                                else:
                                    relationship_type_list.append("")

                                if len(profile_fields[innerNumber]['title']['ranges'])!=0:
                                    relationship_link_list.append(profile_fields[innerNumber]['title']['ranges'][0]['entity']['url'])
                                    if relationship_link_list[-1] is None :
                                        relationship_link_list[-1] = ""
                                else:
                                    relationship_link_list.append("")
                about_relationship_dict = {
                    "name":relationship_name_list,
                    "link":relationship_link_list,
                    "type":relationship_type_list
                }
                
                dict_output = {
                    "name":name,
                    "relationship":about_relationship_dict
                }

            return dict_output
        case _:
            print(f"編號{str(aboutNumber)}為當前不需要的資料")
            return {}


def __parsing_SectionAbout__(resp,aboutNumber):
    edge_list = []
    resps = resp.text.split('\r\n', -1)
    f = open("./temp/sourceCode_section.txt", "w",encoding='utf_8')
    f.write(resp.text)
    f.close()      
    for i, res in enumerate(resps):
        try:
            check =  json.loads(res)['data']['user']['about_app_sections']['nodes']      
            res_dict = _parsing_SectionAbout_edge__(check[0],aboutNumber=aboutNumber)
            edge_list.append(res_dict)
        except:
            continue
    if len(edge_list)==0:
        raise UnboundLocalError(f"沒有取到關於的內容,重試")
    return edge_list

def __parsing_ProfileComet__(resp):
    edge_list = []
    resps = resp.text.split('\r\n', -1)
    tempCursor = ""
    isUpToTime = True
    for i, res in enumerate(resps):
        check =  json.loads(res)['data']
        try:
            if len( check['node']['timeline_list_feed_units']['edges']) == 0:
                return [],"",isUpToTime
            else:
                for edge in check['node']['timeline_list_feed_units']['edges']:
                    try:
                        edge = __parsing_edge__(edge)
                        tempCursor = edge["cursor"]
                        if edge["creation_time"] != 0 :
                            isUpToTime = Auxiliary.dateCompare(edge["creation_time"])
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
    return edge_list, cursor, isUpToTime

def __parsing_CometModern__(resp):
    edge_list = []
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    isUpToTime = True
    for edge in resp['data']['node']['timeline_feed_units']['edges']:
        try:
            edge = __parsing_edge__(edge)
            isUpToTime = Auxiliary.dateCompare(edge["creation_time"])
            if isUpToTime : 
                edge_list.append(edge)
        except Exception as e:
            print(traceback.format_exc())
            continue
    cursor = ""
    if isUpToTime:
        cursor = edge_list[-1]["cursor"] # DANGEROUS
    return edge_list, cursor,isUpToTime

def __parsing_Feedback__(resp,posts_count):
    edge_list = []
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    check = resp['data']['node']['reshares']['edges']
    if len(check) == 0:
        return [],""
        
    for edge in resp['data']['node']['reshares']['edges']:
        try:
            edge = parsing_edges_feedback(edge,posts_count)
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


def Crawl_PagePosts(pageurl):

    tryCount = 0
    proxyCount = int(os.environ.get("proxy_list_number","0"))
    proxyIPList = proxy.getProxyListFromJson()
    randomProxyIP ="http://" + proxyIPList[proxyCount]
    contents = []
    cursor = ''
    headers = __get_cookieid__(pageurl)
    # Get pageid, postid and reqname

    jsonArrayData = reader.readInputJson()
    accountsLen = len(jsonArrayData['user']['account'])
    
    for accountNumber in range(0,accountsLen):
        pageid, docid, req_name = __get_pageid__(pageurl=pageurl,accountNumber=accountNumber)
        if docid != "":
            break
        else:
            print("未能取得文章的docid,嘗試換其他帳號試試")
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
        print(f"當前的標記 : {cursor}")
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
                edge_list, cursor_now,isUpToTime = __parsing_ProfileComet__(resp)
            elif req_name == 'CometModernPageFeedPaginationQuery':
                edge_list, cursor_now,isUpToTime = __parsing_CometModern__(resp)

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
            if isUpToTime == False :
                return contents
                
        except UnboundLocalError:
            print("Reached the last page")
            break

        except Exception as e:
            print("Failed reason : " ,str(e))
            print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"pageid: {pageid}, docid: {docid}, cursor: {cursor}")

            # Get New cookie ID
            # headers = __get_cookieid__(pageurl)
            proxyCount+=1
            os.environ["proxy_list_number"] = str(proxyCount)
            if proxyCount >= len(proxyIPList):
                if tryCount>=5:
                    print(f"failed to catch posts after {tryCount} times trying...")
                    os.environ["proxy_list_number"] = "0"
                    return contents
                print("all proxy are down ! please refresh the proxyList")
                proxy.gRequestsProxyList()
                proxyIPList = proxy.getProxyListFromJson()
                proxyCount = 0
                os.environ["proxy_list_number"] = str(proxyCount)
                tryCount+=1
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
            else:
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
    session.close()
    return contents



def Crawl_PageFeedback(pageurl,feedback_id,docid,posts_count):
    
    tryCount = 0
    proxyCount = int(os.environ.get("proxy_list_number","0"))
    proxyIPList = proxy.getProxyListFromJson()
    randomProxyIP ="http://" + proxyIPList[proxyCount]
    contents = []
    cursor = ''
    headers = __get_cookieid__(pageurl)
    # Get postid and reqname
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
        print(f"當前的標記 : {cursor}")
        data = {'variables': str({
                                    "cursor": cursor,
                                    'id': feedback_id,
                                    "privacySelectorRenderLocation":"COMET_STREAM",
                                    "scale":"1",
                                    "__relay_internal__pv__FBReelsEnableDeferrelayprovider":"false"
                                    }),
                    'doc_id': docid}
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
            print(f"Failed reason : {str(e)}, feedback_id : {feedback_id}, post_id : {posts_count}" )
            print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"post_id: {posts_count},feedback_id : {feedback_id}, docid: {docid}, cursor: {cursor}")

            # Get New cookie ID
            # headers = __get_cookieid__(pageurl)
            proxyCount+=1
            os.environ["proxy_list_number"] = str(proxyCount)
            if proxyCount >= len(proxyIPList):
                if tryCount>=5:
                    print(f"Posts {posts_count} failed to catch feedback after {tryCount} times trying...")
                    os.environ["proxy_list_number"] = "0"
                    return contents
                print("all proxy are down ! please refresh the proxyList")
                proxy.gRequestsProxyList()
                proxyIPList = proxy.getProxyListFromJson()
                proxyCount = 0
                os.environ["proxy_list_number"] = str(proxyCount)
                tryCount+=1
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
            else:
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
    session.close()
    return contents


def Crawl_Section_About(pageurl,fb_dtsg,cookieStr):
    tryCount = 0
    proxyCount = int(os.environ.get("proxy_list_number","0"))
    proxyIPList = proxy.getProxyListFromJson()
    randomProxyIP ="http://" + proxyIPList[proxyCount]
    contents = []
    collectionTokenList = []
    
    headers = __get_cookieid__(pageurl)
    # headers['cookie'] += cookieStr

    # Get pageid, postid and reqname

    jsonArrayData = reader.readInputJson()
    accountsLen = len(jsonArrayData['user']['account'])
    
    for accountNumber in range(0,accountsLen):
        userid, docid, req_name = __get_userid_section__(pageurl,accountNumber)
        if docid != "":
            break
        else:
            print("未能取得關於的docid,嘗試換其他帳號試試")
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

    print("開始抓取個人的關於資料")
    # first call
    # collectionToken 不帶表示抓總覽
    #  "collectionToken":'YXBwX2NvbGxlY3Rpb246MTAwMDAyMzI4ODM0NjM4OjIzMjcxNTgyMjc6MjA0',
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
    resp = session.post(url='https://www.facebook.com/api/graphql/',
                            data=data,
                            headers=headers,timeout=20,verify="./config/certs.pem")
    if req_name == 'ProfileCometAboutAppSectionQuery':
        edge_list = __parsing_SectionAbout__(resp,0)
    
    contents = contents + edge_list
    collectionTokenList = edge_list[0]['id_output']
    collectIDCount = 1
    resp.close()
    while True:
        print(collectIDCount)
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
            time.sleep(random.randint(1,2))


        except Exception as e:
            print("Failed reason : " ,str(e))
            print("ERROR Occured !!! changing proxy...")
            if (not isinstance(e,TimeoutError)) and (not isinstance(e,KeyError)) and (not isinstance(e,ConnectTimeoutError)) and (not isinstance(e,MaxRetryError)) and (not isinstance(e,ConnectionResetError)) and (not isinstance(e,ProxyError)) and (not isinstance(e,ConnectTimeout)):
                writer.writeLogToFile(traceBack=traceback.format_exc())
                writer.writeLogToFile(traceBack=f"userid: {userid}, docid: {docid}, collectionToken: {collectionTokenList[collectIDCount]}")

            # Get New cookie ID
            # headers = __get_cookieid__(pageurl)
            # headers['cookie'] += cookieStr
            proxyCount+=1
            os.environ["proxy_list_number"] = str(proxyCount)
            if proxyCount >= len(proxyIPList):
                if tryCount>=5:
                    print(f"failed to catch SectionAbout after {tryCount} times trying...")
                    os.environ["proxy_list_number"] = "0"
                    return contents
                print("all proxy are down ! please refresh the proxyList")
                proxy.gRequestsProxyList()
                proxyIPList = proxy.getProxyListFromJson()
                proxyCount = 0
                os.environ["proxy_list_number"] = str(proxyCount)
                tryCount+=1
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
            else:
                randomProxyIP ="http://" + proxyIPList[proxyCount]
                continue
    session.close()
    return contents