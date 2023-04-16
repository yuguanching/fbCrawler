import os

from ioService import reader
from webManager import webDriver
from typing import Union

# ---------- input settings ----------
# 輸入資料與客製相關設定檔
json_array_data = reader.readInputJson()
feedback_manual = False
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
retry = 1
retry_feedback = 5

# 連線出現延遲時的等待時間
timeout = 10
timeout_feedback = 60

# 冷卻時間:是否可以關閉proxy使用一次本機公網ip呼叫(單位是秒)
cooldown_timedelta = 30
# 發生任何例外錯誤的容忍次數(使用一次本機公網IP後會重新計數)
exception_max_try = 2
# ---------- connections settings ----------


# ---------- webDriver settings ----------
# 爬蟲相關行為使用的瀏覽器是否要在背景執行
need_headless = True

# 分享行為截圖要截前幾名
screenshot_count = 3

# 隱式等待時間
implicitly_wait = 20

# 所有類型的webDriver type
allDriverType = Union[webDriver.postsDriver, webDriver.feedbackDriver, webDriver.friendzoneDriver, webDriver.groupMemberDriver]
# ---------- webDriver settings ----------


# ---------- proxy settings ----------
# 抓取proxy ip 時取回的數量, 限制抓取一定數量的可用proxy
valid_proxy_ip_len = 7

# 抓回來使用的prxoy_ip_list 全部失效後的重試次數
proxy_try_count = 30
# ---------- proxy settings ----------
