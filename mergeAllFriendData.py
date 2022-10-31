
from ioService import writer,reader,parser
from collections import Counter
from helper import Auxiliary
import pandas as pd
import openpyxl
import numpy as np



def mergeAllFriendzoneDataToExcel():
    file_name = "friendzoneData.xlsx"

    jsonArrayData = reader.readInputJson()

    targetNames = jsonArrayData['targetName']
    all_friendzoneData_list = []


    print(f"開始進行朋友與關係人統計資料合併,粉專列項:{targetNames}")

    for subDir in targetNames:

        #讀取相關的欄位
        friendzoneDataDF = pd.read_excel(f"./output/{subDir}/{file_name}",sheet_name="sheet1",usecols="B:L")
        all_friendzoneData_list.append(friendzoneDataDF)


    all_friendzoneData = pd.concat(all_friendzoneData_list).reset_index(drop=True)

    writer.pdToExcel(des='./output/allFriendzoneData.xlsx',df=all_friendzoneData,sheetName="sheet1")    

    print("合併完成")



if __name__ == "__main__":
    Auxiliary.createIndexExcelAndRead()
    mergeAllFriendzoneDataToExcel()