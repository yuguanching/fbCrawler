from helper import Auxiliary
from ioService import parser, writer
import pandas as pd
import pprint
import numpy as np
import os

sub_dir = "新聞標題斷詞H1"
file_name_q1 = f"./output/{sub_dir}/q1_excel.xlsx"
file_name_q2 = f"./output/{sub_dir}/q2_excel.xlsx"

filter_str_q1 = "聚焦臺海"
filter_str_q2 = "臺海之聲"
start_date_q1 = "2023-01-01"
end_date_q1 = "2023-03-31"
start_date_q2 = "2023-04-01"
end_date_q2 = "2023-06-30"


def start_tag_mission(df: pd.DataFrame, subDir):
    tag_file = f'./output/{subDir}/tag.xlsx'
    target = df['新聞標題'].tolist()
    tag_raw_df = pd.DataFrame({
        "未處理斷句": target
    })
    tag_raw_df = tag_raw_df.reset_index()  # 重新定義流水號
    tag_raw_df.drop('index', inplace=True, axis=1)
    writer.pdToExcel(des=tag_file, df=tag_raw_df, sheetName="rawSentences")

    parser.buildTag(subDir=subDir, forExtraTagMission=True)


df_q2 = pd.read_excel(file_name_q2, sheet_name="工作表1", usecols="B,E,F,G")  # 選出日期跟標題欄
df_q2.dropna(subset=['新聞標題'], inplace=True)  # 去掉無用標題
df_q2['新聞標題'] = df_q2['新聞標題'].apply(lambda x: pd.NA if filter_str_q2 == x else x).fillna(df_q2['內容概要'])
# df = df[df['新聞標題'].str.contains(filter_str) == False]  # 去掉目標雜訊

df_q1 = pd.read_excel(file_name_q1, sheet_name='工作表1', usecols="B,E,G,H")
df_q1.drop(index=0, inplace=True)
df_q1.rename(columns={'Unnamed: 1': '陸媒'}, inplace=True)
df_q1.rename(columns={'Unnamed: 4': '新聞日期'}, inplace=True)
df_q1.rename(columns={'Unnamed: 6': '新聞標題'}, inplace=True)
df_q1.rename(columns={'Unnamed: 7': '內容概要'}, inplace=True)
df_q1.dropna(subset=['新聞標題'], inplace=True)  # 去掉無用標題
df_q1['新聞標題'] = df_q1['新聞標題'].apply(lambda x: pd.NA if filter_str_q1 == x else x).fillna(df_q1['內容概要'])


#  上半年全部
half_year_df = pd.concat([df_q1, df_q2], axis=0, ignore_index=True)
half_year_df.sort_values('新聞日期', ascending=True, inplace=True)  # 排序
half_year_df['新聞日期'] = half_year_df['新聞日期'].apply(np.int64)
half_year_df['新聞日期'] = half_year_df['新聞日期'].apply(Auxiliary.convert_xls_datetime)  # 調整日期
half_year_df = half_year_df[half_year_df['新聞日期'].isin(pd.date_range(start_date_q1, end_date_q2))]


group_dict = dict(list(half_year_df.groupby('陸媒')))

for media in group_dict:
    df_now = group_dict[media]
    df_now_q1 = df_now[df_now['新聞日期'].isin(pd.date_range(start_date_q1, end_date_q1))]
    df_now_q2 = df_now[df_now['新聞日期'].isin(pd.date_range(start_date_q2, end_date_q2))]
    df_now_h1 = df_now[df_now['新聞日期'].isin(pd.date_range(start_date_q1, end_date_q2))]

    if media == "福建日報報業集團\n(海峽導報)":
        media = "福建日報報業集團"
    q1_dir = f'{sub_dir}/{media}/q1'
    q2_dir = f'{sub_dir}/{media}/q2'
    h1_dir = f'{sub_dir}/{media}/h1'

    os.makedirs(f'./output/{q1_dir}')
    os.makedirs(f'./output/{q2_dir}')
    os.makedirs(f'./output/{h1_dir}')
    start_tag_mission(df=df_now_q1, subDir=q1_dir)
    start_tag_mission(df=df_now_q2, subDir=q2_dir)
    start_tag_mission(df=df_now_h1, subDir=h1_dir)
