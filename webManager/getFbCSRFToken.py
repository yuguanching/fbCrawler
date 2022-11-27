from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from ioService import writer, reader
from helper import Auxiliary
from webManager import webDriver
import time
import os
import traceback
import configSetting

os.environ['WDM_LOG_LEVEL'] = '0'


def getCsrfToken():
    target = None
    target_url = configSetting.jsonArrayData['targetURL']
    count = 0
    # ------------------------Web driver settings-------------------------------------
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument('--ignore-ssl-errors')
    # options.headless = True

    wire_options = {
        'proxy': {
            'no_proxy': 'localhost,127.0.0.1'  # excludes
        }
    }

    params_dict = ""
    cookies_xs = ""
    cookies_cUser = ""
    while True:
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=options, seleniumwire_options=wire_options)
            driver.delete_all_cookies()

            webDriver.loginForSeleniumWire(driver=driver, accountCounter=count, loginURL="https://www.facebook.com")
            driver.get(target_url[0])
            time.sleep(3)

            for req in driver.requests:
                if "graphql" in req.url:
                    target = req
                    break

            cookies_xs = driver.get_cookie('xs')
            cookies_cUser = driver.get_cookie('c_user')

            # driver.quit()

            if target is None:
                count += 1
                if count >= len(target_url):
                    count = 0
                continue
            else:
                params_dict = target.params
                print(f"params from selenium wire : {params_dict}")
                print(cookies_xs)
                print(cookies_cUser)
                return params_dict, cookies_xs, cookies_cUser
        except Exception as e:
            # print(traceback.format_exc())
            count += 1
            if count >= len(target_url):
                count = 0
            continue
        finally:
            driver.close()
            driver.quit()
            driver = None
            time.sleep(2)


if __name__ == "__main__":
    getCsrfToken()
