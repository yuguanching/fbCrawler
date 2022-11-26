from operator import mod
import time
import pandas as pd
import random
import re
import os 
import jieba
import traceback
import numpy
import json
import openpyxl


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from collections import Counter
from ioService import writer,reader
from helper import  Auxiliary
from webManager import webDriver
from wordcloud import WordCloud
from PIL import Image
# 關閉web driver的log訊息
os.environ['WDM_LOG_LEVEL'] = '0'

def buildCollectData(rawDataList, subDir, dropNA = False) -> list:

    excel_file = './output/' + subDir + '/collectData.xlsx'
    date = []
    image_url = []
    video_url = []
    like_count = []
    comment_count = []
    share_count = []
    content = []
    urls = []

    # 後續抓取分享需要用到的id標記
    feedback_id = []

    print(f"開始產生{subDir}的文章統計資料")

    # 各內容的抓取位置請參考__resolverEdgesPage__()
    for raw_data in rawDataList:
        # 抓取並處理時間
        date.append((lambda input_time:time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(input_time))))(raw_data["creation_time"]))

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

        #抓取文章的分享id標記
        feedback_id.append(raw_data["feedback_id"])

        #抓取文章網址
        urls.append(raw_data["url"])

    df = pd.DataFrame({
        '時間': date,
        '內容': content,
        '圖片': image_url,
        '按讚數': like_count,
        '留言數': comment_count,
        '分享數': share_count,
        '影片網址':video_url,
        '文章網址': urls
    })

    if dropNA:
        df['內容'].replace('', numpy.nan, inplace=True)
        df.dropna(subset=['內容'], inplace=True)
        df.reset_index(drop=True)

    writer.pdToExcel(des=excel_file, df=df, sheetName="collection", autoFitIsNeed=False)

    print(f"{subDir}的文章統計資料寫入完成,導出分享id標記陣列")
    return feedback_id



