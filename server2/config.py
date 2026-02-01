# 获取当前文件所在的目录
import json
import os

from global_variable import *

current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建相对路径
relative_path = os.path.join(current_dir)

# 读取json文件
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data

# 初始化config.json文件
def init_config():
    path = f'{relative_path}/config.json'

    if not os.path.exists(path):
        try:
            data = []
            data.append({"model":"deepseek-chat",
                         "api_key":"your API key",
                         "model2":"deepseek-chat",
                         "api_key2":"your API key",
                         "api_key3":"your API key",
                         "user_name":"default",
                         "assistant_name":"Bandit"})

            # 打开文件，以写入模式创建文件对象
            with open(f'{relative_path}/config.json', 'w', encoding='utf-8') as file:
                # indent=1 每个层级缩进1个空格
                file.write(json.dumps(data, indent=1, ensure_ascii=False))

            print(f"初始化config.json文件成功!")
        except Exception as e:
            print(f"初始化config.json文件失败!")
            pass

def read_config():
    # 读取config.json文件
    path = f'{relative_path}/config.json'

    if os.path.exists(path):
        try:
            original_data = read_json_file(path)

            model[0] = original_data[0].get('model')
            api_key[0] = original_data[0].get('api_key')
            model2[0] = original_data[0].get('model2')
            api_key2[0] = original_data[0].get('api_key2')
            api_key3[0] = original_data[0].get('api_key3')
            user_name[0] = original_data[0].get('user_name')
            current_assistant[0] = original_data[0].get('assistant_name')

            return original_data
        except Exception as e:
            print(f"读取config.json文件失败!")
            pass
    else:
        return None

# 修改config.json文件
def set_config(data):

    model[0] = data[0].get('model')
    api_key[0] = data[0].get('api_key')
    model2[0] = data[0].get('model2')
    api_key2[0] = data[0].get('api_key2')
    api_key3[0] = data[0].get('api_key3')
    current_assistant[0] = data[0].get('assistant_name')
    user_name[0] = data[0].get('user_name')

    # 打开文件，以写入模式创建文件对象
    with open(f'{relative_path}/config.json', 'w',encoding='utf-8') as file:
        # indent=1 每个层级缩进1个空格
        file.write(json.dumps(data,indent=1,ensure_ascii=False))

    print(f"修改config.json文件成功!\n")
