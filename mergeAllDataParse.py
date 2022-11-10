from ioService import writer,reader,parser
from collections import Counter
from helper import Auxiliary
import pandas as pd

def mergeAllDataParseToExcel():
    file_name = "dataParse.xlsx"

    jsonArrayData = reader.readInputJson()

    targetNames = jsonArrayData['targetName']
    all_sharerData_list = []
    all_sharer_list = []
    all_beenSharer_list = []

    print(f"開始進行分享統計資料合併,粉專列項:{targetNames}")

    for subDir in targetNames:

        #讀取相關的欄位
        sharerDataDF = pd.read_excel(f"./output/{subDir}/{file_name}",sheet_name="sharerData",usecols="B:I")
        sharerDF = pd.read_excel(f"./output/{subDir}/{file_name}",sheet_name="sharer",usecols="B:F")
        been_sharerDF = pd.read_excel(f"./output/{subDir}/{file_name}",sheet_name="been_sharer",usecols="B:E")
        all_sharerData_list.append(sharerDataDF)
        all_sharer_list.append(sharerDF)
        all_beenSharer_list.append(been_sharerDF)

    all_sharerData = pd.concat(all_sharerData_list).reset_index(drop=True)
    all_sharer = pd.concat(all_sharer_list).reset_index(drop=True)
    all_beenSharer = pd.concat(all_beenSharer_list).reset_index(drop=True)

    writer.pdToExcel(des='./output/allDataParse.xlsx',df=all_sharerData,sheetName="sharerData")    
    writer.pdToExcel(des='./output/allDataParse.xlsx',df=all_sharer,sheetName="sharer",mode='a')    
    writer.pdToExcel(des='./output/allDataParse.xlsx',df=all_beenSharer,sheetName="been_sharer",mode='a')    


    print("合併完成")


def mergeAllTagToExcel():
    file_name = "tag.xlsx"

    jsonArrayData = reader.readInputJson()

    targetNames = jsonArrayData['targetName']
    all_raw_sentences_list = []
    all_sentences_list = []
    all_words_list = []

    print(f"開始進行分享斷句、斷詞合併,並產生文字雲,粉專列項:{targetNames}")

    for subDir in targetNames:
        rawSentencesDf = pd.read_excel(f"./output/{subDir}/{file_name}",sheet_name="rawSentences",usecols="B")
        sentencesDF = pd.read_excel(f"./output/{subDir}/{file_name}",sheet_name="sentence",usecols="A:B")
        wordsDF = pd.read_excel(f"./output/{subDir}/{file_name}",sheet_name="word",usecols="A:B")
        all_raw_sentences_list.append(rawSentencesDf)
        all_sentences_list.append(sentencesDF)
        all_words_list.append(wordsDF)
    
    all_raw_sentences = pd.concat(all_raw_sentences_list).reset_index(drop=True)
    all_sentences = pd.concat(all_sentences_list)
    all_words = pd.concat(all_words_list)

    all_sentences = all_sentences.groupby('斷句',sort=False,as_index=False).sum()
    all_sentences.sort_values('使用熱度',ascending=False,inplace=True)
    all_sentences.reset_index(drop=True)

    all_words = all_words.groupby('斷詞',sort=False,as_index=False).sum()
    all_words.sort_values('詞頻',ascending=False,inplace=True)
    all_words.reset_index(drop=True)

    writer.pdToExcel(des='./output/allTag.xlsx',df=all_raw_sentences,sheetName="rawSentences")    
    writer.pdToExcel(des='./output/allTag.xlsx',df=all_sentences,sheetName="sentence",indexIsNeed=False,mode='a')    
    writer.pdToExcel(des='./output/allTag.xlsx',df=all_words,sheetName="word",indexIsNeed=False,mode='a')    
    
    print("合併完成")
    print("開始建立全斷詞的文字雲")

    all_words_counter = Counter()
    for index ,row in all_words.iterrows():
        all_words_counter.update({row['斷詞']:row['詞頻']})

    parser.createWordCloud(subDir="",counter=all_words_counter,for_all=True)



if __name__ == '__main__':
    Auxiliary.createIndexExcelAndRead()
    mergeAllDataParseToExcel()
    mergeAllTagToExcel()
