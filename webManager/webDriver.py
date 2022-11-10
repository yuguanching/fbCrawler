import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from webManager import customWait
from ioService import reader,writer
import os
import json
import random
import time

# 關閉web driver的log訊息
os.environ['WDM_LOG_LEVEL'] = '0'

def catchFeedbackDynamicSource(pageURL,accountNumber,jsonArrayData):

    # Main part start!
    # ------------------------Web driver settings-------------------------------------
    options = webdriver.ChromeOptions()
    # 避開彈跳視窗以免爬蟲被干擾
    options.add_argument("--disable-notifications")
    # 開啟無痕模式(有助於登入)
    options.add_argument('--incognito')
    # 開啟無頭模式,此模式下,會只執行瀏覽器的核心,而不開啟UI,可以順利在背景執行
    # options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    # 設定運行時的語系
    options.add_argument("--lang=zh-tw")
    # options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    # 屏蔽部分警告型log
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging','enable-automation'])
    # docker原本的分享記憶體在 /dev/shm 是 64MB，會造成chorme crash，所以要改成寫入到 /tmp
    options.add_argument('--disable-dev-shm-usage')
    # 以最高權限運行
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-setuid-sandbox")
    # google document 提到需要加上這個屬性來規避 bug
    options.add_argument('--disable-gpu')
    # 不加载图片, 提升速度(有操作截圖功能的話需要打開)
    options.add_argument('blink-settings=imagesEnabled=false')
    options.headless = True



    print("開始動態加載feedback要用的js")
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)

    driver = None
    new_source = ""

    while driver is None :
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
        except:
            writer.writeLogToFile(traceBack=traceback.format_exc())
            print(traceback.format_exc())
            driver = None
            time.sleep(10)
            continue        
    
    
    # 清掉暫存
    driver.delete_all_cookies()

    login(driver=driver,accountCounter=accountNumber,jsonArrayData=jsonArrayData,loginURL="https://www.facebook.com")

    driver.get(pageURL)
    # 隱式等待
    driver.implicitly_wait(5)

    temp = []
    try:
        for x in range(1, 5):
            try:
                driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                temp = WebDriverWait(driver, 5).until(
                    customWait.scrollWait('//div[@class="x1ja2u2z xh8yej3 x1n2onr6 x1yztbdb"]',
                            temp, x))
            except:
                break
        article_locator = (By.XPATH,
                        "//div[@class='x1ja2u2z xh8yej3 x1n2onr6 x1yztbdb']")
        articleStartPoint = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(article_locator))

        for asp in articleStartPoint:
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", asp)

            sharePointLocator = (By.XPATH,".//div[@class='xnfveip']//descendant::span[@class='x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j']")
            try:
                shareListPoint = WebDriverWait(asp,5).until(
                    EC.presence_of_all_elements_located(sharePointLocator))
            except:
                print("搜索其他文章來觸發分享節點的js")
                continue
            
            time.sleep(random.randint(1,3))
            if len(shareListPoint) <= 0:
                print("搜索其他文章來觸發分享節點的js")
                continue
            else :           
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", shareListPoint[0])
                textCheck = ""
                for slp in shareListPoint:
                    textCheck = slp.text
                    hover = ActionChains(driver).move_to_element(slp)
                    hover.perform()
                    time.sleep(2)
                
                if "分享" not in textCheck:
                    print("鎖定的文章只有留言節點,沒有分享節點,無法觸發js加載,搜索其他文章來觸發分享節點的js")
                    continue
                new_source = driver.page_source
                break
    except Exception as e:
        print("動態加載feedback js 發生錯誤: " ,str(e))
        print("粉專沒有抓到分享者加載的js,可能是網頁失效或是登入帳號失效導致,直接回傳空字串")
        return new_source

    if len(new_source)>0:
        print("粉專有抓到分享者加載的js")
    else :
        print("粉專沒有抓到分享者加載的js,回傳空字串")
    driver.close()
    driver.quit()
    driver = None
    time.sleep(5)
    return new_source




def login(driver,accountCounter,jsonArrayData,loginURL) :

    # 登入的帳號與密碼
    usernameList = jsonArrayData['user']['account']
    passwordList = jsonArrayData['user']['password']
    account = usernameList[accountCounter]
    pwd = passwordList[accountCounter]
    print("開始登入,身分 :",account)
    url = loginURL
    driver.get(url)



    # 輸入賬號密碼
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="email"]')))
    elem = driver.find_element(By.ID, "email")
    elem.send_keys(account)

    elem = driver.find_element(By.ID, "pass")
    elem.send_keys(pwd)

    elem.send_keys(Keys.RETURN)

    print("登入完成")
    time.sleep(1)
    return