def buildDataParse(rawDataList, subDir, jsonArrayData) -> None:

    account_num = int(os.environ.get("account_number_now"))
    excel_file = './output/' + subDir + '/dataParse.xlsx'
    collect_data_file = './output/' + subDir + '/collectData.xlsx'
    tag_file = './output/' + subDir + '/tag.xlsx'
    posts_id = []
    sharer_name = []
    sharer_time = []
    sharer_url = []
    been_sharer_name = []
    been_sharer_url = []
    contents = []
    permalinks = []

    print(f"開始產生 {subDir} 的分享者統計資料")
    for article_share_list in rawDataList:
        if len(article_share_list) == 0 :
            continue
        else :
            for share_data in article_share_list:

                # 所屬文章編號
                posts_id.append(int(share_data["posts_count"]))

                # 分享者名稱
                sharer_name.append(share_data["sharer_name"])

                # 分享時間
                sharer_time.append((lambda input_time:time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(input_time))))(share_data["create_time"]))

                # 分享內容
                if share_data["sharer_id"] != "" :
                    contents.append(share_data["contents"])

                # 分享行為產生的單頁連結
                permalinks.append(share_data["permalink"])

                # # 分享者個人頁面
                # profile = "https://www.facebook.com/profile.php?id=" + str(share_data[1])
                # sharer_profile_url.append(profile)

                # 分享者網址和被分享者網址 , 若沒有被分享的目的地,則被分享者網址放空,分享者網址填個人頁面
                if share_data["been_sharer_id"] == "":
                    profile = "https://www.facebook.com/profile.php?id=" + str(share_data["sharer_id"])
                    sharer_url.append(profile)
                    been_sharer_url.append("")
                else :
                    sharerTempURL = "https://www.facebook.com/groups/" + str(share_data["been_sharer_id"]) + "/user/" + str(share_data["sharer_id"])+ "/"
                    beenSharerTempURL = "https://www.facebook.com/groups/" + str(share_data["been_sharer_id"]) + "/"
                    sharer_url.append(sharerTempURL)
                    been_sharer_url.append(beenSharerTempURL)
                
                # 被分享者名稱
                if share_data["been_sharer_id"] == "":
                    been_sharer_name.append("")
                else :
                    temp_name = ""
                    temp_name = share_data["been_sharer_raw_name"]
                    startPoint = temp_name.find(":")
                    endPoint = temp_name.find(".")
                    temp_name = temp_name[startPoint+2:endPoint]
                    been_sharer_name.append(temp_name)
            
    df = pd.DataFrame({
        "所屬文章編號":posts_id,
        "分享者名稱":sharer_name,
        "發布時間":sharer_time,
        "分享者網址":sharer_url,
        "被分享者名稱":been_sharer_name,
        "被分享者網址":been_sharer_url,
        "分享單頁連結":permalinks
    })
    df = df.reset_index() #重新定義流水號
    df.drop('index', inplace=True, axis=1)
    df.insert(0,"粉專名稱",subDir)
    writer.pdToExcel(des=excel_file, df=df, sheetName="sharerData")


    # 先記錄所有需要斷句斷詞的項目

    article_dict = pd.read_excel(collect_data_file, sheet_name="collection", usecols="C")
    article_contents = article_dict['內容'].dropna().tolist()

    all_contents = contents + article_contents

    tag_raw_df = pd.DataFrame({
        "未處理斷句":all_contents
    })
    tag_raw_df = tag_raw_df.reset_index() #重新定義流水號
    tag_raw_df.drop('index', inplace=True, axis=1)
    writer.pdToExcel(des=tag_file, df=tag_raw_df, sheetName="rawSentences")

    # 建立熱詞表
    buildTag(subDir)

    #**在有sharerData的情況下補救用**
    # df = pd.read_excel(excel_file,sheet_name="sharerData",usecols="B:H")

    #-----------------------產生分享者統整資料,並寫到sheet: sharer --------------------------------------
    sharer = df["分享者名稱"].tolist()
    sharer_counter = Counter(sharer)
    sharer_url = []
    sharer_profile_url = []
    for x in sharer_counter:
        temp = df.loc[df['分享者名稱']==x, '分享者網址'].iloc[0]
        sharer_url.append(temp)
    #透過userID 整理出分享者個人的頁面網址
    for url in sharer_url :
        if url.find("profile") != -1:
            sharer_profile_url.append(url)
        else:
            start_idx = url.find("/",url.find("user"))
            end_idx = url.find("?")
            concat = url[start_idx+1:end_idx]
            new_url = "https://www.facebook.com/profile.php?id=" + concat
            sharer_profile_url.append(new_url)

    sharer_df = pd.DataFrame.from_dict(sharer_counter, orient='index').reset_index()
    sharer_df['分享者連結'] = sharer_url
    sharer_df['分享者個人頁面'] = sharer_profile_url
    try:
        sharer_df.set_axis(['分享者', '分享次數', '分享者連結', '分享者個人頁面'], axis=1, inplace=True)
    except:
        sharer_df = pd.DataFrame({
            "分享者":[],
            "分享次數":[],
            "分享者連結":[],
            "分享者個人頁面":[]
        })
    sharer_df = sharer_df.sort_values('分享次數', ascending=False)
    sharer_df = sharer_df.reset_index()
    del sharer_df['index']
    sharer_df.insert(0, "粉專名稱", subDir)

    #------------------------------寫檔到sheet: sharer -------------------------------------
    writer.pdToExcel(des=excel_file, df=sharer_df, sheetName="sharer", mode='a')




    #----------------------彙整好分享者統計資料後,抓取分享者的個人頁面截圖-------------------------
    try:
        screenshot_driver = webDriver.screenshotDriver(driver=None, options=None, isLogin=False)
        screenshot_driver.setOptions(needHeadless=True, needImage=False)
        screenshot_driver.driverInitialize()
        screenshot_driver.login(account_num, jsonArrayData)

        count = 0
        for s_url in sharer_df["分享者個人頁面"].tolist():
            if s_url == "":
                continue
            else:
                if count >=3 :
                    time.sleep(random.randint(2,3))
                    break
                else:
                    print("開始擷取分享者個人頁面的圖片,id : "+str(count))
                    screenshot_driver._getSource(s_url,count, 0, subDir)
                    count+=1
    finally:
        screenshot_driver.clearDriver()


    #-----------------------產生被分享者統整資料,並寫到sheet: been_sharer --------------------------------------

    #已去掉被分享者的nan雜訊
    been_sharer = df["被分享者名稱"].dropna().tolist()
    been_sharer_counter = Counter(been_sharer)
    been_sharer_url = []
    for y in been_sharer_counter:
        #遇到nan就跳過
        try:
            temp1 = df.loc[df['被分享者名稱']==y, '被分享者網址'].iloc[0]
            been_sharer_url.append(temp1)
        except:
            continue

    been_sharer_df = pd.DataFrame.from_dict(been_sharer_counter, orient='index').reset_index()
    been_sharer_df['社團/粉專連結'] = been_sharer_url
    try:
        been_sharer_df.set_axis(['被分享者', '被分享次數', '社團/粉專連結'], axis=1, inplace=True)
    except:
        been_sharer_df = pd.DataFrame({
            "被分享者":[],
            "被分享次數":[],
            "社團/粉專連結":[]
        })
    been_sharer_df = been_sharer_df.sort_values('被分享次數', ascending=False)
    been_sharer_df = been_sharer_df.reset_index()
    del been_sharer_df['index']
    been_sharer_df.insert(0, "粉專名稱", subDir)

    #------------------------------寫檔到sheet: been_sharer-------------------------------------
    writer.pdToExcel(des=excel_file, df=been_sharer_df, sheetName="been_sharer", mode='a')




    #---------------------------彙整好被分享者統計資料後,抓取社團/粉專連結頁面截圖-------------------------------
    try:
        screenshot_driver = webDriver.screenshotDriver(driver=None, options=None, isLogin=False)
        screenshot_driver.setOptions(needHeadless=True, needImage=False)
        screenshot_driver.driverInitialize()
        screenshot_driver.login(account_num, jsonArrayData)

        count = 0
        for s_url in been_sharer_df["社團/粉專連結"].tolist():
            if s_url == "":
                continue
            else:
                if count >=3 :
                    time.sleep(random.randint(2,3))
                    break
                else:
                    print("開始擷取社團/粉專連結頁面的圖片,id : " + str(count))
                    screenshot_driver._getSource(s_url, count, 1, subDir)
                    count+=1
    finally:
        screenshot_driver.clearDriver()

    print("批次資料整理完畢")



