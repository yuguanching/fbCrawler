import pandas as pd
import openpyxl
import numpy as np
import configSetting

from ioService import writer, reader, parser
from collections import Counter
from helper import Auxiliary


def mergeAllFriendzoneDataToExcel() -> None:
    file_name = "friendzoneData.xlsx"

    target_names = configSetting.json_array_data['targetName']
    all_friendzone_data_list = []

    print(f"開始進行朋友與關係人統計資料合併,粉專列項:{target_names}")

    for sub_dir in target_names:

        # 讀取相關的欄位
        friendzoneDataDF = pd.read_excel(f"{configSetting.output_root}{sub_dir}/{file_name}", sheet_name="sheet1", usecols="B:L")
        all_friendzone_data_list.append(friendzoneDataDF)

    all_friendzone_data = pd.concat(all_friendzone_data_list).reset_index(drop=True)

    writer.pdToExcel(des=f'{configSetting.output_root}allFriendzoneData.xlsx', df=all_friendzone_data, sheetName="sheet1")

    print("合併完成")


if __name__ == "__main__":
    Auxiliary.createIndexExcelAndRead()
    mergeAllFriendzoneDataToExcel()
