import os
import json


def readInputJson() -> dict:
    target_file = "./config/input.json"
    has_file = os.path.isfile(target_file)

    if has_file is True:
        with open(target_file, encoding='utf_8') as f:
            jsonArrayData = json.load(f)
            f.close()
    return jsonArrayData
