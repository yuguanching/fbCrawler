import pandas as pd
import win32com.client as win32
import os
import traceback
from datetime import datetime


def pdToExcel(des, df: pd.DataFrame, sheetName, mode='w', autoFitIsNeed=True, indexIsNeed=True) -> None:

    file_dir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(file_dir, des)

    # product csv file
    filename_csv = filename.replace(".xlsx", "_" + sheetName + ".csv")
    df.to_csv(filename_csv, index=False, encoding='utf_8_sig')

    if indexIsNeed is True:
        if mode == "w":
            with pd.ExcelWriter(filename, mode=mode, engine='openpyxl') as writer:
                df.to_excel(writer,
                            encoding='utf_8_sig',
                            index_label='id',
                            sheet_name=sheetName)
        else:
            with pd.ExcelWriter(filename, mode=mode, engine='openpyxl', if_sheet_exists="replace") as writer:
                df.to_excel(writer,
                            encoding='utf_8_sig',
                            index_label='id',
                            sheet_name=sheetName)
    else:
        if mode == "w":
            with pd.ExcelWriter(filename, mode=mode, engine='openpyxl') as writer:
                df.to_excel(writer,
                            encoding='utf_8_sig',
                            index=False,
                            sheet_name=sheetName)
        else:
            with pd.ExcelWriter(filename, mode=mode, engine='openpyxl', if_sheet_exists="replace") as writer:
                df.to_excel(writer,
                            encoding='utf_8_sig',
                            index=False,
                            sheet_name=sheetName)

    if autoFitIsNeed is True:
        try:
            excel = win32.DispatchEx('Excel.Application')
            wb = excel.Workbooks.Open(filename)
            ws = wb.Worksheets(sheetName)
            ws.Columns.AutoFit()
            wb.Save()
            excel.Application.Quit()
        except:
            writeLogToFile(traceBack=traceback.format_exc())
            print(f"Some error were founded, failed to formated the excel file : {des}")

        # for column in df:
        #     print(column)
        #     print(df[column].astype(str).map(len))
        #     column_length = max(df[column].astype(str).map(len).max(), len(column))
        #     col_idx = df.columns.get_loc(column)
        #     writer.sheets[sheetName].set_column(col_idx, col_idx, column_length)


def writeLogToFile(traceBack) -> None:
    now = datetime.now()
    now_for_filename = now.strftime("%Y-%m-%d")
    now_for_log = now.strftime("%Y-%m-%d, %H:%M:%S")
    filename = "./log/" + now_for_filename + ".log"
    sourceFile = open(filename, 'a', encoding='utf_8_sig')
    print(f"[{now_for_log}] : {traceBack}", file=sourceFile)
    sourceFile.close()


def writeTempFile(filename, content) -> None:
    f = open("./temp/" + filename + ".txt", "w", encoding='utf_8_sig')
    f.write(content)
    f.close()
