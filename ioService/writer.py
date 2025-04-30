import os
import traceback
import pandas as pd
import xlwings as xw
import win32com.client as win32
from helper import Auxiliary
from xlwings import Sheet
from datetime import datetime
from docx.shared import Cm, Inches, Pt, Mm
from docxtpl import DocxTemplate
from docxtpl import InlineImage
from docxtpl import RichText
from ioService import reader


def pdToExcel(des, df: pd.DataFrame, sheetName, mode='w', autoFitIsNeed=True, indexIsNeed=True) -> None:

    file_dir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(file_dir, des)

    # product csv file
    # filename_csv = filename.replace(".xlsx", "_" + sheetName + ".csv")
    # df.to_csv(filename_csv, index=False, encoding='utf_8_sig')

    if indexIsNeed is True:
        if mode == "w":
            with pd.ExcelWriter(filename, mode=mode, engine='openpyxl') as writer:
                df.to_excel(writer,
                            index_label='id',
                            sheet_name=sheetName)
        else:
            with pd.ExcelWriter(filename, mode=mode, engine='openpyxl', if_sheet_exists="replace") as writer:
                df.to_excel(writer,
                            index_label='id',
                            sheet_name=sheetName)
    else:
        if mode == "w":
            with pd.ExcelWriter(filename, mode=mode, engine='openpyxl') as writer:
                df.to_excel(writer,
                            index=False,
                            sheet_name=sheetName)
        else:
            with pd.ExcelWriter(filename, mode=mode, engine='openpyxl', if_sheet_exists="replace") as writer:
                df.to_excel(writer,
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


def writeTempFile(filename, content, mode='w') -> None:
    f = open("./temp/" + filename + ".txt", mode=mode, encoding='utf_8_sig')
    f.write(content)
    f.close()


def writeJsonFile(filename, content) -> None:
    f = open("./temp/" + filename + ".json", "w", encoding='utf_8_sig')
    f.write(content)
    f.close()


def copyFileFromSrcToDst(src: str, dst: str) -> None:
    command = f'copy "{src}" "{dst}"'
    os.system(command)


def updateDataToExcelCertainCell(data: pd.DataFrame, filename: str, sheetname: str, cell_index: str) -> None:
    app = xw.App(visible=False)
    wb = xw.Book(filename)
    ws: Sheet = wb.sheets[sheetname]
    ws.range(cell_index).options(index=False, header=False).value = data

    wb.save()
    wb.close()
    app.quit()


def updateFormulaToExcel(filename: str, sheetname: str, start: int, end: int) -> None:
    app = xw.App(visible=False)
    wb = xw.Book(filename)
    ws: Sheet = wb.sheets[sheetname]
    for i in range(start, end + 1):
        ws.range(f"T{i}").formula = f'=IF($E{i}="V",$E$4,0)+IF($F{i}="V",$F$4,0)+IF($G{i}="V",$G$4,0)+IF($H{i}="V",$H$4,0)+IF($I{i}="V",$I$4,0)+IF($J{i}="V",$J$4,0)+IF($K{i}="V",$K$4,0)+IF($L{i}="V",$L$4,0)+IF($M{i}="V",$M$4,0)+IF($N{i}="V",$N$4,0)+IF($O{i}="V",$O$4,0)+IF($P{i}="V",$P$4,0)+IF($Q{i}="V",$Q$4,0)+IF($R{i}="V",$R$4,0)'
    wb.save()
    wb.close()
    app.quit()


def genernate_abnormal_account_word(account_name: str, profile_url: str, subDir: str, index: int) -> None:
    target_root_path = f".\\output\粉專\\{subDir}\\"
    template_file = ".\\template\\abnormal_account_template.docx"
    output_file = f"{target_root_path}臉書異常帳號分析表_{index}.docx"
    tpl = DocxTemplate(template_file)
    context = dict()
    tag_dict = reader.readInputTagSummaryExcel(target_root_path)
    sharer_dict, been_sharer_dict = reader.readInputDataParseSummaryExcel(target_root_path)
    total_share_count = sum(sharer_dict["分享次數"])
    share_people_count = len(sharer_dict["分享次數"])

    page_name = subDir
    if Auxiliary.is_chinese(account_name):
        format_account_name = RichText()
        format_account_name.add(text=account_name, font="標楷體")
    else:
        format_account_name = RichText()
        format_account_name.add(text=account_name, font="Arial")
    context["account_name"] = format_account_name
    context["abnormal_feature"] = "詳如調查報告、假帳號彙整表"
    pic_url = RichText()
    pic_url.add("帳號個人頁面", url_id=tpl.build_url_id(profile_url))
    context["pic_url"] = pic_url
    context["count"] = format(share_people_count, ',')
    context["hot_word_cloud"] = f"臉書「{page_name}」熱詞分析"
    context["word_cloud_pic"] = InlineImage(tpl, f"{target_root_path}img\\word_cloud\\word_cloud.png", width=Inches(4.0), height=Inches(4.0))
    context["hot_word_order"] = f"臉書粉專「{page_name}」的綜整熱詞排序"

    tag_temp_list = []
    for idx in range(0, 20):
        data = {
            "index": str(idx + 1),
            "word": tag_dict["斷詞"][idx],
            "count": tag_dict["詞頻"][idx],
        }
        remain = idx % 10
        if idx < 10:
            tag_temp_list.append([data])
        else:
            tag_temp_list[remain].append(data)
    context["tag_list"] = tag_temp_list

    context["fake_account_title"] = "由中共網軍創建假帳號散布貼文"
    sharer_concat_list = [f"「{sharer_dict['分享者名稱'][idx]}」({sharer_dict['分享次數'][idx]}次)" for idx in range(0, 10)]
    share_content = (
        f"該粉專貼文總計次{format(total_share_count,',')}次分享，主要導流帳號包括"
        + "、".join(sharer_concat_list)
        + f"等{format(share_people_count,',')}個，該些帳號多使用非本人照片為頭像、帳號簡介及發文使用簡體及繁體中文，研係中共委由兩岸網軍創設大量假帳號進行「協同性造假行為」，頻繁分享貼文至個人專頁或各大臉書社團，且{format(share_people_count,',')}個假帳號中分享次數多集中在前百分之十，後續針對前百分之十的分享帳號清查其他同集團粉絲專頁。"
    )
    context["fake_account_text"] = share_content
    context["been_sharer_title"] = "貼文受眾鎖定泛藍、反綠、國內地方性社團"
    been_sharer_count = len(been_sharer_dict["被分享次數"])
    been_sharer_concat_list = [f"「{been_sharer_dict['被分享者'][idx]}」" for idx in range(0, 20)]
    been_sharer_content = (
        f"該粉專貼文多以反獨、反政府政策為主，且被大量轉傳至"
        + "、".join(been_sharer_concat_list)
        + f"等{been_sharer_count}個臉書社團，顯示其散布對象多係泛藍及地方性社團成員。"
    )
    context["been_sharer_text"] = been_sharer_content
    tpl.render(context)
    tpl.save(output_file)