def buildTag(subDir) -> None:
    #建立一個Counter 物件,準備統計各分享者內容中的tag標籤
    tag_file = f"./output/{subDir}/tag.xlsx"
    sentence_counter = Counter()
    special_chars = r"[!|#|~|,|。|，|？|！|：|;|；|』|『|」|「|“|、|”|】|【|／]" 
    #讀取相關的欄位
    data = pd.read_excel(tag_file, sheet_name="rawSentences", usecols="B")
    raw_tag_list = data["未處理斷句"].dropna().tolist()

    for raw_data in raw_tag_list:
        temp = re.sub(special_chars, " ", raw_data)
        temp = addSpaceBetweenEmojies(temp)
        temp = temp.strip()
        split_temp = re.split(r'[\s|\r\n]+', temp)
        split_temp = [split_str for split_str in split_temp if Auxiliary.detectURL(split_str)]     
        sentence_counter.update(split_temp)

    if len(sentence_counter) != 0 :
        #建立儲存tag頻率的xlsx表
        tagList_df = pd.DataFrame.from_dict(sentence_counter, orient='index').reset_index()
        tagList_df = tagList_df.set_axis(['斷句','使用熱度'], axis=1)
        tagList_df = tagList_df.sort_values('使用熱度', ascending=False)
        writer.pdToExcel(des=tag_file, df=tagList_df, sheetName="sentence", indexIsNeed=False, mode='a')
    else :
        empty_df = pd.DataFrame(columns=['斷句', '使用熱度'])
        writer.pdToExcel(des=tag_file, df=empty_df, sheetName="sentence", indexIsNeed=False, mode='a')

    word_counter = Counter()
    jieba.load_userdict("./config/jieba/dict.txt.big.txt")
    # jieba.load_userdict("./config/jieba/dict_extends.txt")
    with open('./config/jieba/stop_words.txt', encoding="utf_8") as f:
        stop_words = [line.strip() for line in f.readlines()]
    for key in sentence_counter :
        parse_list = jieba.lcut(key, cut_all=False)
        parse_list = [w for w in parse_list if len(w)>1 and not re.match('^[a-z|A-Z|0-9|.]*$', w)]
        parse_list = [w for w in parse_list if w not in stop_words]
        for i in range(1, int(sentence_counter[key]+1)):
            word_counter.update(parse_list)
    word_list_df = pd.DataFrame.from_dict(word_counter, orient='index').reset_index()
    try:
        word_list_df.set_axis(['斷詞', '詞頻'], axis=1, inplace=True)
    except:
        word_list_df = pd.DataFrame({
            "斷詞":[],
            "詞頻":[]
        })
    word_list_df = word_list_df.sort_values('詞頻', ascending=False)
    writer.pdToExcel(des=tag_file, df=word_list_df, sheetName="word", indexIsNeed=False, mode='a')

    print("斷詞表建置完成")
    createWordCloud(subDir=subDir, counter=word_counter)



