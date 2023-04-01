from inspect import Traceback
from tempfile import tempdir
from queue import Queue
import grequests
import requests
import re
import json
import traceback

from helper import proxy, Auxiliary, rawDataResolve
from ioService import writer, reader


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


def __parsingGroupMember__(resp: requests.Response) -> tuple[list, str]:
    edge_list = []
    writer.writeTempFile(filename="sourceCode_group_member_edge", content=resp.text)
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    temp_cursor = ""

    for edge in resp['data']['node']['new_forum_members']['edges']:
        try:
            edge = rawDataResolve.__resolverEdgesGroupMember__(edge)
            temp_cursor = edge["cursor"]
            edge_list.append(edge)
        except Exception as e:
            print(traceback.format_exc())
            continue
    temp_cursor = resp['data']['node']['new_forum_members']['page_info']['end_cursor']
    cursor = temp_cursor
    return edge_list, cursor


def __parsingSectionAbout__(resp: requests.Response, aboutNumber) -> list:
    edge_list = []
    resps = resp.text.split('\r\n', -1)
    # writer.writeTempFile(filename="sourceCode_section_edge",content=resp.text)

    for i, res in enumerate(resps):
        try:
            check = json.loads(res)['data']['user']['about_app_sections']['nodes']
            res_dict = rawDataResolve.__resolverEdgesSectionAbout__(check[0], aboutNumber=aboutNumber)
            edge_list.append(res_dict)
        except Exception as e:
            continue
    if len(edge_list) == 0:
        raise UnboundLocalError("沒有取到關於的內容,重試")
    return edge_list


def __parsingProfileComet__(resp: requests.Response) -> tuple[list, str, bool, bool, str]:
    edge_list = []
    resps = resp.text.split('\r\n', -1)
    temp_cursor = ""
    temp_time = ""
    is_up_to_time = True
    arrive_first_catch_time = False
    # 2023/03/28 針對第二型粉專回傳資料抓取的改良
    page_info_obj = dict()

    for i, res in enumerate(resps):
        check = json.loads(res)['data']
        if 'node' in check:
            # 第一種回傳物件
            if 'timeline_list_feed_units' in check['node']:
                if len(check['node']['timeline_list_feed_units']['edges']) != 0:
                    for edge in check['node']['timeline_list_feed_units']['edges']:
                        try:
                            edge = rawDataResolve.__resolverEdgesPage__(edge)
                            temp_cursor = edge["cursor"]
                            if edge["creation_time"] != 0:
                                is_up_to_time, arrive_first_catch_time, temp_time = Auxiliary.dateCompare(edge["creation_time"])
                                if is_up_to_time:
                                    edge_list.append(edge)
                        except Exception as e:
                            print(traceback.format_exc())
                            continue
            else:  # 第二種回傳物件
                edge = check
                try:
                    edge = rawDataResolve.__resolverEdgesPage__(edge)
                    temp_cursor = edge["cursor"]
                    if edge["creation_time"] != 0:
                        is_up_to_time, arrive_first_catch_time, temp_time = Auxiliary.dateCompare(edge["creation_time"])
                        if is_up_to_time:
                            edge_list.append(edge)
                except Exception as e:
                    print(traceback.format_exc())
                    continue
        # 第三種回傳物件
        elif 'page_info' in check:
            page_info_obj = check
            continue
        # 無意義物件
        else:
            continue
    # 取下一次的cursor
    # try:
    #     cursor = page_info_obj['page_info']['end_cursor']
    # except:
    cursor = temp_cursor
    time_now = temp_time
    return edge_list, cursor, is_up_to_time, arrive_first_catch_time, time_now, page_info_obj


def __parsingCometModern__(resp: requests.Response) -> tuple[list, str, bool, bool, str]:
    edge_list = []
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    temp_cursor = ""
    temp_time = ""
    is_up_to_time = True
    arrive_first_catch_time = False
    for edge in resp['data']['node']['timeline_feed_units']['edges']:
        try:
            edge = rawDataResolve.__resolverEdgesPage__(edge)
            temp_cursor = edge["cursor"]
            is_up_to_time, arrive_first_catch_time, temp_time = Auxiliary.dateCompare(edge["creation_time"])
            if is_up_to_time:
                edge_list.append(edge)
        except Exception as e:
            print(traceback.format_exc())
            continue
    cursor = temp_cursor
    if resp['data']['node']['timeline_feed_units']['page_info']['end_cursor'] != None and resp['data']['node']['timeline_feed_units']['page_info']['end_cursor'] != "":
        end_cursor = resp['data']['node']['timeline_feed_units']['page_info']['end_cursor']
        cursor = end_cursor
    time_now = temp_time
    return edge_list, cursor, is_up_to_time, arrive_first_catch_time, time_now


