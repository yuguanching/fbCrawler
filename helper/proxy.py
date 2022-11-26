import gevent
import re
import json
import os
import grequests
import requests
import time

def getTaiwanFreeProxyList() -> list:
    proxy_ips = []
    try:
        response = requests.get("https://freeproxyupdate.com/taiwan-tw/http", timeout=20)
        proxy_ip = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', response.text)  
        proxy_port = re.findall('d>\d+<', response.text)
        response.close()
        for ip, port in zip(proxy_ip, proxy_port):
            proxy_ips.append(ip + ":" + port[2:len(port)-1])
    except :
        print("tw的IP抓取失敗,直接捨棄結果")

    return proxy_ips

# 單線舊版,測試檢查用
def getFreeProxyList() -> dict:
    response = requests.get("https://www.google-proxy.net/")
    
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
    return proxt_dict


# def getProxyListFromJson():
#     proxy_list = json.loads(os.environ['proxy_list'])

#     # target_file = "./config/proxyList.json"
#     # hasFile  = os.path.isfile(target_file)

#     # if hasFile is True :
#     #     with open(target_file,encoding='utf_8') as f :
#     #                 jsonArrayData = json.load(f)
#     #                 f.close()
    
#     return proxy_list



# async def checkIPHealth(session,ip,url):
#     proxy = "http://" + ip
#     # proxies = {'http': ip, 'https': ip}
#     async with session.get(url,proxy=proxy,timeout=5) as resp:
#         res_list = await resp
#         return res_list


def gRequestsProxyList(processNum=None) -> list:
    valid_ips = []
    proxy_ips = []
    while True:
        try:
            response_ssl = requests.get("https://www.sslproxies.org/")
            response_anonymous = requests.get("https://free-proxy-list.net/anonymous-proxy.html")
            response_free = requests.get("https://free-proxy-list.net/")
        
            proxy_ips = proxy_ips +  re.findall('\d+\.\d+\.\d+\.\d+:\d+', response_ssl.text)  #「\d+」代表數字一個位數以上
            proxy_ips = proxy_ips +  re.findall('\d+\.\d+\.\d+\.\d+:\d+', response_anonymous.text)
            proxy_ips = proxy_ips +  re.findall('\d+\.\d+\.\d+\.\d+:\d+', response_free.text)
            proxy_ips =  getTaiwanFreeProxyList() + proxy_ips

            if processNum is None:
                print("異步呼叫,蒐集可用的proxy")
            else:
                print(f"行程{processNum} : 異步呼叫,蒐集可用的proxy")
            response_ssl.close()
            response_anonymous.close()
            response_free.close()

            
            req_list1 = [grequests.get('https://ip.seeip.org/jsonip?',proxies={'http': ip, 'https': ip},timeout=3) for ip in proxy_ips]
            req_list2 = [grequests.get('https://api.ipify.org?format=json',proxies={'http': ip, 'https': ip},timeout=3) for ip in proxy_ips]
            res_list1 = grequests.map(req_list1)
            res_list2 = grequests.map(req_list2)

            for res1, res2, ip in zip(res_list1, res_list2, proxy_ips):
                if (res1 is not None) or (res2 is not None):
                    valid_ips.append(ip)
                if (res1 is not None):
                    res1.close()
                if (res2 is not None):
                    res2.close()

            if len(valid_ips) <=0:
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
    return valid_ips
    
    
    # proxt_dict = {"proxyList" : valid_ips}
    # with open('./config/proxyList.json', 'w', encoding='utf_8') as f:
    #     json.dump(proxt_dict, f, ensure_ascii=False, indent=4)
    
    # ip_list_str = json.dumps(valid_ips)
    # os.environ['proxy_list'] = ip_list_str