def addSpaceBetweenEmojies(text) -> str:
  # Ref: https://gist.github.com/Alex-Just/e86110836f3f93fe7932290526529cd1#gistcomment-3208085
  # Ref: https://en.wikipedia.org/wiki/Unicode_block
  EMOJI_PATTERN = re.compile(
    "(["
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "])"
  )
  text = re.sub(EMOJI_PATTERN, r' ', text)
  return text


def createWordCloud(subDir, counter, forAll = False) -> None:
    file_path = f"./output/{subDir}/img/word_cloud/word_cloud.png"
    if forAll:
        file_path = "./output/all_word_cloud.png"
    font_path = f"./config/word_cloud/標楷體.ttc"
    mask_path = f"./config/word_cloud/organza_asstapas.png"
    mask = numpy.array(Image.open(mask_path))
    mask=(mask==0)*255

    try:
        print("正在產生wordcloud圖片中...")
        wc = WordCloud(
            background_color="#272727", #可配合色碼表
            mode="RGB",
            relative_scaling=0.4,
            scale=10,
            font_path=font_path,
            margin=3,
            max_words=200,
            colormap="Dark2_r", # supported values are 'Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', 'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r', 'flag', 'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r', 'hsv', 'hsv_r', 'inferno', 'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', 'rainbow_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', 'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'turbo', 'turbo_r', 'twilight', 'twilight_r', 'twilight_shifted', 'twilight_shifted_r', 'viridis', 'viridis_r', 'winter', 'winter_r'
            prefer_horizontal=0.95,
            mask=mask
        )

        wc.generate_from_frequencies(frequencies=counter)
        wc.to_file(file_path)
        print("wordcloud圖片產生完成")
    except:
        print("產生wordCloud發生了未知意外,請參考log紀錄")
        writer.writeLogToFile(traceBack=traceback.format_exc())
    finally:
        return 