def __parsingGroupPosts__(resp: requests.Response) -> tuple[list, str, bool, bool, str]:
    edge_list = []
    writer.writeTempFile(filename="sourceCode_group_posts_edge", content=resp.text)
    resps = resp.text.split('\n', -1)
    temp_cursor = ""
    temp_time = ""
    is_up_to_time = True
    arrive_first_catch_time = False
    for i, res in enumerate(resps):
        check = json.loads(res)['data']
        try:
            if len(check['node']['group_feed']['edges']) == 0:
                return [], "", is_up_to_time, arrive_first_catch_time
            else:
                for edge in check['node']['group_feed']['edges']:
                    try:
                        # group post的cursor 若為空,第一筆資料的格式和其他不同,若遇到特徵,則只更新下一個cursor而不抓資料
                        if edge['node']['__typename'] == "GroupsSectionHeaderUnit":
                            temp_cursor = edge["cursor"]
                            break

                        edge = rawDataResolve.__resolverEdgesPage__(edge)
                        temp_cursor = edge["cursor"]
                        if edge["creation_time"] != 0:
                            is_up_to_time, arrive_first_catch_time, temp_time = Auxiliary.dateCompare(edge["creation_time"])
                            if is_up_to_time:
                                edge_list.append(edge)
                    except Exception as e:
                        print(traceback.format_exc())
                        continue
        except:
            # print(traceback.format_exc())
            # print("other label data, abort")
            continue
    cursor = temp_cursor
    time_now = temp_time
    return edge_list, cursor, is_up_to_time, arrive_first_catch_time, time_now


def __parsingFeedback__(resp: requests.Response, posts_count) -> tuple[list, str]:
    edge_list = []
    resps = json.loads(resp.text.split('\r\n', -1)[0])
    temp_cursor = ""

    # 該篇文章還沒有任何分享者,直接視作抓完資料跳出
    check = resps['data']['node']['reshares']['edges']
    if len(check) == 0:
        return [], ""

    for edge in resps['data']['node']['reshares']['edges']:
        try:
            edge = rawDataResolve.__resolverEdgesFeedback__(edge, posts_count)
            temp_cursor = edge["cursor"]
            edge_list.append(edge)
        except Exception as e:
            writer.writeLogToFile(resp.text)
            print(traceback.format_exc())
            continue
    try:
        cursor = resps['data']['node']['reshares']['page_info']['end_cursor']
    except:
        cursor = temp_cursor

    return edge_list, cursor


def hasNextPage_CometModern(resp: requests.Response) -> bool:
    resp = json.loads(resp.text.split('\r\n', -1)[0])

    if 'timeline_feed_units' in resp['data']['node']:
        has_next_page = resp['data']['node']['timeline_feed_units']['page_info']['has_next_page']
    return has_next_page


def hasNextPage_ProfileComet(page_info_obj: dict) -> bool:
    has_next_page = page_info_obj['page_info']['has_next_page']
    return has_next_page


def hasNextPageGroupPost(resp: requests.Response) -> bool:
    resp = json.loads(resp.text.split('\r\n', -1)[0])

    if len(resp['data']['node']['group_feed']['edges']) == 0:
        return False
    else:
        return True


def hasNextPageFeedback(resp: requests.Response) -> bool:
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    if resp['data']['node']['reshares']:
        has_next_page = resp['data']['node']['reshares']['page_info']['has_next_page']

    return has_next_page


def hasNextPageFriendzone(resp: requests.Response) -> bool:
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    if 'pageItems' in resp['data']['node']:
        has_next_page = resp['data']['node']['pageItems']['page_info']['has_next_page']
    else:
        has_next_page = False

    return has_next_page


def hasNextPageGroupMember(resp: requests.Response) -> bool:
    resp = json.loads(resp.text.split('\r\n', -1)[0])
    has_next_page = resp['data']['node']['new_forum_members']['page_info']['has_next_page']

    return has_next_page
