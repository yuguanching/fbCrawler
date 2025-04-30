import re
import os
import time
import random
import emoji
import jieba
import traceback
import numpy
import json
import openpyxl
import pandas as pd
import configSetting

from selenium import webdriver
from operator import mod
from PIL import Image
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from collections import Counter
from ioService import writer, reader
from helper import Auxiliary
from webManager import webDriver
from wordcloud import WordCloud
# 關閉web driver的log訊息
os.environ['WDM_LOG_LEVEL'] = '0'


def buildCollectData(rawDataList, subDir, page_id, screenshotDriver: webDriver.screenshotDriver, dropNA=False, is_use_for_group=False) -> tuple[list, list]:

    excel_file = f'{configSetting.output_root}' + subDir + '/collectData.xlsx'
    date = []
    image_url = []
    video_url = []
    like_count = []
    comment_count = []
    share_count = []
    content = []
    urls = []
    post_id = []
    feedback_id = []
    comment_id = []
    poster_url = []
    poster_name = []

    db_data_list = []

    print(f"開始產生{subDir}的文章統計資料")

    # 各內容的抓取位置請參考__resolverEdgesPage__()
    for raw_data in rawDataList:
        # 抓取並處理時間
        format_date = (lambda input_time: time.strftime("%Y-%m-%d %H:%M:%S",
                       time.localtime(int(input_time))))(raw_data["creation_time"])
        date.append(format_date)

        # 抓取文章內容
        content.append(raw_data["message"])

        # 抓取圖片網址
        image_url.append(raw_data["image_url"])

        # 抓取影片網址
        video_url.append(raw_data["video_url"])

        # 抓取按讚數
        like_count.append(raw_data["reaction_count"])

        # 抓取留言數
        comment_count.append(raw_data["comment_count"])

        # 抓取分享數
        share_count.append(raw_data["share_count"])

        # 抓取文章網址
        urls.append(raw_data["url"])

        # 文章id
        post_id.append(str(raw_data["post_id"]))

        # 分享id
        feedback_id.append(raw_data["feedback_id"])

        # 留言id
        comment_id.append(raw_data["story_id"])

        # 發文者姓名
        poster_name.append(raw_data["poster_name"])

        # 發文者網址
        poster_url.append(raw_data["poster_url"])

        db_data = (str(page_id),
                   str(raw_data["post_id"]),
                   format_date,
                   raw_data["feedback_id"],
                   raw_data["story_id"],
                   raw_data["article_type"],
                   raw_data["message"],
                   int(raw_data["reaction_count"]),
                   int(raw_data["share_count"]),
                   int(raw_data["comment_count"]),
                   raw_data["image_url"],
                   raw_data["video_url"],
                   raw_data["url"])
        db_data_list.append(db_data)

    configSetting.db_adapter.insert_user_article(db_data_list)
    print(f"已插入粉專文章資料")
    time.sleep(5)

    df = pd.DataFrame({
        '時間': date,
        '文章id': post_id,
        '分享id': feedback_id,
        '留言id': comment_id,
        '內容': content,
        '圖片': image_url,
        '按讚數': like_count,
        '留言數': comment_count,
        '分享數': share_count,
        '影片網址': video_url,
        '文章網址': urls,
    })

    usecols = "B:L"
    # 抓取對象是社團而不是粉專的話
    if is_use_for_group:
        df["發文者"] = poster_name
        df["發文者個人網址"] = poster_url
        usecols = "B:N"

    if dropNA:
        df['內容'].replace('', numpy.nan, inplace=True)
        df.dropna(subset=['內容'], inplace=True)
        df.reset_index(drop=True)

    # 實作檢測已存在的舊collectData檔案, 若存在, 進行重複資料的篩選
    # 若有重複, 以新的資料為優先保留
    if os.path.isfile(f"{configSetting.output_root}{subDir}/collectData.xlsx"):
        old_df = pd.read_excel(f"{configSetting.output_root}{subDir}/collectData.xlsx",
                               sheet_name='collection', usecols=usecols, converters={'文章id': str})
        df_new = pd.concat([df, old_df], axis=0, ignore_index=True)
        sorted_df_new = df_new.sort_values(['分享數', '留言數', '按讚數'], ascending=[False, False, False])
        sorted_df_new = sorted_df_new.drop_duplicates(subset=['文章id'], keep='first')
        sorted_df_new['時間'] = pd.to_datetime(sorted_df_new['時間'], format="%Y-%m-%d %H:%M:%S")
        sorted_df_new.sort_values(by='時間', inplace=True, ascending=False)
        sorted_df_new['時間'] = sorted_df_new['時間'].dt.strftime("%Y-%m-%d %H:%M:%S")
        writer.pdToExcel(des=excel_file, df=sorted_df_new, sheetName="collection", autoFitIsNeed=False)
        df = sorted_df_new
    else:
        writer.pdToExcel(des=excel_file, df=df, sheetName="collection", autoFitIsNeed=False)
    print(f"{subDir}的文章統計資料寫入完成")

    #  2023/07/20 額外添加抓取分享數前十的文章截圖
    count = 0
    sorted_df = df.sort_values(['分享數', '按讚數'], ascending=[False, False])
    for s_url, article_id in zip(sorted_df["文章網址"].tolist(), sorted_df["文章id"].tolist()):
        """
        分享行為存在有分享人, 但沒有分享對象的情境,若這種項目數量多到進入前三名
        會影響截圖,故若是遇到,則直接略過,excel那邊則保持這種類型的被分享統計在前三名,作為現象的統計
        """
        if s_url == "":
            continue
        else:
            if count >= configSetting.screenshot_article_count:
                time.sleep(random.randint(1, 2))
                break
            else:
                print("開始文章網址的圖片,id : " + str(count))
                if screenshotDriver._getSource(s_url, count, 2, subDir, article_id):
                    count += 1
                else:
                    continue
    # 最後將分享與留言id回傳給外部使用
    feedback_id_list = df['分享id'].tolist()
    comment_id_list = df['留言id'].tolist()
    article_id_list = df['文章id'].tolist()
    return feedback_id_list, comment_id_list, article_id_list


