import pandas as pd
import openpyxl
import numpy as np
import configSetting

from ioService import writer, reader, parser
from collections import Counter
from helper import Auxiliary


def mergeAllAboutDataToExcel() -> None:

    file_name = "aboutData.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "about"
    wb.save("./output/allAboutData.xlsx")

    target_names = configSetting.json_array_data['targetName']

    print(f"開始進行個人關於資料合併,人員列項:{target_names}")

    all_about_df = pd.DataFrame()
    about_data_dict_list = []
    for sub_dir in target_names:
        # 讀取相關的欄位
        data = pd.read_excel(f"./output/{sub_dir}/{file_name}", sheet_name=None)
        about_data_dict_list.append(data)

    person_count = 1  # 讓返回總表的超連結跳轉的位置可以鎖定當前的人

    about_data: dict
    for about_data in about_data_dict_list:
        for key, value in about_data.items():
            if key == 'about':
                about_data['about'] = about_data['about'].reindex(
                    ['id', '姓名', '性別', '生日', '手機', '信箱', '住址', '個人頁連結', '學經歷', '居住', '人際', '社群'], axis=1)
                all_about_df = pd.concat([all_about_df, about_data['about']], ignore_index=False)
                person_count += 1
            else:
                value.drop('id', inplace=True, axis=1)
                func_str_col = Auxiliary.makeHyperlink("about", "__返回總表__", str(person_count))
                value.insert(len(value.columns), func_str_col, "")
                writer.pdToExcel(des="./output/allAboutData.xlsx", df=value, sheetName=key, mode='a', indexIsNeed=False, autoFitIsNeed=False)

    all_about_df = all_about_df.reset_index()  # 重新定義流水號
    all_about_df.drop('id', inplace=True, axis=1)
    all_about_df.drop('index', inplace=True, axis=1)

    for index, row in all_about_df.iterrows():
        sheet_name = row['姓名'].replace(" ", "_")
        if row['學經歷'] != "" and (not pd.isna(row['學經歷'])):
            exp_sheet_name = sheet_name + "_學經歷"
            func_str = Auxiliary.makeHyperlink(exp_sheet_name, "連結")
            all_about_df.at[index, '學經歷'] = func_str
        if row['居住'] != "" and (not pd.isna(row['居住'])):
            exp_sheet_name = sheet_name + "_居住"
            func_str = Auxiliary.makeHyperlink(exp_sheet_name, "連結")
            all_about_df.at[index, '居住'] = func_str
        if row['人際'] != "" and (not pd.isna(row['人際'])):
            exp_sheet_name = sheet_name + "_人際"
            func_str = Auxiliary.makeHyperlink(exp_sheet_name, "連結")
            all_about_df.at[index, '人際'] = func_str
        if row['社群'] != "" and (not pd.isna(row['社群'])):
            exp_sheet_name = sheet_name + "_社群"
            func_str = Auxiliary.makeHyperlink(exp_sheet_name, "連結")
            all_about_df.at[index, '社群'] = func_str

    writer.pdToExcel(des="./output/allAboutData.xlsx", df=all_about_df, sheetName="about", mode='a', indexIsNeed=False)

    print("合併完成")


if __name__ == "__main__":
    Auxiliary.createIndexExcelAndRead()
    mergeAllAboutDataToExcel()