def buildAboutData(AboutDataList, subDir, targetURL) -> None:
    excel_file = './output/' + subDir + '/aboutData.xlsx'

    sheet_adjust_name = subDir.replace(" ","_")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "about"
    wb.save(excel_file)

    # with open("contents.json",encoding='utf_8') as f :
    #             jsonArrayData = json.load(f)
    #             f.close()
    # AboutDataList = jsonArrayData


    # 0:總覽ID、1:學歷與工作經歷、2:住過的地方、3:聯絡與基本資料、4:家人與感情狀況
    # 需要另外開表的項目:學校與工作經歷 住過的地方 社群資料 社交人際
    

    # 處理學經歷資料
    experience_dict = AboutDataList[1]
    experience_dict['work']['type'] = ["工作"] * len(experience_dict['work']['name'])
    experience_dict['college']['type'] = ["大專院校"] * len(experience_dict['college']['name'])
    experience_dict['highSchool']['type'] = ["高中"] * len(experience_dict['highSchool']['name'])

    experience_name_list = []
    experience_link_list = []
    experience_date_list = []
    experience_type_list = []

    experience_name_list+=(experience_dict['work']['name'])
    experience_name_list+=(experience_dict['college']['name'])
    experience_name_list+=(experience_dict['highSchool']['name'])

    # 字串處理
    for i in range(0,len(experience_name_list)):
        startIndex = experience_name_list[i].find("at")
        if startIndex== -1:
            startIndex = experience_name_list[i].find("to")
        if startIndex == -1:
            experience_name_list[i] = experience_name_list[i]
        else:
            experience_name_list[i] = experience_name_list[i][startIndex+3:]

    experience_link_list+=(experience_dict['work']['link'])
    experience_link_list+=(experience_dict['college']['link'])
    experience_link_list+=(experience_dict['highSchool']['link'])

    experience_date_list+=(experience_dict['work']['date'])
    experience_date_list+=(experience_dict['college']['date'])
    experience_date_list+=(experience_dict['highSchool']['date'])

    experience_type_list+=(experience_dict['work']['type'])
    experience_type_list+=(experience_dict['college']['type'])
    experience_type_list+=(experience_dict['highSchool']['type'])


    experienceDF = pd.DataFrame({
        "名稱":experience_name_list,
        "類型":experience_type_list,
        "時間":experience_date_list,
        "連結":experience_link_list
    })

    experience_sheet_name = sheet_adjust_name + "_" + experience_dict['name']

    if len(experience_name_list)!=0:
        writer.pdToExcel(des=excel_file,df=experienceDF,sheetName=experience_sheet_name,mode='a')
    
    # 處理住過的地方
    live_dict = AboutDataList[2]

    live_name_list = []
    live_link_list = []
    live_type_list = []

    live_name_list+=live_dict['live']['name']
    live_link_list+=live_dict['live']['link']
    live_type_list+=live_dict['live']['type']

    liveDF = pd.DataFrame({
        "名稱":live_name_list,
        "類型":live_type_list,
        "連結":live_link_list
    })

    live_sheet_name = sheet_adjust_name + "_" + live_dict['name']

    if len(live_name_list)!=0:
        writer.pdToExcel(des=excel_file,df=liveDF,sheetName=live_sheet_name,mode='a')

    # 處理人際關係
    relationship_dict = AboutDataList[4]

    relationship_name_list = []
    relationship_link_list = []
    relationship_type_list = []

    relationship_name_list+=relationship_dict['relationship']['name']
    relationship_link_list+=relationship_dict['relationship']['link']
    relationship_type_list+=relationship_dict['relationship']['type']

    relationshipDF = pd.DataFrame({
        "名稱":relationship_name_list,
        "類型":relationship_type_list,
        "連結":relationship_link_list
    })

    relationship_sheet_name = sheet_adjust_name + "_" + relationship_dict['name']

    if len(relationship_name_list)!=0:
        writer.pdToExcel(des=excel_file,df=relationshipDF,sheetName=relationship_sheet_name,mode='a')


    # 處理社群連結

    social_dict = AboutDataList[3]

    social_name_list = []
    social_link_list = []
    social_type_list = []

    social_name_list+=social_dict['social']['name']
    social_link_list+=social_dict['social']['link']
    social_type_list+=social_dict['social']['type']

    socialDF = pd.DataFrame({
        "名稱":social_name_list,
        "類型":social_type_list,
        "連結":social_link_list
    })

    social_sheet_name = sheet_adjust_name + "_" + social_dict['name']

    if len(social_name_list)!=0:
        writer.pdToExcel(des=excel_file,df=socialDF,sheetName=social_sheet_name,mode='a')


    # 處理基本資料與關聯所有子表
    basic_dict = AboutDataList[3]

    birthday = basic_dict['birthday_date']
    if basic_dict['birthday_year']!="":
        birthday = basic_dict['birthday_year'] + " " + birthday 

    df_dict = {
        "姓名":subDir,
        "性別":basic_dict['gender'],
        "生日":str(birthday),
        "手機":basic_dict['phone'],
        "信箱":basic_dict['email'],
        "住址":basic_dict["address"],
        "個人頁連結":targetURL
    }

    basicDF = pd.DataFrame.from_records([df_dict])    

    association_map = {
        "學經歷":{
            "name":experience_sheet_name,
            "length":len(experience_name_list)
        },
        "居住":{
            "name":live_sheet_name,
            "length":len(live_name_list)
        },
        "人際":{
            "name":relationship_sheet_name,
            "length":len(relationship_name_list)
        },
        "社群":{
            "name":social_sheet_name,
            "length":len(social_name_list)
        }
    }

    buildAssociation(excelFile=excel_file, basicDF=basicDF, association_map=association_map)

