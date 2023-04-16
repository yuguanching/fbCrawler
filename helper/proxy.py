import gevent
import re
import json
import os
import grequests
import requests
import time
import configSetting
import base64

from py_mini_racer import MiniRacer
from queue import Queue
from bs4 import BeautifulSoup


def getNovaFreeProxyList() -> list:
    ctx = MiniRacer()
    s = requests.session()
    resp = s.get("https://www.proxynova.com/proxy-server-list/elite-proxies/")
    soup = BeautifulSoup(resp.text, 'html.parser')
    rows = soup.find('table', {'id': 'tbl_proxy_list'}).find('tbody').find_all('tr')
    ip_list = []
    for row in rows:
        row_content = row.find_all('td')
        ip = ""
        for i in range(0, 2):
            if i == 0:
                try:
                    jsStr = "function scriptRunner(){" + \
                        str(row_content[i].find('script').text).replace("document.write", "return ") + "} scriptRunner()"

                    ip = ctx.eval(jsStr)
                except:
                    break
            else:
                port = str(row_content[i].text).strip()
                ip += ":" + port
        if ip != "":
            ip_list.append(ip)

    s.close()
    return ip_list


def getCZFreeProxyList() -> list:

    s = requests.session()
    resp = s.get("http://free-proxy.cz/en/proxylist/country/all/http/uptime/all")
    soup = BeautifulSoup(resp.text, 'html.parser')
    rows = soup.find('table', {'id': 'proxy_list'}).find('tbody').find_all('tr')
    resp.close()
    ip_list = []
    for row in rows:
        row_content = row.find_all('td')
        if len(row_content) <= 1:
            continue
        else:
            ip = ""
            for i in range(0, 2):
                if i == 0:
                    target = str(row_content[i])
                    res = re.findall(r'Base64\.decode\("(.*?)"\)', target)[0]
                    res = base64.b64decode(res).decode('utf-8')
                    ip = res
                else:
                    ip = ip + ":" + row_content[i].text
            ip_list.append(ip)

    s.close()
    return ip_list


def getTaiwanFreeProxyList() -> list:
    proxy_ips = []
    s = requests.session()
    try:
        response = s.get("https://freeproxyupdate.com/taiwan-tw/http", timeout=configSetting.timeout)
        proxy_ip = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', response.text)
        proxy_port = re.findall('d>\d+<', response.text)
        response.close()
        for ip, port in zip(proxy_ip, proxy_port):
            proxy_ips.append(ip + ":" + port[2:len(port)-1])
    except:
        print("tw的IP抓取失敗,直接捨棄結果")

    s.close()
    return proxy_ips

# 單線舊版,測試檢查用


def getFreeProxyList() -> dict:
    response = requests.get("https://www.google-proxy.net/")
    proxy_ips = re.findall('\d+\.\d+\.\d+\.\d+:\d+', response.text)  # 「\d+」代表數字一個位數以上
    proxy_ips = getTaiwanFreeProxyList() + proxy_ips
    valid_ips = []
    response.close()

    # 限制抓取一定數量的可用proxy即可
    limit_count = configSetting.valid_proxy_ip_len
    s = requests.session()
    for ip in proxy_ips:
        try:
            result = s.get('https://ip.seeip.org/jsonip?',
                           proxies={'http': ip, 'https': ip},
                           timeout=3)
            print(result.json())
            valid_ips.append(ip)
            if len(valid_ips) == limit_count:
                break
        except:
            print(f"{ip} invalid 1")
            try:
                result = s.get('https://api.ipify.org?format=json',
                               proxies={'http': ip, 'https': ip},
                               timeout=3)
                print(result.json())
                valid_ips.append(ip)
                if len(valid_ips) == limit_count:
                    break
            except:
                print(f"{ip} invalid 2")

    proxt_dict = {"proxyList": valid_ips}
    with open('./config/proxyList.json', 'w', encoding='utf_8') as f:
        json.dump(proxt_dict, f, ensure_ascii=False, indent=4)
    s.close()
    return proxt_dict

# async def checkIPHealth(session,ip,url):
#     proxy = "http://" + ip
#     # proxies = {'http': ip, 'https': ip}
#     async with session.get(url,proxy=proxy,timeout=5) as resp:
#         res_list = await resp
#         return res_list