def extendCommentData(commentDataList, subDir):
    excel_file = f'{configSetting.output_root}' + subDir + '/collectData.xlsx'
    comment_data = []
    comment_posts_count = []

    for articleComments in commentDataList:
        for commentData in articleComments:
            msg = commentData['content']
            comment_posts_count.append(commentData['posts_count'])
            urls = re.findall(
                'http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', msg)
            if len(urls) <= 0:
                comment_data.append("")
            else:
                comment_data.append(urls[0])

    df = pd.DataFrame({
        '編號': comment_posts_count,
        '第三方連結': comment_data
    })
    # 排序用, 用完就刪掉
    df = df.sort_values('編號')
    df.drop('編號', inplace=True, axis=1)
    with pd.ExcelWriter(excel_file, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        df.to_excel(writer,
                    index=False,
                    sheet_name="collection",
                    startcol=12)
    # filename_csv = excel_file.replace(".xlsx", "_" + "collection" + ".csv")
    # csv_df = pd.read_csv(filename_csv)
    # csv_df.insert(loc=8, column="第三方連結", value=df['第三方連結'])
    # csv_df.to_csv(filename_csv, index=False, encoding='utf_8_sig')


def buildDataParse(rawDataList, subDir, pageID, screenshotDriver: webDriver.screenshotDriver) -> None:

    special_chars = r"[!|#|~|,|。|，|？|！|：|;|；|』|『|」|「|“|、|”|】|【|／|\[|\]|?|*|※|］|［]"
    db_data_list = []
    excel_file = f'{configSetting.output_root}' + subDir + '/dataParse.xlsx'
    collect_data_file = f'{configSetting.output_root}' + subDir + '/collectData.xlsx'
    tag_file = f'{configSetting.output_root}' + subDir + '/tag.xlsx'
    posts_id = []
    sharer_name = []
    share_time = []
    sharer_url = []
    sharer_type = []
    sharer_id = []
    been_sharer_name = []
    been_sharer_url = []
    contents = []
    permalinks = []

    # ==================================分享者雜資料統計區============================
    print(f"開始產生 {subDir} 的分享者統計資料")
    if configSetting.operate_by_loading_db is False:
        for article_share_list in rawDataList:
            if len(article_share_list) == 0:
                continue
            else:
                for share_data in article_share_list:

                    # 分享時間
                    format_date = (lambda input_time: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(input_time))))(share_data["create_time"])

                    # 分享者網址和被分享者網址 , 若沒有被分享的目的地,則被分享者網址放空,分享者網址填個人頁面
                    sharerTempURL = share_data["sharer_url"]
                    sharer_temp_name = re.sub(special_chars, "", share_data["sharer_name"])
                    been_sharer_temp_name = ""
                    been_sharer_temp_url = ""
                    if share_data["been_sharer_id"] != "":
                        sharerTempURL = f"https://www.facebook.com/groups/{str(share_data['been_sharer_id'])}/user/{str(share_data['sharer_id'])}/"
                        been_sharer_temp_url = f"https://www.facebook.com/groups/{str(share_data['been_sharer_id'])}/"
                        been_sharer_temp_name = share_data["been_sharer_raw_name"]
                        been_sharer_temp_name = re.sub(special_chars, "", been_sharer_temp_name)

                    db_data = (
                        share_data["share_event_id"],
                        pageID,
                        share_data["article_id"],
                        share_data["feedback_id"],
                        format_date,
                        share_data["sharer_id"],
                        sharer_temp_name,
                        sharerTempURL,
                        share_data["sharer_type"],
                        share_data["contents"],
                        share_data["been_sharer_id"],
                        been_sharer_temp_name,
                        been_sharer_temp_url,
                        share_data["permalink"]
                    )
                    db_data_list.append(db_data)
        configSetting.db_adapter.insert_article_share_data(db_data_list)
        print(f"已插入粉專分享資料")
        time.sleep(5)

    # theDate = configSetting.json_array_data["searchStartDate"]
    # share_data_from_db = configSetting.db_adapter.get_article_share_data_by_certain_article(user_id=pageID, deadline=theDate)
    share_data_from_db = configSetting.db_adapter.get_article_share_data(user_id=pageID)
    print(f"已取得粉專分享資料，共{len(share_data_from_db)}筆")
    time.sleep(5)
    for share_data in share_data_from_db:
        posts_id.append(share_data[0])
        sharer_name.append(share_data[1])
        sharer_id.append(share_data[2])
        share_time.append(str(share_data[3]))
        sharer_url.append(share_data[4])
        sharer_type.append(share_data[5])
        been_sharer_name.append(share_data[6])
        been_sharer_url.append(share_data[7])
        permalinks.append(share_data[8])

    df = pd.DataFrame({
        "所屬文章id": posts_id,
        "分享者名稱": sharer_name,
        "分享者id": sharer_id,
        "分享者類型": sharer_type,
        "發布時間": share_time,
        "分享者網址": sharer_url,
        "被分享者名稱": been_sharer_name,
        "被分享者網址": been_sharer_url,
        "分享單頁連結": permalinks
    })
    df = df.reset_index()  # 重新定義流水號
    df.drop('index', inplace=True, axis=1)
    df.insert(0, "粉專id", str(pageID))
    df.insert(0, "粉專名稱", subDir)
    writer.pdToExcel(des=excel_file, df=df, sheetName="sharerData")
    # ==================================分享者雜資料統計區============================

    # ====================================斷詞處理區=================================
    # 先記錄所有需要斷句斷詞的項目
    article_dict = pd.read_excel(collect_data_file, sheet_name="collection", usecols="F")
    article_contents = article_dict['內容'].dropna().tolist()

    all_contents = contents + article_contents

    tag_raw_df = pd.DataFrame({"未處理斷句": all_contents})
    tag_raw_df = tag_raw_df.reset_index()  # 重新定義流水號
    tag_raw_df.drop('index', inplace=True, axis=1)
    writer.pdToExcel(des=tag_file, df=tag_raw_df, sheetName="rawSentences")
    # 建立熱詞表
    buildTag(subDir)
    # ====================================斷詞處理區=================================

    # **在有sharerData的情況下補救用**
    # df = pd.read_excel(excel_file, sheet_name="sharerData", usecols="B:K")

    # -----------------------產生分享者統整資料,並寫到sheet: sharer --------------------------------------
    sharer = df["分享者名稱"].tolist()
    sharer_counter = Counter(sharer)
    sharer_url = []
    sharer_id = []
    sharer_type = []
    sharer_profile_url = []
    sharer_start_date = []
    sharer_end_date = []

    # 透過雜資料以分享者名稱進行分組, 排序後獲得使用者在此粉專分享足跡的最早與最晚時間
    print("開始進行分享者聚合")
    share_data_group_dict = dict(list(df.groupby("分享者名稱")))
    for name, _ in share_data_group_dict.items():
        share_data_group_dict[name]['發布時間'] = pd.to_datetime(share_data_group_dict[name]['發布時間'], format="%Y-%m-%d %H:%M:%S")
        share_data_group_dict[name].sort_values(by='發布時間', inplace=True)
        share_data_group_dict[name]['發布時間'] = share_data_group_dict[name]['發布時間'].dt.strftime("%Y-%m-%d %H:%M:%S")

    for x in sharer_counter:
        temp = df.loc[df['分享者名稱'] == x, '分享者網址'].iloc[0]
        temp_id = df.loc[df['分享者名稱'] == x, '分享者id'].iloc[0]
        temp_type = df.loc[df['分享者名稱'] == x, '分享者類型'].iloc[0]
        sharer_start_date.append(share_data_group_dict[x]['發布時間'].values[0])
        sharer_end_date.append(share_data_group_dict[x]['發布時間'].values[len(share_data_group_dict[x]['發布時間']) - 1])
        sharer_url.append(temp)
        sharer_profile_url.append(generate_personal_profile_link(temp))
        sharer_id.append(temp_id)
        sharer_type.append(temp_type)
    print("完成分享者聚合")

    sharer_df = pd.DataFrame.from_dict(sharer_counter, orient='index').reset_index()
    sharer_df['分享者id'] = sharer_id
    sharer_df['分享者類型'] = sharer_type
    sharer_df['分享者連結'] = sharer_url
    sharer_df['分享者個人頁面'] = sharer_profile_url
    sharer_df['分享最早時間'] = sharer_start_date
    sharer_df['分享最晚時間'] = sharer_end_date
    try:
        sharer_df = sharer_df.set_axis(['分享者名稱', '分享次數', '分享者id', '分享者類型', '分享者連結', '分享者個人頁面', '分享最早時間', '分享最晚時間'], axis="columns")
    except:
        sharer_df = pd.DataFrame({
            "分享者名稱": [],
            "分享次數": [],
            "分享者id": [],
            "分享者類型": [],
            "分享者連結": [],
            "分享者個人頁面": [],
            "分享最早時間": [],
            "分享最晚時間": [],
        })
    sharer_df = sharer_df.sort_values('分享次數', ascending=False)
    sharer_df = sharer_df.reset_index()
    del sharer_df['index']
    sharer_df.insert(0, "粉專id", pageID)
    sharer_df.insert(0, "粉專名稱", subDir)
    print("完成分享者聚合資料的資料框建置")
    # ------------------------------寫檔到sheet: sharer -------------------------------------
    writer.pdToExcel(des=excel_file, df=sharer_df, sheetName="sharer", mode='a')
    # ----------------------彙整好分享者統計資料後,抓取分享者的個人頁面截圖-------------------------
    # count = 0
    # for s_url in sharer_df["分享者個人頁面"].tolist():
    #     if s_url == "":
    #         continue
    #     else:
    #         if count >= configSetting.screenshot_count:
    #             time.sleep(random.randint(1, 2))
    #             break
    #         else:
    #             print("開始擷取分享者個人頁面的圖片,id : " + str(count))
    #             try:
    #                 if screenshotDriver._getSource(s_url, count, 0, subDir, None):
    #                     count += 1
    #                 else:
    #                     continue
    #             except Exception as e:
    #                 print(f"分享者個人頁面圖片截取失敗, 錯誤訊息:{e}")
    #                 count += 1

    # -----------------------產生被分享者統整資料,並寫到sheet: been_sharer --------------------------------------

    # 已去掉被分享者的nan雜訊
    been_sharer = df["被分享者名稱"].dropna().tolist()
    been_sharer_counter = Counter(been_sharer)
    been_sharer_url = []
    for y in been_sharer_counter:
        # 遇到nan就跳過
        try:
            temp1 = df.loc[df['被分享者名稱'] == y, '被分享者網址'].iloc[0]
            been_sharer_url.append(temp1)
        except:
            continue

    been_sharer_df = pd.DataFrame.from_dict(been_sharer_counter, orient='index').reset_index()
    been_sharer_df['社團/粉專連結'] = been_sharer_url
    try:
        been_sharer_df = been_sharer_df.set_axis(['被分享者', '被分享次數', '社團/粉專連結'], axis="columns")
    except:
        been_sharer_df = pd.DataFrame({
            "被分享者": [],
            "被分享次數": [],
            "社團/粉專連結": []
        })
    been_sharer_df = been_sharer_df.sort_values('被分享次數', ascending=False)
    been_sharer_df = been_sharer_df.reset_index()
    del been_sharer_df['index']
    been_sharer_df.insert(0, "粉專id", pageID)
    been_sharer_df.insert(0, "粉專名稱", subDir)
    print("完成被分享者聚合資料的資料框建置")

    # ------------------------------寫檔到sheet: been_sharer-------------------------------------
    writer.pdToExcel(des=excel_file, df=been_sharer_df, sheetName="been_sharer", mode='a')
    # ---------------------------彙整好被分享者統計資料後,抓取社團/粉專連結頁面截圖-------------------------------

    # count = 0
    # for s_url in been_sharer_df["社團/粉專連結"].tolist():
    #     """
    #     分享行為存在有分享人, 但沒有分享對象的情境,若這種項目數量多到進入前三名
    #     會影響截圖,故若是遇到,則直接略過,excel那邊則保持這種類型的被分享統計在前三名,作為現象的統計
    #     """
    #     if s_url == "":
    #         continue
    #     else:
    #         if count >= configSetting.screenshot_count:
    #             time.sleep(random.randint(1, 2))
    #             break
    #         else:
    #             print("開始擷取社團/粉專連結頁面的圖片,id : " + str(count))
    #             try:
    #                 if screenshotDriver._getSource(s_url, count, 1, subDir):
    #                     count += 1
    #                 else:
    #                     continue
    #             except Exception as e:
    #                 print(f"社團/粉專連結頁面圖片截取失敗, 錯誤訊息:{e}")
    #                 count += 1

    # ------------------------------產生異常帳號彙整表-------------------------------------
    dataparse_file = f"{configSetting.output_root}{subDir}/dataParse.xlsx"
    sharer_df = pd.read_excel(dataparse_file, sheet_name="sharer", usecols="D:K")
    buildAberrantAccountDataSet(sharerDF=sharer_df, subDir=subDir)
    # ------------------------------產生異常帳號彙整表-------------------------------------

    print("批次資料整理完畢")


