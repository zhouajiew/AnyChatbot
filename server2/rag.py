import json
import os

import requests
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from global_variable import *

# 获取当前文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建相对路径
relative_path = os.path.join(current_dir)

# 读取json文件
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算余弦相似度

    Args:
        vec1: 向量1
        vec2: 向量2

    Returns:
        float: 余弦相似度
    """
    try:
        # 转换为numpy数组
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        # 计算点积
        dot_product = np.dot(vec1, vec2)

        # 计算范数
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        # 计算相似度
        similarity = dot_product / (norm1 * norm2)

        return float(similarity)
    except Exception as e:
        print(f"计算余弦相似度失败: {str(e)}\n")
        return 0.0

# 获取query的embedding
def get_query_embedding(input):
    url = "https://api.siliconflow.cn/v1/embeddings"

    payload = {
        "model": "BAAI/bge-m3",
        "input": input,
        "encoding_format": "float"
    }
    headers = {
        "Authorization": f"Bearer {api_key3[0]}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers, timeout=10)

    embedding_json = json.loads(response.text)

    query_embedding = None

    if hasattr(embedding_json, 'data') and len(embedding_json.data) > 0:
        query_embedding = embedding_json.data[0].embedding
    elif isinstance(embedding_json, dict) and 'data' in embedding_json:
        query_embedding = embedding_json['data'][0]['embedding']
    else:
        print(f"无法解析嵌入向量响应: {embedding_json}\n")

    if query_embedding:
        print(f"成功创建query_embedding!\n")

    return query_embedding

# 搜索rag3文件
def search_from_rag_json3(who, query_embedding):
    path = f"{relative_path}/private/{who}/rag3({current_assistant[0]}).json"

    original_data = []
    new_data = []

    if os.path.exists(path):
        try:
            original_data = read_json_file(path)
        except Exception as e:
            print(f"读取{who}的rag3({current_assistant[0]}).json文件失败!\n")
            pass
    else:
        os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)
        # 打开文件，以写入模式创建文件对象
        with open(f'{relative_path}/private/{who}/rag3({current_assistant[0]}).json', 'w', encoding='utf-8') as file:
            # indent=1 每个层级缩进1个空格
            file.write(json.dumps([], indent=1, ensure_ascii=False))

    for o in original_data:
        o_embedding = o.get("embedding")
        s = _cosine_similarity(query_embedding, o_embedding)

        new_data.append({
            "content":o.get("content"),
            'timestamp':o.get('timestamp'),
            "score":s
        })

    new_data.sort(key=lambda x: x["score"], reverse=True)

    return new_data


# 搜索rag2文件
def search_from_rag_json2(who, query_embedding):
    path = f"{relative_path}/private/{who}/rag2({current_assistant[0]}).json"

    original_data = []
    new_data = []

    if os.path.exists(path):
        try:
            original_data = read_json_file(path)
        except Exception as e:
            print(f"读取{who}的rag2({current_assistant[0]}).json文件失败!\n")
            pass
    else:
        os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)
        # 打开文件，以写入模式创建文件对象
        with open(f'{relative_path}/private/{who}/rag2({current_assistant[0]}).json', 'w', encoding='utf-8') as file:
            # indent=1 每个层级缩进1个空格
            file.write(json.dumps([], indent=1, ensure_ascii=False))

    for o in original_data:
        o_embedding = o.get("embedding")
        s = _cosine_similarity(query_embedding, o_embedding)

        new_data.append({
            "content":o.get("content"),
            "score":s
        })

    new_data.sort(key=lambda x: x["score"], reverse=True)

    return new_data


# 搜索rag文件
def search_from_rag_json(who, query_embedding):
    path = f"{relative_path}/private/{who}/rag({current_assistant[0]}).json"

    original_data = []
    new_data = []

    if os.path.exists(path):
        try:
            original_data = read_json_file(path)
        except Exception as e:
            print(f"读取{who}的rag({current_assistant[0]}).json文件失败!\n")
            pass
    else:
        os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)
        # 打开文件，以写入模式创建文件对象
        with open(f'{relative_path}/private/{who}/rag({current_assistant[0]}).json', 'w', encoding='utf-8') as file:
            # indent=1 每个层级缩进1个空格
            file.write(json.dumps([], indent=1, ensure_ascii=False))

    for o in original_data:
        o_embedding = o.get("embedding")
        s = _cosine_similarity(query_embedding, o_embedding)

        new_data.append({
            "timestamp":o.get("timestamp"),
            "user_content":o.get("user_content"),
            "assistant_content":o.get("assistant_content"),
            "score":s
        })

    new_data.sort(key=lambda x: x["score"], reverse=True)

    return new_data

# 将重要信息的概括写入到rag3中
def write_in_rag3(who, data):
    path = f"{relative_path}/private/{who}/rag3({current_assistant[0]}).json"

    original_data = []

    if os.path.exists(path):
        try:
            original_data = read_json_file(path)
        except Exception as e:
            print(f"读取{who}的rag3({current_assistant[0]}).json文件失败!\n")
            pass
    else:
        os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)

    original_data.append(data)

    # 考虑到不应让文件太大，只取最新5000条
    if len(original_data) > 5000:
        original_data = original_data[-5000:]

    rag_num = len(original_data)

    with open(path, 'w', encoding='utf-8') as file:
        # indent=1 每个层级缩进1个空格
        file.write(json.dumps(original_data, indent=1, ensure_ascii=False))

    print(f"写入{who}的rag3({current_assistant[0]}).json文件成功!\n")
    print(f"当前已完成的rag数量为{rag_num}\n")

# 将重要信息的概括写入到rag2中
def write_in_rag2(who, data):
    path = f"{relative_path}/private/{who}/rag2({current_assistant[0]}).json"

    original_data = []

    if os.path.exists(path):
        try:
            original_data = read_json_file(path)
        except Exception as e:
            print(f"读取{who}的rag2({current_assistant[0]}).json文件失败!\n")
            pass
    else:
        os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)

    original_data.append(data)

    # 考虑到不应让文件太大，只取最新5000条
    if len(original_data) > 5000:
        original_data = original_data[-5000:]

    rag_num = len(original_data)

    with open(path, 'w', encoding='utf-8') as file:
        # indent=1 每个层级缩进1个空格
        file.write(json.dumps(original_data, indent=1, ensure_ascii=False))

    print(f"写入{who}的rag2({current_assistant[0]}).json文件成功!\n")
    print(f"当前概括的rag数量为{rag_num}\n")

# 写入到rag中
def write_in_rag(who, data):
    path = f"{relative_path}/private/{who}/rag({current_assistant[0]}).json"

    original_data = []

    if os.path.exists(path):
        try:
            original_data = read_json_file(path)
        except Exception as e:
            print(f"读取{who}的rag({current_assistant[0]}).json文件失败!\n")
            pass
    else:
        os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)

    original_data.append(data)

    # 考虑到不应让文件太大，只取最新5000条
    if len(original_data) > 5000:
        original_data = original_data[-5000:]

    rag_num = len(original_data)

    with open(path, 'w', encoding='utf-8') as file:
        # indent=1 每个层级缩进1个空格
        file.write(json.dumps(original_data, indent=1, ensure_ascii=False))

    print(f"写入{who}的rag({current_assistant[0]}).json文件成功!\n")
    print(f"关于{who}的rag数量为{rag_num}\n")

# 构建语义查询结果
def generate_rag_content(num, rag_results):

    rag_content_part1 = ""

    for idx, m in enumerate(rag_results):
        if idx != len(rag_results) - 1:
            rag_content_part1 += f"对话{idx + num + 1}:\n用户发送该消息的时间为:{m['timestamp']}\n用户的消息:\n{m['user_content']}\n\n"
        else:
            rag_content_part1 += f"对话{idx + num + 1}:\n用户发送该消息的时间为:{m['timestamp']}\n用户的消息:\n{m['user_content']}"

    return rag_content_part1
