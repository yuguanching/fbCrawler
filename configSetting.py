import os
import configSetting

from ioService import reader
from webManager import webDriver
from typing import Union
from datetime import datetime
from Adaptor.FacebookSourceAdaptor import FacebookSourceAdaptor


# ---------- input settings ----------
# 輸入資料與客製相關設定檔
json_array_data = reader.readInputJson()
operate_by_loading_db = False
output_root = './output/粉專/'

sp_time = datetime.strptime("2010-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
# ---------- input settings ----------


# ---------- tasks settings ----------
# 根據輸入資料的多寡決定執行程序的個數
input_data_num = len(json_array_data['targetName'])
process_worker = 1
if input_data_num >= 1 and input_data_num <= 8:
    process_worker = input_data_num
elif input_data_num >= 9 and input_data_num <= 200:
    process_worker = 8
else:
    process_worker = os.cpu_count()

# 多執行緒任務中統計進行中數量時每隔多少進行一次顯示
queue_show_interval = 50
multithread_median = 100
multithread_high = 200
# ---------- tasks settings ----------


# ---------- connections settings ----------
# 發起request若出現異常的重試次數
retry = 3
retry_feedback = 5

# 連線出現延遲時的等待時間
timeout = 15
timeout_feedback = 60

# 冷卻時間:是否可以關閉proxy使用一次本機公網ip呼叫(單位是秒)
cooldown_timedelta = 60
# 發生任何例外錯誤的容忍次數(使用一次本機公網IP後會重新計數)
exception_max_try = 100

# ---------- connections settings ----------


# ---------- webDriver settings ----------
# 爬蟲相關行為使用的瀏覽器是否要在背景執行
need_headless = True

# 分享行為截圖要截前幾名
screenshot_count = 3
screenshot_article_count = 10

# 隱式等待時間
implicitly_wait = 20

# 所有類型的webDriver type
allDriverType = Union[webDriver.postsDriver, webDriver.feedbackDriver,
                      webDriver.friendzoneDriver, webDriver.groupMemberDriver]
# ---------- webDriver settings ----------


# ---------- proxy settings ----------
# 抓取proxy ip 時取回的數量, 限制抓取一定數量的可用proxy
valid_proxy_ip_len = 7

# 抓回來使用的prxoy_ip_list 全部失效後的重試次數
proxy_try_count = 30
# ---------- proxy settings ----------


# ---------- db settings ----------

RPA_HOST = os.environ.get("RPA_HOST", "192.168.50.242")
RPA_USER = os.environ.get("RPA_USER", "jerry_yu")
RPA_PWD = os.environ.get("RPA_PWD", "Ni998453!!!")
RPA_DB = os.environ.get("RPA_DB", "facebookData")
RPA_PORT = int(os.environ.get("RPA_PORT", 3306))

db_adapter = FacebookSourceAdaptor()

# ---------- db settings ----------
