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
import re
import os
import json


# # helper.__get_userid_section__("https://www.facebook.com/andy.chang.184881")


# params = getFbCSRFToken.get_csrf_token()

# # fb_dtsg = params['fb_dtsg']

# fb_dtsg = "NAcOWjrI7grx6XHQjRmrckzp8mlEFAjUO5yvsafsPqZtZlnbN32YvMA:29:1661418907"


# contents = helper.Crawl_Section_About("https://www.facebook.com/profile.php?id=100002328834638",fb_dtsg=fb_dtsg)

# print(contents)
# with open('contents.json', 'w', encoding='utf_8') as f:
#     json.dump(contents, f, ensure_ascii=False, indent=4)

# parser.buildAboutData([],"字浚賢")    
helper.__get_friendzone_nov_section__("https://www.facebook.com/profile.php?id=100063501608985",0)
# res = helper.Crawl_friendzone("https://www.facebook.com/profile.php?id=100014369017560")
# params,cookie_xs,cookie_cUser = getFbCSRFToken.get_csrf_token()
# fb_dtsg = params['fb_dtsg']
# source = helper.Crawl_friendzone_id("https://www.facebook.com/profile.php?id=100014369017560",fb_dtsg,0)
