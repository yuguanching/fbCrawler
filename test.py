from helper import proxy, helper,Auxiliary
import json
from datetime import datetime
from ioService import parser,writer
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from seleniumwire import webdriver
from collections import Counter
from ioService import writer,reader
from helper import  Auxiliary
from webManager import webDriver,getFbCSRFToken
from wordcloud import WordCloud
from queue import Queue
from http.client import HTTPConnection

import re
import os
import json
import pprint
import sys
# # helper.__get_userid_section__("https://www.facebook.com/andy.chang.184881")


# params = getFbCSRFToken.get_csrf_token()

# # fb_dtsg = params['fb_dtsg']

# fb_dtsg = "NAcOWjrI7grx6XHQjRmrckzp8mlEFAjUO5yvsafsPqZtZlnbN32YvMA:29:1661418907"


# contents = helper.Crawl_Section_About("https://www.facebook.com/profile.php?id=100002328834638",fb_dtsg=fb_dtsg)

# print(contents)
# with open('contents.json', 'w', encoding='utf_8') as f:
#     json.dump(contents, f, ensure_ascii=False, indent=4)

# parser.buildAboutData([],"字浚賢")    
# helper.__get_friendzone_nov_section__("https://www.facebook.com/profile.php?id=100063501608985",0)
# res = helper.Crawl_friendzone("https://www.facebook.com/profile.php?id=100014369017560")
# params,cookie_xs,cookie_cUser = getFbCSRFToken.get_csrf_token()
# fb_dtsg = params['fb_dtsg']
# source = helper.Crawl_friendzone_id("https://www.facebook.com/profile.php?id=100014369017560",fb_dtsg,0)

# jsonArrayData = reader.readInputJson()
# proxy_ip_list = proxy.gRequestsProxyList()
# friendzoneList = helper.Crawl_friendzone(pageurl="https://www.facebook.com/profile.php?id=100002545204563",jsonArrayData=jsonArrayData,proxy_ip_list=proxy_ip_list,process_num=0)


# lista = ["61.216.156.222:60808", "122.49.208.230:3128", "117.251.103.186:8080", "172.105.184.208:8001", "176.196.250.86:3128", "117.240.53.116:3128", "218.32.248.8:3128", "72.18.134.138:8080", "173.167.76.202:3128", "142.132.170.72:80", "204.185.204.64:8080", "122.49.208.242:3128", "117.251.103.186:8080", "110.34.3.229:3128", "193.122.71.184:3128", "190.95.132.194:999", "4.233.217.137:8888", "204.185.204.64:8080", "122.49.208.242:3128", "133.242.171.216:3128", "117.251.103.186:8080", "122.49.208.230:3128", "46.161.195.107:1981", "110.34.3.229:3128", "5.58.33.187:55507", "115.96.208.124:8080", "3.28.123.171:8080", "179.49.113.230:999", "172.105.184.208:8001", "3.28.118.153:8080", "189.201.153.89:999", "3.28.181.8:8080"]

# stra = '["61.216.156.222:60808", "122.49.208.230:3128", "117.251.103.186:8080", "172.105.184.208:8001", "176.196.250.86:3128", "117.240.53.116:3128", "218.32.248.8:3128", "72.18.134.138:8080", "173.167.76.202:3128", "142.132.170.72:80", "204.185.204.64:8080", "122.49.208.242:3128", "117.251.103.186:8080", "110.34.3.229:3128", "193.122.71.184:3128", "190.95.132.194:999", "4.233.217.137:8888", "204.185.204.64:8080", "122.49.208.242:3128", "133.242.171.216:3128", "117.251.103.186:8080", "122.49.208.230:3128", "46.161.195.107:1981", "110.34.3.229:3128", "5.58.33.187:55507", "115.96.208.124:8080", "3.28.123.171:8080", "179.49.113.230:999", "172.105.184.208:8001", "3.28.118.153:8080", "189.201.153.89:999", "3.28.181.8:8080"]'

# if json.dumps(lista) == stra:
#     print("AA")
# else :
#     print("BB")

aaa = os.environ.get('111')
print(int(aaa))