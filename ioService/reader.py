import os
import json

def readInputJson():
    target_file = "./config/input.json"
    hasFile  = os.path.isfile(target_file)

    if hasFile is True :
        with open(target_file,encoding='utf_8') as f :
                    jsonArrayData = json.load(f)
                    f.close()
    return jsonArrayData