def gRequestsProxyList(processNum=None) -> list:
    valid_ips = []
    proxy_ips = []
    s = requests.session()
    while True:
        try:
            if processNum is None:
                print("異步呼叫,蒐集可用的proxy")
            else:
                print(f"行程{processNum} : 異步呼叫,蒐集可用的proxy")

            response_ssl = s.get("https://www.sslproxies.org/")
            response_anonymous = s.get("https://free-proxy-list.net/anonymous-proxy.html")
            response_free = s.get("https://free-proxy-list.net/")

            proxy_ips = getNovaFreeProxyList() + proxy_ips
            proxy_ips = proxy_ips + re.findall('\d+\.\d+\.\d+\.\d+:\d+', response_ssl.text)  # 「\d+」代表數字一個位數以上
            proxy_ips = proxy_ips + re.findall('\d+\.\d+\.\d+\.\d+:\d+', response_anonymous.text)
            proxy_ips = proxy_ips + re.findall('\d+\.\d+\.\d+\.\d+:\d+', response_free.text)
            proxy_ips = getCZFreeProxyList() + proxy_ips
            proxy_ips = getTaiwanFreeProxyList() + proxy_ips

            response_ssl.close()
            response_anonymous.close()
            response_free.close()

            # 濾掉重複的
            proxy_ips_set = set(proxy_ips)
            proxy_ips = list(proxy_ips_set)

            proxy_timeout = 2
            req_list1 = [grequests.get('https://ip4.seeip.org/json', proxies={'http': ip, 'https': ip}, timeout=proxy_timeout) for ip in proxy_ips]
            req_list2 = [grequests.get('https://api.ipify.org?format=json',
                                       proxies={'http': ip, 'https': ip}, timeout=proxy_timeout) for ip in proxy_ips]
            req_list3 = [grequests.get('https://www.facebook.com', proxies={'http': ip, 'https': ip}, timeout=proxy_timeout) for ip in proxy_ips]
            res_list1 = grequests.map(req_list1)
            res_list2 = grequests.map(req_list2)
            req_list3 = grequests.map(req_list3)
            for res1, res2, res3, ip in zip(res_list1, res_list2, req_list3, proxy_ips):
                votes = 0
                if (res1 is not None):
                    votes += 1
                if (res2 is not None):
                    votes += 1
                if (res3 is not None):
                    votes += 2
                if votes >= 2:
                    valid_ips.append(ip)
                if (res1 is not None):
                    res1.close()
                if (res2 is not None):
                    res2.close()
                if (res3 is not None):
                    res3.close()

            if len(valid_ips) <= 0:
                print(f"行程{processNum} 取proxy發生意外錯誤2,等待後重取")
                valid_ips = []
                proxy_ips = []
                continue
            else:
                break
        except Exception as e:
            print(f"行程{processNum} 取proxy發生意外錯誤1: {str(e)},等待後重取")
            valid_ips = []
            proxy_ips = []
            continue
    s.close()
    return valid_ips


def updateProxyAndStatus(proxyCount, tryCount, ProxyIpList, processNum):

    print(f"行程{processNum}-> all proxy are down ! please refresh the proxyList")
    proxyCount += 1
    if proxyCount >= len(ProxyIpList):
        ProxyIpList = gRequestsProxyList(processNum)
        proxyCount = 0
        tryCount += 1

    return proxyCount, tryCount, ProxyIpList


def updateMultiThreadProxyAndStatus(proxyCount, tryCount, ProxyIpList, processNum, postsCount, dataLength, queueSignal: Queue):

    proxyCount += 1
    if proxyCount >= len(ProxyIpList):
        # 先比較環境變數中的proxyList有沒有更新
        if json.dumps(ProxyIpList) != os.environ['proxy_list']:
            # print(f"行程{process_num} 發現環境變數已更新,直接從環境變數刷新proxyList")
            ProxyIpList = json.loads(os.environ['proxy_list'])
            proxyCount = 0
        else:
            # 尚未有人更新,檢查當前是否有人占用更新proxyList的資格,若可以更新proxyList,執行後刷新環境變數
            if queueSignal.qsize() == 0:
                queueSignal.put(str(processNum))
                ProxyIpList = gRequestsProxyList(processNum)
                ip_list_str = json.dumps(ProxyIpList)
                os.environ['proxy_list'] = ip_list_str
                proxyCount = 0
                tryCount += 1
                queueSignal.get()  # 釋放信號
                print(f"行程{processNum}->文章or用戶編號{postsCount} : proxyList更新完畢, 目前已抓取{dataLength}份資料,已嘗試了{tryCount}次")
            else:
                # 有人占用,就先不更新proxyList, 直接取得當前環境變數中的proxyList來(等於跳空一輪)
                # print(f"行程{process_num} 不更新proxyList,取當前的環境變數")
                ProxyIpList = json.loads(os.environ['proxy_list'])
                proxyCount = 0

    return proxyCount, tryCount, ProxyIpList
