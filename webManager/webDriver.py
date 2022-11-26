from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from abc import ABC, abstractmethod
from webManager import customWait
from ioService import writer
import os
import random
import time
import traceback

# 關閉web driver的log訊息
os.environ['WDM_LOG_LEVEL'] = '0'

def loginForSeleniumWire(driver, accountCounter, jsonArrayData, loginURL) :

    # 登入的帳號與密碼
    username_list = jsonArrayData['user']['account']
    password_list = jsonArrayData['user']['password']
    account = username_list[accountCounter]
    pwd = password_list[accountCounter]
    print("開始登入,身分 :", account)
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

class customWebDriver(ABC):

    def __init__(self, driver=None, options=None, isLogin=False):
        """初始化driver實體,預設為未登入狀態."""

        self.driver = driver
        self.options = options
        self.loginURL = "https://www.facebook.com"
        self.isLogin = isLogin
    
    def setOptions(self, needImage, needHeadless):
        """設定模擬瀏覽器的設定參數.
        Args:
            needImage: 是否需要在加載頁面時載入圖片
            needHeadless: 是否要以無頭模式於背景執行
        """

        self.options = Options()
         # 避開彈跳視窗以免爬蟲被干擾
        self.options.add_argument("--disable-notifications")
        # 開啟無痕模式(有助於登入)
        self.options.add_argument('--incognito')
        self.options.add_argument("--window-size=1920,1080")
        # 設定運行時的語系
        self.options.add_argument("--lang=zh-tw")
        # options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
        # 屏蔽部分警告型log
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_experimental_option('excludeSwitches', ['enable-logging','enable-automation'])
        # docker原本的分享記憶體在 /dev/shm 是 64MB，會造成chorme crash，所以要改成寫入到 /tmp
        self.options.add_argument('--disable-dev-shm-usage')
        # 以最高權限運行
        self.options.add_argument('--no-sandbox')
        self.options.add_argument("--disable-setuid-sandbox")
        # google document 提到需要加上這個屬性來規避 bug
        self.options.add_argument('--disable-gpu')
        # 不加载图片, 提升速度(有操作截圖功能的話需要打開)
        if needImage:
            self.options.add_argument('blink-settings=imagesEnabled=false')
        if needHeadless:
            self.options.headless = True
    
    def driverInitialize(self):
        """建立啟動器,失敗時則重試到成功建立為止."""

        self.driver = None
        while self.driver is None :
            try:
                self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
            except:
                self.driver = None
                continue

        # 清掉暫存
        self.driver.delete_all_cookies()


    def login(self, accountCounter, jsonArrayData):
        """執行登入動作.
        Args:
            accountCounter: 當前是使用第幾組帳密做登入
            jsonArrayData: 設定檔資料
        """
        username_list = jsonArrayData['user']['account']
        password_list = jsonArrayData['user']['password']
        account = username_list[accountCounter]
        pwd = password_list[accountCounter]
        print("開始登入,身分 :",account)
        url = self.loginURL
        self.driver.get(url)

        # 輸入賬號密碼
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="email"]')))
        elem =  self.driver.find_element(By.ID, "email")
        elem.send_keys(account)

        elem =  self.driver.find_element(By.ID, "pass")
        elem.send_keys(pwd)

        elem.send_keys(Keys.RETURN)

        print("登入完成")
        time.sleep(1)
        return
    
    def clearDriver(self):
        """清除啟動器,回收相關資源."""

        if self.driver is not None:
            self.driver.close()
            self.driver.quit()
            self.driver = None
        self.isLogin = False

    @abstractmethod
    def _getSource(self):
        """抽象方法,待定義取得爬蟲資訊的手法."""
        pass

class postsDriver(customWebDriver):
    """取得文章與使用者相關docid資源的driver"""


    def _getSource(self, pageURL):
        time_pause = 3
        self.driver.get(pageURL)
        self.driver.implicitly_wait(20)

        time.sleep(time_pause)
        self.driver.refresh()
        time.sleep(time_pause)

        resp = self.driver.page_source

        time.sleep(time_pause)
        return resp

