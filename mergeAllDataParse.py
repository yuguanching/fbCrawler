import pandas as pd
import configSetting

from ioService import writer, reader, parser
from collections import Counter
from helper import Auxiliary


def mergeAllDataParseToExcel() -> None:
    file_name = "dataParse.xlsx"

    target_names = configSetting.json_array_data['targetName']
    all_sharer_data_list = []
    all_sharer_list = []
    all_been_sharer_list = []

    print(f"開始進行分享統計資料合併,粉專列項:{target_names}")

    for sub_dir in target_names:

        # 讀取相關的欄位
        sharer_data_df = pd.read_excel(f"{configSetting.output_root}{sub_dir}/{file_name}", sheet_name="sharerData", usecols="B:K")
        sharer_df = pd.read_excel(f"{configSetting.output_root}{sub_dir}/{file_name}", sheet_name="sharer", usecols="B:J")
        been_sharer_df = pd.read_excel(f"{configSetting.output_root}{sub_dir}/{file_name}", sheet_name="been_sharer", usecols="B:F")
        all_sharer_data_list.append(sharer_data_df)
        all_sharer_list.append(sharer_df)
        all_been_sharer_list.append(been_sharer_df)

    all_sharer_data = pd.concat(all_sharer_data_list).reset_index(drop=True)
    all_sharer = pd.concat(all_sharer_list).reset_index(drop=True)
    all_been_sharer = pd.concat(all_been_sharer_list).reset_index(drop=True)

    writer.pdToExcel(des=f'{configSetting.output_root}allDataParse.xlsx', df=all_sharer_data, sheetName="sharerData")
    writer.pdToExcel(des=f'{configSetting.output_root}allDataParse.xlsx', df=all_sharer, sheetName="sharer", mode='a')
    writer.pdToExcel(des=f'{configSetting.output_root}allDataParse.xlsx', df=all_been_sharer, sheetName="been_sharer", mode='a')

    print("合併完成")


def mergeAllTagToExcel() -> None:
    file_name = "tag.xlsx"

    target_names = configSetting.json_array_data['targetName']
    all_raw_sentences_list = []
    all_sentences_list = []
    all_words_list = []

    print(f"開始進行分享斷句、斷詞合併,並產生文字雲,粉專列項:{target_names}")

    for sub_dir in target_names:
        rawSentencesDf = pd.read_excel(f"{configSetting.output_root}{sub_dir}/{file_name}", sheet_name="rawSentences", usecols="B")
        sentencesDF = pd.read_excel(f"{configSetting.output_root}{sub_dir}/{file_name}", sheet_name="sentence", usecols="A:B")
        wordsDF = pd.read_excel(f"{configSetting.output_root}{sub_dir}/{file_name}", sheet_name="word", usecols="A:B")
        all_raw_sentences_list.append(rawSentencesDf)
        all_sentences_list.append(sentencesDF)
        all_words_list.append(wordsDF)

    all_raw_sentences = pd.concat(all_raw_sentences_list).reset_index(drop=True)
    all_sentences = pd.concat(all_sentences_list)
    all_words = pd.concat(all_words_list)

    all_sentences = all_sentences.groupby('斷句', sort=False, as_index=False).sum()
    all_sentences.sort_values('使用熱度', ascending=False, inplace=True)
    all_sentences.reset_index(drop=True)

    all_words = all_words.groupby('斷詞', sort=False, as_index=False).sum()
    all_words.sort_values('詞頻', ascending=False, inplace=True)
    all_words.reset_index(drop=True)

    writer.pdToExcel(des=f'{configSetting.output_root}allTag.xlsx', df=all_raw_sentences, sheetName="rawSentences")
    writer.pdToExcel(des=f'{configSetting.output_root}allTag.xlsx', df=all_sentences, sheetName="sentence", indexIsNeed=False, mode='a')
    writer.pdToExcel(des=f'{configSetting.output_root}allTag.xlsx', df=all_words, sheetName="word", indexIsNeed=False, mode='a')

    print("合併完成")
    print("開始建立全斷詞的文字雲")

    all_words_counter = Counter()
    for index, row in all_words.iterrows():
        all_words_counter.update({row['斷詞']: row['詞頻']})

    parser.createWordCloud(subDir="", counter=all_words_counter, forAll=True)


if __name__ == '__main__':
    Auxiliary.createIndexExcelAndRead()
    mergeAllDataParseToExcel()
    mergeAllTagToExcel()