def buildTag(subDir, forExtraTagMission=False) -> None:
    # 建立一個Counter 物件,準備統計各分享者內容中的tag標籤
    if forExtraTagMission:
        tag_file = f"{subDir}/tag.xlsx"
    else:
        tag_file = f"{configSetting.output_root}{subDir}/tag.xlsx"
    sentence_counter = Counter()
    special_chars = r"[!|#|~|,|。|，|？|！|：|;|；|』|『|」|「|“|、|”|】|【|／|\[|\]|?|*|※|］|［]"
    # 讀取相關的欄位
    data = pd.read_excel(tag_file, sheet_name="rawSentences", usecols="B", converters={"未處理斷句": str})
    raw_tag_list = data["未處理斷句"].dropna().tolist()

    for raw_data in raw_tag_list:
        raw_data = emoji.replace_emoji(raw_data, replace="")
        raw_data = raw_data.replace("～", "")
        raw_data = raw_data.replace("－", "")
        raw_data = raw_data.replace(".", "")
        raw_data = raw_data.replace("…", "")

        temp = re.sub(special_chars, " ", raw_data)
        temp = addSpaceBetweenEmojies(temp)
        temp = temp.strip()
        split_temp = re.split(r'[\s|\r\n]+', temp)
        split_temp = [
            split_str for split_str in split_temp if Auxiliary.detectURL(split_str)]
        sentence_counter.update(split_temp)

    if len(sentence_counter) != 0:
        # 建立儲存tag頻率的xlsx表
        tagList_df = pd.DataFrame.from_dict(
            sentence_counter, orient='index').reset_index()
        tagList_df = tagList_df.set_axis(['斷句', '使用熱度'], axis="columns")
        tagList_df = tagList_df.sort_values('使用熱度', ascending=False)
        writer.pdToExcel(des=tag_file, df=tagList_df, sheetName="sentence",
                         autoFitIsNeed=False, indexIsNeed=False, mode='a')
    else:
        empty_df = pd.DataFrame(columns=['斷句', '使用熱度'])
        writer.pdToExcel(des=tag_file, df=empty_df, sheetName="sentence",
                         autoFitIsNeed=False, indexIsNeed=False, mode='a')

    word_counter = Counter()
    jieba.load_userdict("./config/jieba/dict.txt.big.txt")
    # jieba.load_userdict("./config/jieba/dict_extends.txt")
    with open('./config/jieba/stop_words.txt', encoding="utf_8") as f:
        stop_words = [line.strip() for line in f.readlines()]
    for key in sentence_counter:
        parse_list = jieba.lcut(key, cut_all=False)
        parse_list = [w for w in parse_list if len(
            w) > 1 and not re.match('^[a-z|A-Z|0-9|.]*$', w)]
        parse_list = [w for w in parse_list if w not in stop_words]
        for i in range(1, int(sentence_counter[key] + 1)):
            word_counter.update(parse_list)
    word_list_df = pd.DataFrame.from_dict(
        word_counter, orient='index').reset_index()
    try:
        word_list_df = word_list_df.set_axis(['斷詞', '詞頻'], axis="columns")
    except:
        word_list_df = pd.DataFrame({
            "斷詞": [],
            "詞頻": []
        })
    word_list_df = word_list_df.sort_values('詞頻', ascending=False)
    writer.pdToExcel(des=tag_file, df=word_list_df, sheetName="word",
                     autoFitIsNeed=False, indexIsNeed=False, mode='a')

    print("斷詞表建置完成")
    createWordCloud(subDir=subDir, counter=word_counter,
                    forExtraTagMission=forExtraTagMission)


