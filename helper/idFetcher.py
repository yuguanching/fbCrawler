import requests
import re
import random
import os
import configSetting

from typing import Union
from bs4 import BeautifulSoup
from webManager import webDriver
from ioService import writer, reader


def fetchEigenvaluesAndID(func, customDriver: configSetting.allDriverType, pageURL, errString, checkOption=2) -> Union[tuple[str, str, str, bool], tuple[str, str, str, str, str, bool]]:
    # checkOption-> 0: 只檢查id , 1:只檢查docid , 2: 兩個都檢查(預設值為2)
    accounts_len = len(configSetting.json_array_data['user']['account'])
    account_num = os.environ.get("account_number_now")
    id = ""
    docid = ""
    req_name = ""
    comment_docid = ""
    comment_req_name = ""
    if account_num is None:
        account_num = random.randint(0, accounts_len-1)
    else:
        account_num = int(account_num)

    # 先檢查登入狀態,若未登入則先完成首次登入
    # 下方的判斷中,只要發現有取不到必要資料的情形,則捨棄當前的driver實體,重新創立一個並重新登入
    if customDriver.isLogin:
        pass
    else:
        customDriver.login(account_num)
        customDriver.isLogin = True

    while True:
        if isinstance(customDriver, webDriver.feedbackDriver):
            id, docid, req_name, comment_docid, comment_req_name, is_been_banned = func(pageURL=pageURL, customDriver=customDriver)
        else:
            id, docid, req_name, is_been_banned = func(pageURL=pageURL, customDriver=customDriver)

        # 若發現該頁面被臉書封鎖,則直接回傳空值與標記,由外部判斷處理
        if is_been_banned:
            break

        match checkOption:
            case 0:
                if id != "":
                    os.environ['account_number_now'] = str(account_num)
                    break
                else:
                    print(errString)
                    account_num += 1
                    if account_num == accounts_len:
                        account_num = 0
                    os.environ['account_number_now'] = str(account_num)
                    customDriver.clearDriver()
                    customDriver.driverInitialize()
                    customDriver.login(account_num)
                    customDriver.isLogin = True
                    continue
            case 1:
                if docid != "":
                    os.environ['account_number_now'] = str(account_num)
                    break
                else:
                    print(errString)
                    account_num += 1
                    if account_num == accounts_len:
                        account_num = 0
                    os.environ['account_number_now'] = str(account_num)
                    customDriver.clearDriver()
                    customDriver.driverInitialize()
                    customDriver.login(account_num)
                    customDriver.isLogin = True
                    continue
            case 2:
                if docid != "" and id != "":
                    os.environ['account_number_now'] = str(account_num)
                    break
                else:
                    print(errString)
                    account_num += 1
                    if account_num == accounts_len:
                        account_num = 0
                    os.environ['account_number_now'] = str(account_num)
                    customDriver.clearDriver()
                    customDriver.driverInitialize()
                    customDriver.login(account_num)
                    customDriver.isLogin = True
                    continue
    if isinstance(customDriver, webDriver.feedbackDriver):
        return id, docid, req_name, comment_docid, comment_req_name, is_been_banned
    else:
        return id, docid, req_name, is_been_banned


def __getFriendzoneNovSection__(pageURL, customDriver: webDriver.friendzoneDriver) -> tuple[str, str, str, bool]:

    print("以selenium的爬蟲登入法取得friendzone docid")
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

    if len(re.findall('"tab_key":"friends_all","id":"(.*?)"', resp)) >= 1:
        friendzone_id = re.findall('"tab_key":"friends_all","id":"(.*?)"', resp)[0]
    else:
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


def __getGroupMemberSection__(pageURL, customDriver: webDriver.groupMemberDriver) -> tuple[str, str, str, bool]:

    print("以selenium的爬蟲登入法取得社團成員資料 docid")
    is_been_banned = False
    # userid = ''
    resp = customDriver._getSource(pageURL=pageURL)
    if resp == "":
        return "", "", "", is_been_banned

    if ("目前無法查看此內容" in resp) and ("empty_states_icons" in resp):
        is_been_banned = True
        return "", "", "", is_been_banned

    writer.writeTempFile(filename="sourceCode_group", content=resp)
    # writer.writeTempFile(filename="sourceCode_friendzone",content=resp)

    # # userID
    # if len(re.findall('"userID":"([0-9]{1,})",', resp)) >= 1:
    #     userid = re.findall('"userID":"([0-9]{1,})",', resp)[0]
    # else:
    #     userid = ''

    if len(re.findall('content="fb://group/(.*?)"', resp)) >= 1:
        group_id = re.findall('content="fb://group/(.*?)"', resp)[0]
    else:
        group_id = ''

    # section docid
    soup = BeautifulSoup(resp, 'lxml')
    docid = ""
    req_name = ""

    for js in soup.findAll('link', {'rel': 'preload'}):
        resp_href = requests.get(js['href'])
        for line in resp_href.text.split('\n', -1):
            if 'GroupsCometMembersPageNewForumMembersSectionRefetchQuery_' in line:
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'GroupsCometMembersPageNewForumMembersSectionRefetchQuery'
                break
    # print('userid is: {}'.format(userid))
    print('groupid is: {}'.format(group_id))
    print('docid is: {}'.format(docid))
    print(f"req_name is: {req_name}")
    return group_id, docid, req_name, is_been_banned


