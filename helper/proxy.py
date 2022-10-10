import re
import json
import os
import grequests
import requests


def getTaiwanFreeProxyList():
    response = requests.get("https://freeproxyupdate.com/taiwan-tw/http",timeout=20)

    proxy_ips = []
    proxy_ip = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', response.text)  
    proxy_port = re.findall('d>\d+<', response.text)
    for ip,port in zip(proxy_ip,proxy_port):
        proxy_ips.append(ip + ":" + port[2:len(port)-1])

    response.close()
    return proxy_ips

def getFreeProxyList():
    response = requests.get("https://www.sslproxies.org/")
    
    proxy_ips = re.findall('\d+\.\d+\.\d+\.\d+:\d+', response.text)  #「\d+」代表數字一個位數以上

    proxy_ips =  getTaiwanFreeProxyList() + proxy_ips
    valid_ips = []
    response.close()

    # 限制抓取一定數量的可用proxy即可
    limit_count = 5
    s = requests.session()
    for ip in proxy_ips:
        try:
            result = s.get('https://ip.seeip.org/jsonip?',
                    proxies={'http': ip, 'https': ip},
                    timeout=5)
            print(result.json())
            valid_ips.append(ip)
            if len(valid_ips)==limit_count:
                break
        except:
            print(f"{ip} invalid 1")
            try:
                result = s.get('https://api.ipify.org?format=json',
                        proxies={'http': ip, 'https': ip},
                        timeout=5)
                print(result.json())
                valid_ips.append(ip)
                if len(valid_ips)==limit_count:
                    break
            except:
                print(f"{ip} invalid 2")

    proxt_dict = {"proxyList" : valid_ips}
    with open('./config/proxyList.json', 'w', encoding='utf_8') as f:
        json.dump(proxt_dict, f, ensure_ascii=False, indent=4)
    s.close()


def getProxyListFromJson():
    target_file = "./config/proxyList.json"
    hasFile  = os.path.isfile(target_file)

    if hasFile is True :
        with open(target_file,encoding='utf_8') as f :
                    jsonArrayData = json.load(f)
                    f.close()
    
    return jsonArrayData['proxyList']



# async def checkIPHealth(session,ip,url):
#     proxy = "http://" + ip
#     # proxies = {'http': ip, 'https': ip}
#     async with session.get(url,proxy=proxy,timeout=5) as resp:
#         res_list = await resp
#         return res_list


def gRequestsProxyList():
    response = requests.get("https://www.sslproxies.org/")
    
    proxy_ips = re.findall('\d+\.\d+\.\d+\.\d+:\d+', response.text)  #「\d+」代表數字一個位數以上
    proxy_ips =  getTaiwanFreeProxyList() + proxy_ips
    print("異步呼叫,蒐集可用的proxy")
    valid_ips = []
    response.close()
    
    req_list1 = [grequests.get('https://ip.seeip.org/jsonip?',proxies={'http': ip, 'https': ip},timeout=5) for ip in proxy_ips]
    req_list2 = [grequests.get('https://api.ipify.org?format=json',proxies={'http': ip, 'https': ip},timeout=5) for ip in proxy_ips]
    res_list1 = grequests.map(req_list1)
    res_list2 = grequests.map(req_list2)

    for res1,res2,ip in zip(res_list1,res_list2,proxy_ips):
        if (not res1 is None) or (not res2 is None):
            valid_ips.append(ip)
        if (not res1 is None):
            res1.close()
        if (not res2 is None):
            res2.close()

    proxt_dict = {"proxyList" : valid_ips}
    with open('./config/proxyList.json', 'w', encoding='utf_8') as f:
        json.dump(proxt_dict, f, ensure_ascii=False, indent=4)

    # timeout = aiohttp.ClientTimeout(total=600)
    # connector = aiohttp.TCPConnector(limit=50)

    # async with aiohttp.ClientSession(timeout=timeout,connector=connector) as session:
    #     tasks1 = []
    #     tasks2 = []
    #     for ip in proxy_ips:
    #         tasks1.append(asyncio.create_task(checkIPHealth(session,ip,'https://ip.seeip.org/jsonip?')))
    #     for ip in proxy_ips:
    #         tasks2.append(asyncio.create_task(checkIPHealth(session,ip,'https://api.ipify.org?format=json')))
    #     res_list1 = await asyncio.gather(*tasks1)
    #     res_list2 = await asyncio.gather(*tasks2)

    #     for res1,res2,ip in zip(res_list1,res_list2,proxy_ips):
    #         if (not res1 is None) or (not res2 is None):
    #             valid_ips.append(ip)
    #         if (not res1 is None):
    #             res1.close()
    #         if (not res2 is None):
    #             res2.close()

    # proxt_dict = {"proxyList" : valid_ips}
    # with open('proxyList.json', 'w', encoding='utf_8') as f:
    #     json.dump(proxt_dict, f, ensure_ascii=False, indent=4)