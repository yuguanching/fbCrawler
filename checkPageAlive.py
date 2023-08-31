import grequests
import requests
import json
import configSetting
import time

from datetime import datetime
from fake_useragent import UserAgent
from ioService import reader, writer


page_dict = reader.readInputJson(target_file=f"{configSetting.output_root}page_check_list.json")
names = page_dict['targetName']
urls = page_dict['targetURL']

dead_list = []
alive_dict = {
    "targetName": list(),
    "targetURL": list()
}
fake_user_agent = UserAgent()
headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
           'accept-language': 'en'}
headers['ec-ch-ua-platform'] = 'Windows'
headers['User-Agent'] = str(fake_user_agent.chrome)
headers['sec-fetch-site'] = "same-origin"
headers['origin'] = "https://www.facebook.com"
for i, (name, url) in enumerate(zip(names, urls)):
    resp = requests.get(url=urls[i], headers=headers)
    if names[i] in resp.text:
        alive_dict['targetName'].append(names[i])
        alive_dict['targetURL'].append(urls[i])
        continue
    else:
        dead_list.append(names[i])
    resp.close()
    time.sleep(1)

print(f"確認已被封號的粉專清單: {dead_list}")
writer.writeTempFile("dead_list", f"[{datetime.now()}]: {dead_list}", mode='a')
with open(f"{configSetting.output_root}page_check_list.json", 'w', newline='', encoding='utf_8') as jsonfile:
    json.dump(alive_dict, jsonfile, ensure_ascii=False)
print("存活清單更新完成")