def addSpaceBetweenEmojies(text) -> str:
    # Ref: https://gist.github.com/Alex-Just/e86110836f3f93fe7932290526529cd1#gistcomment-3208085
    # Ref: https://en.wikipedia.org/wiki/Unicode_block
    EMOJI_PATTERN = re.compile(
        "["
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F700-\U0001F77F"  # alchemical symbols
        u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA00-\U0001FA6F"  # Chess Symbols
        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        u"\U00002702-\U000027B0"  # Dingbats
        u"\u2640-\u2642"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+", flags=re.UNICODE
    )
    text = re.sub(EMOJI_PATTERN, r' ', text)
    return text


def createWordCloud(subDir, counter, forAll=False, forExtraTagMission=False) -> None:

    file_path = f"{configSetting.output_root}{subDir}/img/word_cloud/word_cloud.png"
    report_file_path = f"{configSetting.output_root}{subDir}/img/report/images_10.png"
    if forAll:
        file_path = f"{configSetting.output_root}all_word_cloud.png"
    font_path = f"./config/word_cloud/標楷體.ttc"
    mask_path = f"./config/word_cloud/organza_asstapas.png"
    mask = numpy.array(Image.open(mask_path))
    mask = (mask == 0) * 255

    try:
        print("正在產生wordcloud圖片中...")
        wc = WordCloud(
            background_color="#272727",  # 可配合色碼表
            mode="RGB",
            relative_scaling=0.4,
            scale=1,
            font_path=font_path,
            margin=3,
            max_words=200,
            colormap="Dark2_r",  # supported values are 'Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', 'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r', 'flag', 'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r', 'hsv', 'hsv_r', 'inferno', 'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', 'rainbow_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', 'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'turbo', 'turbo_r', 'twilight', 'twilight_r', 'twilight_shifted', 'twilight_shifted_r', 'viridis', 'viridis_r', 'winter', 'winter_r'
            prefer_horizontal=0.95,
            mask=mask
        )

        wc.generate_from_frequencies(frequencies=counter)
        if forExtraTagMission:
            wc.to_file(f"{subDir}/word_cloud.png")
        else:
            wc.to_file(file_path)
            wc.to_file(report_file_path)
        print("wordcloud圖片產生完成")
    except:
        print("產生wordCloud發生了未知意外,請參考log紀錄")
        writer.writeLogToFile(traceBack=traceback.format_exc())
    finally:
        return