class feedbackDriver(customWebDriver):
    """取得分享行為相關docid資源的driver"""


    def _getSource(self, pageURL):
        print("開始動態加載feedback要用的js")
        time_pause = 2
        new_source = ""
        self.driver.get(pageURL)
        # 隱式等待
        self.driver.implicitly_wait(20)

        temp = []
        try:
            for x in range(1, 5):
                try:
                    self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                    temp = WebDriverWait(self.driver, 5).until(
                        customWait.scrollWait('//div[@class="x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z"]',  # 每一篇文章的開頭層級
                                temp, x))
                except:
                    break
            article_locator = (By.XPATH,
                            "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']")
            article_start_point = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(article_locator))

            for asp in article_start_point:
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", asp)

                share_point_locator = (By.XPATH,".//div[@class='xnfveip']//descendant::span[@class='x4k7w5x x1h91t0o x1h9r5lt xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j x1jfb8zj']")
                try:
                    share_list_point = WebDriverWait(asp,5).until(
                        EC.presence_of_all_elements_located(share_point_locator))
                except:
                    print("搜索其他文章來觸發分享節點的js")
                    continue
                
                time.sleep(random.randint(1,3))
                if len(share_list_point) <= 0:
                    print("搜索其他文章來觸發分享節點的js")
                    continue
                else :           
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", share_list_point[0])
                    text_check = ""
                    for slp in share_list_point:
                        text_check = slp.text
                        hover = ActionChains(self.driver).move_to_element(slp)
                        hover.perform()
                        time.sleep(time_pause)
                    
                    if "分享" not in text_check:
                        print("鎖定的文章只有留言節點,沒有分享節點,無法觸發js加載,搜索其他文章來觸發分享節點的js")
                        continue
                    new_source = self.driver.page_source
                    break
        except Exception as e:
            print("動態加載feedback js 發生錯誤: " ,str(e))
            print("粉專沒有抓到分享者加載的js,可能是網頁失效或是登入帳號失效導致,直接回傳空字串")
            time.sleep(time_pause)
            return new_source

        if len(new_source)>0:
            print("粉專有抓到分享者加載的js")
        else :
            print("粉專沒有抓到分享者加載的js,回傳空字串")
        # driver.close()
        time.sleep(time_pause)
        return new_source

class friendzoneDriver(customWebDriver):
    """取得朋友群相關docid資源的driver"""


    def _getSource(self, pageURL):  
        print("開始動態加載friendzone要用的js")
        new_source = ""
        time_pause = 2
        self.driver.get(pageURL)
        # 隱式等待
        self.driver.implicitly_wait(20)
        time.sleep(time_pause)
        try:
            banner_element_locator = (By.XPATH,
                            "//div[@class='xng8ra x6ikm8r x10wlt62 x1n2onr6 xh8yej3 x1ja2u2z x1a2a7pz' and @role='tablist']//descendant::a[@role='tab']")
            banner_element_points = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(banner_element_locator))
            
            for bep in banner_element_points:
                if bep.text=="朋友":
                    bep.click()
                else:
                    continue
                # hover = ActionChains(driver).move_to_element(bep)
                # hover.perform()
            
            time.sleep(time_pause)
            new_source = self.driver.page_source    
        except Exception as e:
            print("動態加載friendzone js 發生錯誤: " ,str(e))
            print("沒有抓到朋友群加載的js,可能是網頁失效或是登入帳號失效導致,直接回傳空字串")
            time.sleep(time_pause)
            return new_source


        if len(new_source)>0:
            print("有抓到用戶加載的friendzone js")
        else :
            print("沒有抓到friendzone js,回傳空字串")
        time.sleep(time_pause)
        return new_source

    def catchSpecialJsSource(self,pageURL):
        
        self.driver.get(pageURL)
        # 隱式等待
        self.driver.implicitly_wait(20)
        time.sleep(1)   
        new_source = self.driver.page_source

        return new_source

class screenshotDriver(customWebDriver):
    """擷取分享者或被分享者葉面
    Args: 
        driver: 啟動器
        url: 目標網址
        count: 當前擷取的是第幾個項目
        switch: 0:分享者,1:被分享者
        subDir: 當前目標的資料夾名稱

    Cautions: 跑截圖的時候請勿晃動畫面,以免截到錯誤的畫面
    """

    def _getSource(self,url,count,switch,subDir):
        time_pause = 2
        self.driver.get(url)
        time.sleep(time_pause)
        self.driver.execute_script("window.scrollTo(0,0)")
        path = ""
        if switch == 0:
            path = "./output/" + subDir + "/img/sharer/" + str(count) + ".png"
            locator = (By.CSS_SELECTOR,"div.x78zum5.xdt5ytf.x10cihs4.x1t2pt76.x1n2onr6.x1ja2u2z > div > div > div")
        else :
            path = "./output/" + subDir + "/img/been_sharer/" + str(count) + ".png"
            locator = (By.CSS_SELECTOR,"div.x78zum5.xdt5ytf.x10cihs4.x1t2pt76.x1n2onr6.x1ja2u2z > div > div")        
        
        try:
            #personal_profile上面的部分截圖
            catch_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
            #統一暫存到img資料夾,因涉及存檔,故加time.sleep
            catch_element.screenshot(path)
        except:
            writer.writeLogToFile(traceBack=traceback.format_exc())
            print("截圖動作失敗,查看log檔確認原因")

        time.sleep(time_pause)
        return    