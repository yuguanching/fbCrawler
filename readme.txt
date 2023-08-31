# 於config 裡面的input.json設定要跑的粉專名稱與網址,並設定要用於登入的帳密



 # 相關粉專紀錄頁:https://docs.google.com/spreadsheets/d/10vkb3jl42d8E3_qiHI9tSaRNi6tuamb-W0IKr4SRY1w/edit?pli=1#gid=0



指令與功能指引
# python main.py : 執行主程式,批次產生目標粉專們的文章資料、分享統計資料

# python proxy.py : 主動抓取刷新一次proxyList.json裡的可用proxy清單

# python sharerRandom.py : 在目標粉專都已產生dataParse.xlsx的前提下執行,產生sharer的分群資料

# python mergeAll.py : 在目標粉專都已產生dataParse.xlsx、tag.xlsx的前提下執行,產生所有粉專聚合的統計資料 allDataParse、allTag、文字雲

# python buildIndexCatalog.py : 產生目標粉專的目錄檔案 index.xlsx

# python personProfile.py : 針對個人頁面產生文章統計資料(不含分享者相關資料),一樣吃input.json,特性:文章內容若為空的資料則濾掉不紀錄在excel中
p.s : input.json 的searchDate ,會提供一個日期限制,久於該日期之後的文章則不蒐集(預設為1970-01-01 , 代表全蒐集)

一、跑粉專跟其分享者

1、inputjson設定跑main.py

2、mergeAllDataParse.py

二、跑個人頁面+朋友群資料

1、inputjson設定跑personProfile.py

2、mergeAllAboutData.py

3、mergeAllFriendData.py



筆記與踩坑

# multiProcess的應用中,各程序之間不會共用os.environ

# 抓取"文章"的功能中,cursor在抓取到某個時間點之後的文章皆存在過期現象,過期後的cursor有可能直接指向終點或是某一篇特定的文章