import os
import random
import time
import traceback
import configSetting
import re

from datetime import datetime
from helper import Auxiliary
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from typing import Union, Tuple
from abc import ABC, abstractmethod
from webManager import customWait
from ioService import writer


# 關閉web driver的log訊息
os.environ['WDM_LOG_LEVEL'] = '0'


# 有新的driver建立時要去configSetting.py登記型別

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
        self.options.add_argument('--log-level=3')
        self.options.add_argument("--window-size=1920,1080")
        # 設定運行時的語系
        self.options.add_argument("--lang=zh-tw")
        # 屏蔽部分警告型log
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        # docker原本的分享記憶體在 /dev/shm 是 64MB，會造成chrome crash，所以要改成寫入到 /tmp
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
            self.options.add_argument("--headless=new")

    def driverInitialize(self, driver: webdriver.Chrome = None):
        """
        建立啟動器,失敗時則重試到成功建立為止
        若有已存在的啟動器餵進來,則直接植入當前物件的屬性中
        """
        self.driver = None
        if driver is not None:
            self.driver = driver
        else:
            while self.driver is None:
                try:
                    self.driver = webdriver.Chrome(service=Service(
                        ChromeDriverManager().install()), options=self.options)
                except:
                    self.driver = None
                    continue

        # 清掉暫存
        self.driver.delete_all_cookies()

    def login(self, accountCounter=0):
        """執行登入動作.
        Args:
            accountCounter: 當前是使用第幾組帳密做登入
        """
        username_list = configSetting.json_array_data['user']['account']
        password_list = configSetting.json_array_data['user']['password']
        account = username_list[accountCounter]
        pwd = password_list[accountCounter]
        print("開始登入,身分 :", account)
        url = self.loginURL
        self.driver.get(url)

        # 輸入賬號密碼
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="email"]')))
        elem = self.driver.find_element(By.ID, "email")
        elem.send_keys(account)

        elem = self.driver.find_element(By.ID, "pass")
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
        self.driver.implicitly_wait(configSetting.implicitly_wait)

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
        self.driver.implicitly_wait(configSetting.implicitly_wait)
        temp = []
        try:
            for x in range(1, 5):
                try:
                    self.driver.execute_script(
                        "window.scrollTo(0,document.body.scrollHeight)")
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

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", asp)

                share_point_locator = (
                    By.XPATH, ".//div[@class='x1n2onr6']//descendant::span[@class='x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j']")
                try:
                    share_list_point = WebDriverWait(asp, 5).until(
                        EC.presence_of_all_elements_located(share_point_locator))
                except:
                    print("搜索其他文章來觸發分享節點的js")
                    continue

                time.sleep(random.randint(1, 3))
                if len(share_list_point) <= 0:
                    print("搜索其他文章來觸發分享節點的js")
                    continue
                else:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", share_list_point[0])
                    text_check = ""
                    has_share_text = False
                    for slp in share_list_point:
                        text_check = slp.text
                        if "分享" in text_check:
                            has_share_text = True
                        hover = ActionChains(self.driver).move_to_element(slp)
                        hover.perform()
                        time.sleep(time_pause)

                    if not has_share_text:
                        print("鎖定的文章只有留言節點,沒有分享節點,無法觸發js加載,搜索其他文章來觸發分享節點的js")
                        continue
                    new_source = self.driver.page_source
                    break
        except Exception as e:
            print("動態加載feedback js 發生錯誤: ", str(e))
            print("粉專沒有抓到分享者加載的js,可能是網頁失效或是登入帳號失效導致,直接回傳空字串")
            time.sleep(time_pause)
            return new_source

        if len(new_source) > 0:
            print("粉專有抓到分享者加載的js")
        else:
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
        self.driver.implicitly_wait(configSetting.implicitly_wait)
        time.sleep(time_pause)
        try:
            banner_element_locator = (By.XPATH,
                                      "//div[@class='xng8ra x6ikm8r x10wlt62 x1n2onr6 xh8yej3 x1ja2u2z x1a2a7pz' and @role='tablist']//descendant::a[@role='tab']")
            banner_element_points = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(banner_element_locator))

            for bep in banner_element_points:
                if bep.text == "朋友":
                    bep.click()
                else:
                    continue
                # hover = ActionChains(driver).move_to_element(bep)
                # hover.perform()

            time.sleep(time_pause)
            new_source = self.driver.page_source
        except Exception as e:
            print("動態加載friendzone js 發生錯誤: ", str(e))
            print("沒有抓到朋友群加載的js,可能是網頁失效或是登入帳號失效導致,直接回傳空字串")
            time.sleep(time_pause)
            return new_source

        if len(new_source) > 0:
            print("有抓到用戶加載的friendzone js")
        else:
            print("沒有抓到friendzone js,回傳空字串")
        time.sleep(time_pause)
        return new_source

    def catchSpecialJsSource(self, pageURL):

        self.driver.get(pageURL)
        # 隱式等待
        self.driver.implicitly_wait(configSetting.implicitly_wait)
        time.sleep(1)
        new_source = self.driver.page_source

        return new_source


