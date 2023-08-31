import pandas as pd
import configSetting

from ioService import writer, reader


def sharerPartition() -> None:

    file_name = "dataParse.xlsx"

    target_names = configSetting.json_array_data['targetName']

    for sub_dir in target_names:
        print(f"{sub_dir} 開始以sharer sheet 進行分群")
        # 讀取相關的欄位
        sharer_df = pd.read_excel(f"{configSetting.output_root}{sub_dir}/{file_name}", sheet_name="sharer", usecols="B:J")

        # 從第幾筆開始分群,前面的都去掉
        start_from_where = 50
        # 每次採樣的數量
        partition_number = 50
        if len(sharer_df) > 50:
            sharer_df = sharer_df[start_from_where:]
            df_shuffled = sharer_df.sample(frac=1).reset_index(drop=True)

            start = 0
            end = start + partition_number
            output_excel = 0
            while (end < len(df_shuffled)):
                temp_df = df_shuffled[start:end]
                writer.pdToExcel(des=f'{configSetting.output_root}' + sub_dir + '/sharerOutput_' +
                                 str(output_excel) + '.xlsx', df=temp_df, sheetName="sheet1")
                start = end
                end = start + partition_number
                output_excel += 1

            # 處理最後剩下不滿50個的資料
            if end >= len(df_shuffled):
                end = len(df_shuffled)
                temp_df = df_shuffled[start:end]
                writer.pdToExcel(des=f'{configSetting.output_root}' + sub_dir + '/sharerOutput_' +
                                 str(output_excel) + '.xlsx', df=temp_df, sheetName="sheet1")

        print(f"{sub_dir} 分群完成")
    return


if __name__ == '__main__':
    sharerPartition()