def getPageSource(pageURL,jsonArrayData,accountNumber=0):

    # ------------------------Web driver settings-------------------------------------
    options = webdriver.ChromeOptions()
    # 避開彈跳視窗以免爬蟲被干擾
    options.add_argument("--disable-notifications")
    # 開啟無痕模式(有助於登入)
    options.add_argument('--incognito')
    # 開啟無頭模式,此模式下,會只執行瀏覽器的核心,而不開啟UI,可以順利在背景執行
    # options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    # 設定運行時的語系
    options.add_argument("--lang=zh-tw")
    # options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    # 屏蔽部分警告型log
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging','enable-automation'])
    # docker原本的分享記憶體在 /dev/shm 是 64MB，會造成chorme crash，所以要改成寫入到 /tmp
    options.add_argument('--disable-dev-shm-usage')
    # 以最高權限運行
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-setuid-sandbox")
    # google document 提到需要加上這個屬性來規避 bug
    options.add_argument('--disable-gpu')
    # 不加载图片, 提升速度(有操作截圖功能的話需要打開)
    options.add_argument('blink-settings=imagesEnabled=false')
    options.headless = True
    # options.add_experimental_option('extensionLoadTimeout', 60000)

    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
    driver = None

    while driver is None :
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
        except:
            writer.writeLogToFile(traceBack=traceback.format_exc())
            print(traceback.format_exc())
            driver = None
            time.sleep(10)
            continue

    # 清掉暫存
    driver.delete_all_cookies()

    login(driver=driver,accountCounter=accountNumber,jsonArrayData=jsonArrayData,loginURL="https://www.facebook.com")

    driver.get(pageURL)

    driver.implicitly_wait(20)

    time.sleep(3)
    driver.refresh()
    time.sleep(3)

    resp = driver.page_source

    driver.close()
    driver.quit()
    driver = None
    time.sleep(3)

    return resp




def catchSectionFriendzoneSource(pageURL,jsonArrayData,accountNumber=0):
    
    # Main part start!
    # ------------------------Web driver settings-------------------------------------
    options = webdriver.ChromeOptions()
    # 避開彈跳視窗以免爬蟲被干擾
    options.add_argument("--disable-notifications")
    # 開啟無痕模式(有助於登入)
    options.add_argument('--incognito')
    # 開啟無頭模式,此模式下,會只執行瀏覽器的核心,而不開啟UI,可以順利在背景執行
    options.add_argument("--window-size=1920,1080")
    # 設定運行時的語系
    options.add_argument("--lang=zh-tw")
    # options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    # 屏蔽部分警告型log
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging','enable-automation'])
    # docker原本的分享記憶體在 /dev/shm 是 64MB，會造成chorme crash，所以要改成寫入到 /tmp
    options.add_argument('--disable-dev-shm-usage')
    # 以最高權限運行
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-setuid-sandbox")
    # google document 提到需要加上這個屬性來規避 bug
    options.add_argument('--disable-gpu')
    # 不加载图片, 提升速度(有操作截圖功能的話需要打開)
    options.add_argument('blink-settings=imagesEnabled=false')

    options.headless = True

    print("開始動態加載friendzone要用的js")
    driver = None
    new_source = ""

    while driver is None :
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
        except:
            writer.writeLogToFile(traceBack=traceback.format_exc())
            print(traceback.format_exc())
            driver = None
            time.sleep(10)
            continue

    
    # 清掉暫存
    driver.delete_all_cookies()

    login(driver=driver,accountCounter=accountNumber,jsonArrayData=jsonArrayData,loginURL="https://www.facebook.com")

    driver.get(pageURL)
    # 隱式等待
    driver.implicitly_wait(5)
    time.sleep(2)
    try:
        bannerElement_locator = (By.XPATH,
                        "//div[@class='xng8ra x6ikm8r x10wlt62 x1n2onr6 xh8yej3 x1ja2u2z x1a2a7pz' and @role='tablist']//descendant::a[@role='tab']")
        bannerElementPoints = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(bannerElement_locator))
        
        for bep in bannerElementPoints:
            if bep.text=="朋友":
                bep.click()
            else:
                continue
            # hover = ActionChains(driver).move_to_element(bep)
            # hover.perform()
        
        time.sleep(2)
        new_source = driver.page_source    
    except Exception as e:
        print("動態加載friendzone js 發生錯誤: " ,str(e))
        print("沒有抓到朋友群加載的js,可能是網頁失效或是登入帳號失效導致,直接回傳空字串")
        return new_source


    if len(new_source)>0:
        print("有抓到用戶加載的friendzone js")
    else :
        print("沒有抓到friendzone js,回傳空字串")
    driver.close()
    driver.quit()
    driver = None
    time.sleep(5)
    return new_source


def catchspecialJS(pageURL):
     # Main part start!
    # ------------------------Web driver settings-------------------------------------
    options = webdriver.ChromeOptions()
    # 避開彈跳視窗以免爬蟲被干擾
    options.add_argument("--disable-notifications")
    # 開啟無痕模式(有助於登入)
    options.add_argument('--incognito')
    # 開啟無頭模式,此模式下,會只執行瀏覽器的核心,而不開啟UI,可以順利在背景執行
    options.add_argument("--window-size=1920,1080")
    # 設定運行時的語系
    options.add_argument("--lang=zh-tw")
    # options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    # 屏蔽部分警告型log
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging','enable-automation'])
    # docker原本的分享記憶體在 /dev/shm 是 64MB，會造成chorme crash，所以要改成寫入到 /tmp
    options.add_argument('--disable-dev-shm-usage')
    # 以最高權限運行
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-setuid-sandbox")
    # google document 提到需要加上這個屬性來規避 bug
    options.add_argument('--disable-gpu')
    # 不加载图片, 提升速度(有操作截圖功能的話需要打開)
    options.add_argument('blink-settings=imagesEnabled=false')

    options.headless = True
    driver = None

    while driver is None :
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
        except:
            writer.writeLogToFile(traceBack=traceback.format_exc())
            print(traceback.format_exc())
            driver = None
            time.sleep(10)
            continue

    # 清掉暫存
    driver.delete_all_cookies()

    
    driver.get(pageURL)
    # 隱式等待
    driver.implicitly_wait(5)
    time.sleep(1)   
    new_source = driver.page_source

    driver.close()
    driver.quit()
    driver = None


    return new_source