def buildAboutData(AboutDataList, subDir, targetURL) -> None:
    excel_file = f'{configSetting.output_root}' + subDir + '/aboutData.xlsx'

    sheet_adjust_name = subDir.replace(" ", "_")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "about"
    wb.save(excel_file)

    # 0:總覽ID、1:學歷與工作經歷、2:住過的地方、3:聯絡與基本資料、4:家人與感情狀況
    # 需要另外開表的項目:學校與工作經歷 住過的地方 社群資料 社交人際

    # 處理學經歷資料
    experience_dict = AboutDataList[1]
    experience_dict['work']['type'] = ["工作"] * \
        len(experience_dict['work']['name'])
    experience_dict['college']['type'] = ["大專院校"] * \
        len(experience_dict['college']['name'])
    experience_dict['highSchool']['type'] = ["高中"] * \
        len(experience_dict['highSchool']['name'])

    experience_name_list = []
    experience_link_list = []
    experience_date_list = []
    experience_type_list = []

    experience_name_list += (experience_dict['work']['name'])
    experience_name_list += (experience_dict['college']['name'])
    experience_name_list += (experience_dict['highSchool']['name'])

    # 字串處理
    for i in range(0, len(experience_name_list)):
        startIndex = experience_name_list[i].find("at")
        if startIndex == -1:
            startIndex = experience_name_list[i].find("to")
        if startIndex == -1:
            experience_name_list[i] = experience_name_list[i]
        else:
            experience_name_list[i] = experience_name_list[i][startIndex + 3:]

    experience_link_list += (experience_dict['work']['link'])
    experience_link_list += (experience_dict['college']['link'])
    experience_link_list += (experience_dict['highSchool']['link'])

    experience_date_list += (experience_dict['work']['date'])
    experience_date_list += (experience_dict['college']['date'])
    experience_date_list += (experience_dict['highSchool']['date'])

    experience_type_list += (experience_dict['work']['type'])
    experience_type_list += (experience_dict['college']['type'])
    experience_type_list += (experience_dict['highSchool']['type'])

    experienceDF = pd.DataFrame({
        "名稱": experience_name_list,
        "類型": experience_type_list,
        "時間": experience_date_list,
        "連結": experience_link_list
    })

    experience_sheet_name = sheet_adjust_name + "_" + experience_dict['name']

    if len(experience_name_list) != 0:
        writer.pdToExcel(des=excel_file, df=experienceDF,
                         sheetName=experience_sheet_name, mode='a')

    # 處理住過的地方
    live_dict = AboutDataList[2]

    live_name_list = []
    live_link_list = []
    live_type_list = []

    live_name_list += live_dict['live']['name']
    live_link_list += live_dict['live']['link']
    live_type_list += live_dict['live']['type']

    liveDF = pd.DataFrame({
        "名稱": live_name_list,
        "類型": live_type_list,
        "連結": live_link_list
    })

    live_sheet_name = sheet_adjust_name + "_" + live_dict['name']

    if len(live_name_list) != 0:
        writer.pdToExcel(des=excel_file, df=liveDF,
                         sheetName=live_sheet_name, mode='a')

    # 處理人際關係
    relationship_dict = AboutDataList[4]

    relationship_name_list = []
    relationship_link_list = []
    relationship_type_list = []

    relationship_name_list += relationship_dict['relationship']['name']
    relationship_link_list += relationship_dict['relationship']['link']
    relationship_type_list += relationship_dict['relationship']['type']

    relationshipDF = pd.DataFrame({
        "名稱": relationship_name_list,
        "類型": relationship_type_list,
        "連結": relationship_link_list
    })

    relationship_sheet_name = sheet_adjust_name + \
        "_" + relationship_dict['name']

    if len(relationship_name_list) != 0:
        writer.pdToExcel(des=excel_file, df=relationshipDF,
                         sheetName=relationship_sheet_name, mode='a')

    # 處理社群連結

    social_dict = AboutDataList[3]

    social_name_list = []
    social_link_list = []
    social_type_list = []

    social_name_list += social_dict['social']['name']
    social_link_list += social_dict['social']['link']
    social_type_list += social_dict['social']['type']

    socialDF = pd.DataFrame({
        "名稱": social_name_list,
        "類型": social_type_list,
        "連結": social_link_list
    })

    social_sheet_name = sheet_adjust_name + "_" + social_dict['name']

    if len(social_name_list) != 0:
        writer.pdToExcel(des=excel_file, df=socialDF,
                         sheetName=social_sheet_name, mode='a')

    # 處理基本資料與關聯所有子表
    basic_dict = AboutDataList[3]

    birthday = basic_dict['birthday_date']
    if basic_dict['birthday_year'] != "":
        birthday = basic_dict['birthday_year'] + " " + birthday

    df_dict = {
        "姓名": subDir,
        "性別": basic_dict['gender'],
        "生日": str(birthday),
        "手機": basic_dict['phone'],
        "信箱": basic_dict['email'],
        "住址": basic_dict["address"],
        "個人頁連結": targetURL
    }

    basicDF = pd.DataFrame.from_records([df_dict])

    association_map = {
        "學經歷": {
            "name": experience_sheet_name,
            "length": len(experience_name_list)
        },
        "居住": {
            "name": live_sheet_name,
            "length": len(live_name_list)
        },
        "人際": {
            "name": relationship_sheet_name,
            "length": len(relationship_name_list)
        },
        "社群": {
            "name": social_sheet_name,
            "length": len(social_name_list)
        }
    }

    buildAssociation(excelFile=excel_file, basicDF=basicDF,
                     association_map=association_map)


