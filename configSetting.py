
from ioService import reader

import os

# ---------- input settings ----------
# 輸入資料與客製相關設定檔
jsonArrayData = reader.readInputJson()
# ---------- input settings ----------


# ---------- tasks settings ----------
# 根據輸入資料的多寡決定執行程序的個數
input_data_num = len(jsonArrayData['targetName'])
process_worker = 1
if input_data_num >= 1 and input_data_num <= 8:
    process_worker = input_data_num
elif input_data_num >= 9 and input_data_num <= 200:
    process_worker = 8
else:
    process_worker = os.cpu_count()

# 多執行緒任務中統計進行中數量時每隔多少進行一次顯示
queue_show_interval = 50
# ---------- tasks settings ----------


# ---------- connections settings ----------
# 發起request若出現異常的重試次數
retry = 3

# 連線出現延遲時的等待時間
timeout = 20
# ---------- connections settings ----------


# ---------- webDriver settings ----------
# 爬蟲相關行為使用的瀏覽器是否要在背景執行
need_headless = True

# 分享行為截圖要截前幾名
screenshot_count = 3

# 隱士等待時間
implicitly_wait = 20
# ---------- webDriver settings ----------


# ---------- proxy settings ----------
# 抓取proxy ip 時取回的數量, 限制抓取一定數量的可用proxy
valid_proxy_ip_len = 7

# 抓回來使用的prxoy_ip_list 全部失效後的重試次數
proxy_try_count = 1000
# ---------- proxy settings ----------