def __getUserIDSection__(pageURL, customDriver: webDriver.postsDriver):

    print("以selenium的爬蟲登入法取得userid、about的docid")
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


def __getDocIDFeedback__(pageURL, customDriver: webDriver.feedbackDriver) -> tuple[str, str, str, str, str, bool]:

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
    comment_docid = ""
    comment_req_name = ""
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
            else:
                continue

        # 抓留言用的docid
        for line in resp.text.split('\n', -1):
            if 'CometFocusedStoryViewUFIQuery_' in line:
                comment_ans_list = re.findall('e.exports="([0-9]{1,})"', line)
                if len(comment_ans_list) > 0:
                    comment_docid = comment_ans_list[0]
                    comment_req_name = 'CometFocusedStoryViewUFIQuery'
                    break

        resp.close()
        if req_name == "CometResharesFeedPaginationQuery" and comment_req_name == "CometFocusedStoryViewUFIQuery":
            break
    print(f'feedback docid is: {docid}, req_name is: {req_name}')
    print(f'comment docid is: {comment_docid}, req_name is: {comment_req_name}')
    return "", docid, req_name, comment_docid, comment_req_name, is_been_banned


def __getPageID__(pageURL, customDriver: webDriver.postsDriver) -> tuple[str, str, str, bool]:

    pageid = ''
    is_been_banned = False
    pageURL = re.sub('/$', '', pageURL)

    resp = requests.get(pageURL)
    resp = resp.text
    # *部分粉專有鎖年齡與國家,導致只能登入後才能瀏覽,故改用爬蟲登入法取得頁面資料
    if "pageID" not in resp:
        print("以selenium的爬蟲登入法取得pageid、post的docid")
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
                if len(re.findall('"userID":"(.*?)"', resp)) >= 1:
                    pageid = re.findall('"userID":"(.*?)"', resp)[0]
                break

            if 'CometModernPageFeedPaginationQuery_' in line and docid == "":
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


def __getGroupPageID__(pageURL, customDriver: webDriver.postsDriver) -> tuple[str, str, str, bool]:

    groupid = ''
    is_been_banned = False
    pageURL = re.sub('/$', '', pageURL)

    resp = requests.get(pageURL)
    resp = resp.text
    # *部分粉專有鎖年齡與國家,導致只能登入後才能瀏覽,故改用爬蟲登入法取得頁面資料
    if "pageID" not in resp:
        print("以selenium的爬蟲登入法取得pageid、post的docid")
        resp = customDriver._getSource(pageURL=pageURL)
    writer.writeTempFile(filename="groupSourceCode", content=resp)
    if ("目前無法查看此內容" in resp) and ("empty_states_icons" in resp):
        is_been_banned = True
        return "", "", "", is_been_banned

    # group_id
    if len(re.findall('content="fb://group/(.*?)"', resp)) >= 1:
        groupid = re.findall('content="fb://group/(.*?)"', resp)[0]
    else:
        groupid = ''

    # postid
    soup = BeautifulSoup(resp, 'lxml')
    docid = ""
    req_name = ""
    for js in soup.findAll('link', {'rel': 'preload'}):
        resp_href = requests.get(js['href'])
        for line in resp_href.text.split('\n', -1):
            if 'GroupsCometFeedRegularStoriesPaginationQuery_facebookRelayOperation' in line:
                docid = re.findall('e.exports="([0-9]{1,})"', line)[0]
                req_name = 'GroupsCometFeedRegularStoriesPaginationQuery'
                break
        resp_href.close()

    print('groupid is: {}'.format(groupid))
    print('docid is: {}'.format(docid))
    print(f"req_name is: {req_name}")
    return groupid, docid, req_name, is_been_banned
