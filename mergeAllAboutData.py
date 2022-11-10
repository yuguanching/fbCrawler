from ioService import writer,reader,parser
from collections import Counter
from helper import Auxiliary
import pandas as pd
import openpyxl
import numpy as np



def mergeAllAboutDataToExcel():

    file_name = "aboutData.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "about"
    wb.save("./output/allAboutData.xlsx")

    jsonArrayData = reader.readInputJson()

    targetNames = jsonArrayData['targetName']

    print(f"開始進行個人關於資料合併,人員列項:{targetNames}")


    allAboutDF = pd.DataFrame()
    about_data_dict_list = []
    for subDir in targetNames:
    #讀取相關的欄位
        data = pd.read_excel(f"./output/{subDir}/{file_name}",sheet_name=None)
        about_data_dict_list.append(data)

    personCount = 1 # 讓返回總表的超連結跳轉的位置可以鎖定當前的人
    for about_data in about_data_dict_list:
        for key,value in about_data.items():
            if key == 'about':
                about_data['about'] = about_data['about'].reindex(['id','姓名','性別','生日','手機','信箱','住址','個人頁連結','學經歷','居住','人際','社群'],axis=1)
                allAboutDF = pd.concat([allAboutDF,about_data['about']],ignore_index=False)
                personCount+=1
            else:
                value.drop('id', inplace=True, axis=1)
                funcStr_col = Auxiliary.make_hyperlink("about","__返回總表__",str(personCount))
                value.insert(len(value.columns),funcStr_col,"")
                writer.pdToExcel(des="./output/allAboutData.xlsx",df=value,sheetName=key,mode='a',indexIsNeed=False,autoFitIsNeed=False)
    
    allAboutDF = allAboutDF.reset_index() #重新定義流水號
    allAboutDF.drop('id', inplace=True, axis=1)
    allAboutDF.drop('index', inplace=True, axis=1)

    for index,row in allAboutDF.iterrows():
        sheet_name = row['姓名'].replace(" ","_")
        if row['學經歷'] != "" and (not pd.isna(row['學經歷'])):
            exp_sheet_name = sheet_name + "_學經歷"
            funcStr = Auxiliary.make_hyperlink(exp_sheet_name,"連結")
            allAboutDF.at[index,'學經歷'] = funcStr
        if row['居住'] != "" and  (not pd.isna(row['居住'])):
            exp_sheet_name = sheet_name + "_居住"
            funcStr = Auxiliary.make_hyperlink(exp_sheet_name,"連結")
            allAboutDF.at[index,'居住'] = funcStr
        if row['人際'] != "" and  (not pd.isna(row['人際'])):
            exp_sheet_name = sheet_name + "_人際"
            funcStr = Auxiliary.make_hyperlink(exp_sheet_name,"連結")
            allAboutDF.at[index,'人際'] = funcStr
        if row['社群'] != "" and  (not pd.isna(row['社群'])):
            exp_sheet_name = sheet_name + "_社群"
            funcStr = Auxiliary.make_hyperlink(exp_sheet_name,"連結")
            allAboutDF.at[index,'社群'] = funcStr

    writer.pdToExcel(des="./output/allAboutData.xlsx",df=allAboutDF,sheetName="about",mode='a',indexIsNeed=False)

    print("合併完成")











if __name__ == "__main__":
    Auxiliary.createIndexExcelAndRead()
    mergeAllAboutDataToExcel()