def buildAssociation(excelFile, basicDF, association_map) -> None:
    for key, value in association_map.items():
        if value['length'] == 0:
            basicDF.insert(len(basicDF.columns), key, "")
        else:
            funcStr = Auxiliary.makeHyperlink(value['name'], "連結")
            basicDF.insert(loc=len(basicDF.columns),
                           column=key, value=[funcStr])
            # basicDF[key] = [funcStr]

    writer.pdToExcel(des=excelFile, df=basicDF, sheetName="about", mode='a')


def buildFriendzoneData(FriendzoneDataList, subDir, targetURL) -> None:

    excel_file = f'{configSetting.output_root}' + \
        subDir + '/friendzoneData.xlsx'
    name_list = []
    gender_list = []
    birthday_list = []
    phone_list = []
    email_list = []
    address_list = []
    work_list = []
    work_date_list = []
    profile_list = []
    associate_name_list = []
    associate_url_list = []

    for data in FriendzoneDataList:
        # 處理學經歷資料
        experience_dict = data[1]

        experience_name_list = []
        experience_date_list = []

        experience_name_list += (experience_dict['work']['name'])

        # 字串處理
        for i in range(0, len(experience_name_list)):
            startIndex = experience_name_list[i].find("at")
            if startIndex == -1:
                startIndex = experience_name_list[i].find("to")
            if startIndex == -1:
                experience_name_list[i] = experience_name_list[i]
            else:
                experience_name_list[i] = experience_name_list[i][startIndex + 3:]

        experience_date_list += (experience_dict['work']['date'])
        if len(experience_name_list) != 0:
            work_list.append(experience_name_list[0])
        else:
            work_list.append("")
        if len(experience_date_list) != 0:
            work_date_list.append(experience_date_list[0])
        else:
            work_date_list.append("")

        address_dict = data[2]
        if len(address_dict['live']['name']) != 0:
            address_list.append(address_dict['live']['name'][0])
        else:
            address_list.append("")

        basic_dict = data[3]

        birthday = basic_dict['birthday_date']
        if basic_dict['birthday_year'] != "":
            birthday = basic_dict['birthday_year'] + " " + birthday

        birthday_list.append(str(birthday))
        gender_list.append(basic_dict["gender"])
        phone_list.append(basic_dict['phone'])
        email_list.append(basic_dict['email'])

        profile_dict = data[5]

        name_list.append(profile_dict['name'])
        profile_list.append(profile_dict['url'])
        associate_name_list.append(subDir)
        associate_url_list.append(targetURL)

    # print(f"name_list lens: {len(name_list)},contents : {name_list}")
    # print(f"gender_list lens: {len(gender_list)},contents : {gender_list}")
    # print(f"birthday_list lens: {len(birthday_list)},contents : {birthday_list}")
    # print(f"phone_list lens: {len(phone_list)},contents : {phone_list}")
    # print(f"email_list lens: {len(email_list)},contents : {email_list}")
    # print(f"address_list lens: {len(address_list)},contents : {address_list}")
    # print(f"work_list lens: {len(work_list)},contents : {work_list}")
    # print(f"work_date_list lens: {len(work_date_list)},contents : {work_date_list}")
    # print(f"profile_list lens: {len(profile_list)},contents : {profile_list}")

    df = pd.DataFrame({
        "關係人姓名": associate_name_list,
        "關係人個人頁連結": associate_url_list,
        "姓名": name_list,
        "性別": gender_list,
        "生日": birthday_list,
        "手機": phone_list,
        "信箱": email_list,
        "住址": address_list,
        "工作": work_list,
        "工作起訖時間": work_date_list,
        "連結": profile_list
    })

    df = df.reset_index()  # 重新定義流水號
    df.drop('index', inplace=True, axis=1)
    writer.pdToExcel(des=excel_file, df=df, sheetName="sheet1")


