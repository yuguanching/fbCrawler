from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from ioService import writer
import time
import traceback


#**跑截圖的時候請勿晃動畫面,以免截到錯誤的畫面
def CatchScreenshot(driver,url,count,switch,subDir):

    driver.get(url)
    time.sleep(2)
    driver.execute_script("window.scrollTo(0,0)")
    path = ""
    if switch == 0:
        path = "./output/" + subDir + "/img/sharer/" + str(count) + ".png"
        locator = (By.CSS_SELECTOR,"div.x78zum5.xdt5ytf.x10cihs4.x1t2pt76.x1n2onr6.x1ja2u2z > div > div > div")
    else :
        path = "./output/" + subDir + "/img/been_sharer/" + str(count) + ".png"
        locator = (By.CSS_SELECTOR,"div.x78zum5.xdt5ytf.x10cihs4.x1t2pt76.x1n2onr6.x1ja2u2z > div > div")        
    
    try:
        #personal_profile上面的部分截圖
        catchElement = WebDriverWait(driver,10).until(EC.presence_of_element_located(locator))
        #統一暫存到img資料夾,因涉及存檔,故加time.sleep
        catchElement.screenshot(path)
    except:
        writer.writeLogToFile(traceBack=traceback.format_exc())
        print("截圖動作失敗,查看log檔確認原因")

    time.sleep(2)
    return    