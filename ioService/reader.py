import os
import json
import pandas as pd


def readInputJson(target_file="./config/input.json") -> dict:
    has_file = os.path.isfile(target_file)

    if has_file is True:
        with open(target_file, encoding='utf_8') as f:
            json_array_data = json.load(f)
            f.close()
    return json_array_data


def readInputTagSummaryExcel(dir_path: str) -> dict:
    excel_dir_path = dir_path + "tag.xlsx"

    dataframe_from_excel = pd.read_excel(excel_dir_path, sheet_name="word")
    modified_dict = dict()
    for key, values in dataframe_from_excel.to_dict().items():
        modified_dict[key] = list(values.values())
    return modified_dict


def readInputDataParseSummaryExcel(dir_path: str) -> tuple[dict, dict]:
    excel_dir_path = dir_path + "dataParse.xlsx"

    sharer_from_excel = pd.read_excel(excel_dir_path, sheet_name="sharer")
    been_sharer_from_excel = pd.read_excel(excel_dir_path, sheet_name="been_sharer")
    been_sharer_from_excel.dropna(subset=["被分享者"], inplace=True)  # 去掉沒有主要被分享對象者
    sharer_dict = dict()
    been_sharer_dict = dict()
    for key, values in sharer_from_excel.to_dict().items():
        sharer_dict[key] = list(values.values())
    for key, values in been_sharer_from_excel.to_dict().items():
        been_sharer_dict[key] = list(values.values())
    return sharer_dict, been_sharer_dict
