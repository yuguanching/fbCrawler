import re
import json
import time
import httpx
import asyncio
import urllib.parse
import configSetting
from datetime import datetime
from fake_useragent import UserAgent
from ioService import reader, writer


async def alive_check():
    json_data = configSetting.json_array_data
    targetURLS = json_data["targetURL"]
    targetNames = json_data["targetName"]

    task_list = []
    new_url_list = []
    new_name_list = []

    for url, name in zip(targetURLS, targetNames):
        task_list.append(check(name, url))

    results = await asyncio.gather(*task_list)
    for name, url, is_alive in results:
        if is_alive:
            new_name_list.append(name)
            new_url_list.append(url)
    json_data["targetURL"] = new_url_list
    json_data["targetName"] = new_name_list
    json_obj = json.dumps(json_data, indent=4, ensure_ascii=False)
    with open("./config/input.json", "w", encoding="utf-8") as outfile:
        outfile.write(json_obj)
    configSetting.json_array_data = reader.readInputJson()


async def check(name: str, url: str) -> tuple[str, str, bool]:
    print(f"檢查粉專:{name}")
    url_format = ""
    if "profile.php" in url:
        re_search = re.findall(
            r"https:\/\/www.facebook.com\/profile.php\?id=([0-9]{1,}).*", url)
        parse_name = name.replace("，", "").replace("。", "")
        url_format = f"https://www.facebook.com/people/{urllib.parse.quote_plus(parse_name).replace('+','-')}/{re_search[0]}/"
    else:
        url_format = url
    is_alive = False
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
               'accept-language': 'zh-Hant'}
    headers['ec-ch-ua-platform'] = 'Windows'
    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    headers['sec-fetch-site'] = "same-origin"
    headers['origin'] = "https://www.facebook.com"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url=url_format, headers=headers)
    writer.writeTempFile(filename="wdferggrthht", content=resp.text)
    is_alive = True if name in resp.text else False
    return name, url, is_alive