def buildAssociation(excelFile,basicDF,association_map) -> None:
    for key,value in association_map.items():
        if value['length'] == 0:
            basicDF.insert(len(basicDF.columns), key, "")
        else:
            funcStr = Auxiliary.makeHyperlink(value['name'],"連結")
            basicDF.insert(loc=len(basicDF.columns), column=key, value=[funcStr])
            # basicDF[key] = [funcStr]
    
    writer.pdToExcel(des=excelFile, df=basicDF, sheetName="about", mode='a')

def buildFriendzoneData(FriendzoneDataList, subDir, targetURL) -> None:

    excel_file = './output/' + subDir + '/friendzoneData.xlsx'
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

        experience_name_list+=(experience_dict['work']['name'])

        # 字串處理
        for i in range(0, len(experience_name_list)):
            startIndex = experience_name_list[i].find("at")
            if startIndex == -1:
                startIndex = experience_name_list[i].find("to")
            if startIndex == -1:
                experience_name_list[i] = experience_name_list[i]
            else:
                experience_name_list[i] = experience_name_list[i][startIndex+3:]    
                
        
        experience_date_list+=(experience_dict['work']['date'])
        if len(experience_name_list) != 0:
            work_list.append(experience_name_list[0])
        else:
            work_list.append("")
        if len(experience_date_list) != 0:
            work_date_list.append(experience_date_list[0])
        else :
            work_date_list.append("")
        
        address_dict = data[2]
        if len(address_dict['live']['name']) != 0:
            address_list.append(address_dict['live']['name'][0])
        else:
            address_list.append("")
        

        basic_dict = data[3]

        birthday = basic_dict['birthday_date']
        if basic_dict['birthday_year']!="":
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
        "關係人姓名":associate_name_list,
        "關係人個人頁連結":associate_url_list,
        "姓名":name_list,
        "性別":gender_list,
        "生日":birthday_list,
        "手機":phone_list,
        "信箱":email_list,
        "住址":address_list,
        "工作":work_list,
        "工作起訖時間":work_date_list,
        "連結":profile_list
    })

    df = df.reset_index() #重新定義流水號
    df.drop('index', inplace=True, axis=1)
    writer.pdToExcel(des=excel_file, df=df, sheetName="sheet1")