class screenshotDriver(customWebDriver):
    """擷取分享者或被分享者頁面
    Args: 
        driver: 啟動器
        url: 目標網址
        count: 當前擷取的是第幾個項目
        switch: 0:分享者,1:被分享者
        subDir: 當前目標的資料夾名稱

    Cautions: 跑截圖的時候請勿晃動畫面,以免截到錯誤的畫面
    """

    def _getSource(self, url, count, switch, subDir, article_id=None) -> bool:
        self.driver.get(url)
        time.sleep(2)
        self.driver.execute_script("window.scrollTo(0,0)")
        path = ""
        current_url = self.driver.current_url

        try:
            jump_dialog_exit_locator = (
                By.XPATH, "//div[@class='x1n2onr6 x1ja2u2z x1afcbsf x78zum5 xdt5ytf x1a2a7pz x6ikm8r x10wlt62 x71s49j x1jx94hy x1qpq9i9 xdney7k xu5ydu1 xt3gfkd x104qc98 x1g2kw80 x16n5opg xl7ujzl xhkep3z x193iq5w' and @role='dialog']/child::div[@class='x92rtbv x10l6tqk x1tk7jg1 x1vjfegm']/child::div")
            jel_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(jump_dialog_exit_locator))
            jel_element.click()
            time.sleep(2)
        except:
            print("no jump")
            pass
        if switch == 0:
            path = f"{configSetting.output_root}" + subDir + "/img/sharer/" + str(count) + ".png"
            locator = (By.XPATH, "//div[@class='x78zum5 xdt5ytf x1t2pt76 x1n2onr6']/child::div")
        elif switch == 1:
            path = f"{configSetting.output_root}" + subDir + "/img/been_sharer/" + str(count) + ".png"
            locator = (By.XPATH, "//div[@class='x78zum5 xdt5ytf x1t2pt76 x1n2onr6']/child::div")
        else:
            mod_count = count + 5
            if mod_count < 10:
                mod_count = "0" + str(mod_count)
            else:
                mod_count = str(mod_count)
            path = f"{configSetting.output_root}" + subDir + "/img/report/images_" + mod_count + ".png"
            if "video" in current_url or "watch" in current_url:  # 抓影片的類型
                if "live" in current_url:
                    locator = (
                        By.XPATH,
                        "//div[@class='x78zum5 x5yr21d xl56j7k xh8yej3']",
                    )
                else:
                    locator = (
                        By.XPATH,
                        "//div[@class='x78zum5 xkrivgy x1gryazu x4pn7vq']",
                    )
            elif "reel" in current_url:  # 抓短影音的類型
                locator = (
                    By.XPATH,
                    "//div[@class='xjbqb8w x1lq5wgf xgqcy7u x30kzoy x9jhf4c x78zum5 x1q0g3np xod5an3 x14vqqas x6ikm8r x10wlt62 x1n2onr6 x1k90msu x6o7n8i x9lcvmn x1m6m0jg']",
                )
            else:
                locator = (
                    By.XPATH,
                    "//div[@class='html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd']/../..",
                )

        try:
            # personal_profile上面的部分截圖
            catch_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
            # 統一暫存到img資料夾,因涉及存檔,故加time.sleep
            catch_element.screenshot(path)
            Auxiliary.image_compress(path)
            if switch == 2:
                with open(path, "rb") as f:
                    image = f.read()
                configSetting.db_adapter.update_article_image(article_id=article_id, image_field="image", image=image)
        except:
            writer.writeLogToFile(traceBack=traceback.format_exc())
            print("截圖動作失敗,查看log檔確認原因")
            return False
        time.sleep(2)
        return True

    def fetch_fanspage_basic_data(self, url, subDir) -> Tuple[str, str, str, str]:
        date_re = re.compile(pattern=r'(\d+)年(\d+)月(\d+)日')
        date_re_no_year = re.compile(pattern=r'(\d+)月(\d+)日')
        homepage_image_path = f"{configSetting.output_root}" + subDir + "/img/report/images_01.png"
        transparency_image_path = f"{configSetting.output_root}" + subDir + "/img/report/images_00.png"
        self.driver.get(f"{url}")
        time.sleep(2)
        self.driver.execute_script("window.scrollTo(0,0)")
        try:
            jump_dialog_exit_locator = (
                By.XPATH, "//div[@class='x1n2onr6 x1ja2u2z x1afcbsf x78zum5 xdt5ytf x1a2a7pz x6ikm8r x10wlt62 x71s49j x1jx94hy x1qpq9i9 xdney7k xu5ydu1 xt3gfkd x104qc98 x1g2kw80 x16n5opg xl7ujzl xhkep3z x193iq5w' and @role='dialog']/child::div[@class='x92rtbv x10l6tqk x1tk7jg1 x1vjfegm']/child::div")
            jel_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(jump_dialog_exit_locator))
            jel_element.click()
            time.sleep(2)
        except:
            print("no jump")
            pass
        locator = (By.XPATH, "//div[@class='x78zum5 xdt5ytf x1iyjqo2 x1t2pt76 xeuugli']")
        homepage_view = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
        homepage_view.screenshot(homepage_image_path)
        Auxiliary.image_compress(homepage_image_path)
        profile_photo_url = self.driver.find_element(
            By.XPATH, "//a[@class='x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1q0g3np x87ps6o x1lku1pv x1a2a7pz xzsf02u x1rg5ohu']").get_attribute("href")
        transparency_page = f"{url}&sk=about_profile_transparency" if 'profile' in url else f"{url}/about_profile_transparency"
        self.driver.get(url=transparency_page)
        time.sleep(2)
        self.driver.execute_script("window.scrollTo(0,0)")
        try:
            jump_dialog_exit_locator = (
                By.XPATH, "//div[@class='x1n2onr6 x1ja2u2z x1afcbsf x78zum5 xdt5ytf x1a2a7pz x6ikm8r x10wlt62 x71s49j x1jx94hy x1qpq9i9 xdney7k xu5ydu1 xt3gfkd x104qc98 x1g2kw80 x16n5opg xl7ujzl xhkep3z x193iq5w' and @role='dialog']/child::div[@class='x92rtbv x10l6tqk x1tk7jg1 x1vjfegm']/child::div")
            jel_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(jump_dialog_exit_locator))
            jel_element.click()
            time.sleep(2)
        except:
            print("no jump")
            pass

        found_date = self.driver.find_elements(
            By.XPATH, "//div[@class='x9f619 x1n2onr6 x1ja2u2z x78zum5 x1nhvcw1 x1qjc9v5 xozqiw3 x1q0g3np xexx8yu xykv574 xbmpl8g x4cne27 xifccgj xs83m0k']")[1].find_element(By.XPATH, ".//div[@class='xzsf02u x6prxxf xvq8zen x126k92a x12nagc']").text

        check_all = self.driver.find_element(
            By.XPATH, "//div[@class='x1n2onr6 x1ja2u2z x78zum5 x2lah0s xl56j7k x6s0dn4 xozqiw3 x1q0g3np xi112ho x17zwfj4 x585lrc x1403ito x972fbf xcfux6l x1qhh985 xm0m39n x9f619 xn6708d x1ye3gou x1qhmfi1 x1r1pt67']")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", check_all)
        time.sleep(2)
        check_all.click()
        time.sleep(2)
        locator = (By.XPATH, "//div[@class='x1n2onr6 x1ja2u2z x1afcbsf x78zum5 xdt5ytf x1a2a7pz x6ikm8r x10wlt62 x71s49j x1jx94hy x1qpq9i9 xdney7k xu5ydu1 xt3gfkd x104qc98 x1g2kw80 x16n5opg xl7ujzl xhkep3z x1n7qst7 xh8yej3']")
        transparency_view = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
        transparency_view.screenshot(transparency_image_path)
        Auxiliary.image_compress(transparency_image_path)
        if '年' not in found_date:
            month, day = date_re_no_year.findall(found_date)[0]
            format_found_date = datetime.now().replace(month=int(month), day=int(day), hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        else:
            year, month, day = date_re.findall(found_date)[0]
            format_found_date = datetime.now().replace(year=int(year), month=int(month), day=int(day), hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")

        return profile_photo_url, format_found_date, transparency_image_path, homepage_image_path


class groupMemberDriver(customWebDriver):
    """取得社團成員資料相關docid資源的driver"""

    def _getSource(self, pageURL):
        print("開始動態加載社團成員資料要用的js")
        new_source = ""
        time_pause = 2
        self.driver.get(pageURL)
        # 隱式等待
        self.driver.implicitly_wait(configSetting.implicitly_wait)
        time.sleep(time_pause)
        try:
            banner_element_locator = (By.XPATH,
                                      "//div[@class='xng8ra x6ikm8r x10wlt62 x1n2onr6 xh8yej3 x1ja2u2z x1a2a7pz' and @role='tablist']//descendant::a[@role='tab']")
            banner_element_points = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(banner_element_locator))

            for bep in banner_element_points:
                if bep.text == "用戶":
                    bep.click()
                else:
                    continue
                # hover = ActionChains(driver).move_to_element(bep)
                # hover.perform()

            time.sleep(time_pause)
            new_source = self.driver.page_source
        except Exception as e:
            print("動態加載社團成員資料 js 發生錯誤: ", str(e))
            print("沒有抓到朋友群加載的js,可能是網頁失效或是登入帳號失效導致,直接回傳空字串")
            time.sleep(time_pause)
            return new_source

        if len(new_source) > 0:
            print("有抓到社團成員資料 js")
        else:
            print("沒有抓到社團成員資料 js,回傳空字串")
        time.sleep(time_pause)
        return new_source

    def catchSpecialJsSource(self, pageURL):

        self.driver.get(pageURL)
        # 隱式等待
        self.driver.implicitly_wait(configSetting.implicitly_wait)
        time.sleep(1)
        new_source = self.driver.page_source

        return new_source