def buildGroupMemberData(GroupMemberDataList, subDir) -> None:

    excel_file = f'{configSetting.output_root}' + subDir + '/groupMember.xlsx'
    name_list = []
    url_list = []
    id_list = []

    for data in GroupMemberDataList:

        name_list.append(data['name'])
        url_list.append(data['url'])
        id_list.append(data['userID'])

    df = pd.DataFrame({
        "姓名": name_list,
        "用戶編號": id_list,
        "個人頁連結": url_list,

    })

    df = df.reset_index()  # 重新定義流水號
    df.drop('index', inplace=True, axis=1)
    writer.pdToExcel(des=excel_file, df=df, sheetName="sheet1")


def buildAberrantAccountDataSet(sharerDF: pd.DataFrame, subDir: str):

    sharerDF = sharerDF[sharerDF['分享次數'] >= 5]  # 只有分享次數大於5是彙整的目標
    sharerDF = sharerDF[sharerDF['分享者類型'] == 1]  # 只蒐集個人類型的分享者
    target_user_list = sharerDF['分享者名稱'].tolist()

    # 每50個分一群
    target_user_list_group = list()
    temp_list = []
    for user in target_user_list:
        if len(temp_list) < 50:
            temp_list.append(user)
        else:
            target_user_list_group.append(temp_list.copy())
            temp_list = list()
            temp_list.append(user)
    if len(temp_list) > 0:
        target_user_list_group.append(temp_list.copy())

    for file_idx, group_user_list in enumerate(target_user_list_group):
        # 彙整表格模板
        df_template = pd.DataFrame({
            '項次': [],
            '帳號名稱': [],
            '帳號創立時間': [],
            '帳號網址': [],
            '外國人卻以中文評論': [],
            '性別錯置': [],
            '非人頭貼或無頭貼': [],
            '未顯示或無好友資訊': [],
            '好友多為外國人士': [],
            '好友具中國人士': [],
            '無動態或僅有大頭貼更換動態': [],
            '僅分享貼文': [],
            '以簡體字發文': [],
            '貼文多具親中言論': [],
            '發文風格轉變': [],
            '下架理由': [],
            '異常帳號紀錄暨特殊情形分析報告': []
        })
        for idx, user_name in enumerate(group_user_list):
            # 目標帳號的分享聚合資料
            target_now_detail = sharerDF.loc[sharerDF['分享者名稱'] == user_name]
            # 每一群excel抽出第一個帳號撰寫對應的異常帳號分析表word檔
            if idx == 0:
                writer.genernate_abnormal_account_word(
                    account_name=user_name, profile_url=target_now_detail.iloc[0]['分享者個人頁面'], subDir=subDir, index=file_idx)

            # 開始產生帳號彙整資料
            row = pd.DataFrame.from_dict({
                '項次': [idx+1],
                '帳號名稱': [f"{target_now_detail.iloc[0]['分享者名稱']}"],
                '帳號創立時間': [""],
                '帳號網址': [f"{str(target_now_detail.iloc[0]['分享者個人頁面'])}"],
                '外國人卻以中文評論': [""],
                '性別錯置': [""],
                '非人頭貼或無頭貼': [""],
                '未顯示或無好友資訊': [""],
                '好友多為外國人士': [""],
                '好友具中國人士': [""],
                '無動態或僅有大頭貼更換動態': [""],
                '僅分享貼文': [""],
                '以簡體字發文': [""],
                '貼文多具親中言論': [""],
                '發文風格轉變': [""],
                '下架理由': [1],
                '異常帳號紀錄暨特殊情形分析報告': [""]
            })
            df_template = pd.concat([df_template, row], ignore_index=True)
        template_file = ".\\template\\新版臉書異常帳號表格.xlsx"
        dst_file = f".\\output\\粉專\\{subDir}\\臉書異常帳號彙整_{str(file_idx)}.xlsx"
        writer.copyFileFromSrcToDst(src=template_file, dst=dst_file)
        writer.updateDataToExcelCertainCell(data=df_template, filename=dst_file, sheetname="工作表1", cell_index="A4")
        # writer.updateFormulaToExcel(filename=dst_file, sheetname="工作表1", start=4, end=53)


def generate_personal_profile_link(url: str) -> str:
    # 透過userID 整理出分享者個人的頁面網址
    if url.find("profile") != -1:
        return url
    else:
        start_idx = url.find("/", url.find("user"))
        end_idx = url.find("?")
        concat = url[start_idx + 1:end_idx]
        new_url = "https://www.facebook.com/profile.php?id=" + concat
        return new_url
