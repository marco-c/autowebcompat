import os
import json


def get_inconsistencies():
    files = os.listdir('./data/')

    parsed_files = []
    for file in files:
        parts = os.path.splitext(file)[0].split('_')
        info = {
            'id': parts[0],
            'browser': parts[-1],
            'element': '_'.join(parts[1:-1])
        }
        parsed_files.append(info)
    
    print(json.dumps(parsed_files, indent=2))



get_inconsistencies()
