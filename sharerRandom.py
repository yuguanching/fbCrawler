import pandas as pd

from ioService import writer,reader


def sharerPartition() :

    file_name = "dataParse.xlsx"

    # shareDF 透過讀檔取得
    jsonArrayData = reader.readInputJson()

    targetNames = jsonArrayData['targetName']


    for subDir in targetNames:
        print(f"{subDir} 開始以sharer sheet 進行分群")
        #讀取相關的欄位
        sharerDF = pd.read_excel(f"./output/{subDir}/{file_name}",sheet_name="sharer",usecols="B:F")


        # 從第幾筆開始分群,前面的都去掉
        startFromWhere = 50 
        # 每次採樣的數量
        partitionNumber = 50
        if len(sharerDF)>50:
            sharerDF = sharerDF[startFromWhere:]
            df_shuffled=sharerDF.sample(frac=1).reset_index(drop=True)
            
            start = 0
            end = start + partitionNumber
            outputExcel = 0
            while (end < len(df_shuffled)) :
                tempDF = df_shuffled[start:end]
                writer.pdToExcel(des='./output/' + subDir + '/sharerOutput_' + str(outputExcel) + '.xlsx',df=tempDF,sheetName="sheet1")
                start = end
                end = start + partitionNumber
                outputExcel+=1
            
            # 處理最後剩下不滿50個的資料
            if end >= len(df_shuffled):
                end = len(df_shuffled)
                tempDF = df_shuffled[start:end]
                writer.pdToExcel(des='./output/' + subDir + '/sharerOutput_' + str(outputExcel) + '.xlsx',df=tempDF,sheetName="sheet1")

        print(f"{subDir} 分群完成")
    return 



if __name__ == '__main__':
    sharerPartition()