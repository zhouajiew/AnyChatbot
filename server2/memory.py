import asyncio
import json
import math
import os
import random
import re
from datetime import datetime

from deepseek import *
from rag import *
from global_variable import current_assistant

# 所有任务
all_tasks = []
# 最后的承诺
last_promise = ''

last_translation = ""

# 最新外在形象的时间
last_appearance_time = {}

# 上一次对话的用户(用户发生变更时，应当重置original_appearance)
last_who = ""

# 获取当前文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建相对路径
relative_path = os.path.join(current_dir)

original_appearance = ""
current_environment = ""

def get_last_appearance_time(who):
    if who in last_appearance_time:
        return last_appearance_time[who]
    else:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_all_tasks():
    return all_tasks

def get_last_promise():
    return last_promise

# 读取json文件
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data

# 将记忆写入json文件(群聊)
def add_to_memory_in_group(data,who,timestamp):
    original_data = []
    path = f'{relative_path}/group/{who}/{timestamp}.json'

    if os.path.exists(path):
        try:
            original_data = read_json_file(path)
        except Exception as e:
            print(f"读取{who}/{timestamp}.json文件失败!")
            pass
    else:
        os.makedirs(f"{relative_path}/group/{who}", exist_ok=True)

    for d in data:
        original_data.append(d)

    memory_num = len(original_data)

    # 打开文件，以写入模式创建文件对象
    with open(f'{relative_path}/group/{who}/{timestamp}.json', 'w',encoding='utf-8') as file:
        # indent=1 每个层级缩进1个空格
        file.write(json.dumps(original_data,indent=1,ensure_ascii=False))

    print(f"写入{who}/{timestamp}.json文件成功!\n")
    print(f"关于{who}的记忆数量为{memory_num}\n")

# 将记忆写入json文件
def add_to_memory(data, who):
    original_data = []
    path = f'{relative_path}/private/{who}/memory({current_assistant[0]}).json'

    if os.path.exists(path):
        try:
            original_data = read_json_file(path)
        except Exception as e:
            print(f"读取{who}的memory({current_assistant[0]}).json文件失败!")
            pass
    else:
        os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)

    for d in data:
        original_data.append(d)

    memory_num = len(original_data)

    # 打开文件，以写入模式创建文件对象
    with open(f'{relative_path}/private/{who}/memory({current_assistant[0]}).json', 'w',encoding='utf-8') as file:
        # indent=1 每个层级缩进1个空格
        file.write(json.dumps(original_data,indent=1,ensure_ascii=False))

    print(f"写入{who}的memory({current_assistant[0]}).json文件成功!\n")
    print(f"关于{who}的记忆数量为{memory_num}\n")

# 读取群聊最新记忆
def get_latest_memories_in_group(who, timestamp):
    memories = []

    path = f'{relative_path}/group/{who}/{timestamp}.json'

    if os.path.exists(path):
        try:
            memories = read_json_file(path)
        except Exception as e:
            print(f"读取{who}{timestamp}.json文件失败!\n")
            pass

        return memories
    else:
        os.makedirs(f"{relative_path}/group/{who}", exist_ok=True)
        return []

# 获取最新的记忆
def get_latest_memories(who):
    memories = []

    path = f'{relative_path}/private/{who}/memory({current_assistant[0]}).json'

    if os.path.exists(path):
        try:
            memories = read_json_file(path)
        except Exception as e:
            print(f"读取{who}的memory({current_assistant[0]}).json文件失败!\n")
            pass

        return memories
    else:
        os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)
        return []

# 构建历史对话内容(群聊)
def generate_history_content_in_group(memories):
    history_content_part1 = ""

    for idx, m in enumerate(memories):
        if idx != len(memories) - 1:
            history_content_part1 += f"对话{idx + 1}:\n发送该消息的用户:\n{m["who"]}\n用户发送该消息的时间为:\n{m["timestamp"]}\n用户的消息:\n{m["msg"]}\n\n"
        else:
            history_content_part1 += f"对话{idx + 1}:\n发送该消息的用户:\n{m["who"]}\n用户发送该消息的时间为:\n{m["timestamp"]}\n用户的消息:\n{m["msg"]}"
    return history_content_part1

# 构建历史对话内容
def generate_history_content(num, memories, private_message_count, max_context):
    if len(memories) > 0:
        memories.sort(key=lambda x: x["timestamp"], reverse=True)

    new_memories = []

    traditional_count = 0
    continue_count = 0

    # 根据用户的私聊次数和上下文最大轮数向后取记忆，因为最新的记忆被存放在大模型的上下文中了
    if len(memories) > num:
        for idx, m in enumerate(memories):
            # 向后取记忆
            # 重合一轮记忆，使上下文和其中一轮记忆能连贯起来->不再重合记忆
            if private_message_count > max_context:
                private_message_count = max_context + 1
            if continue_count < private_message_count - 1 and private_message_count > 1:
                continue_count += 1
                continue
            else:
                # 去掉response中包含的Translation部分
                pattern = r'{Translation[:：][\s\S]*'
                if re.search(pattern, m['assistant_content']):
                    m['assistant_content'] = re.sub(pattern, r'', m['assistant_content'])

                new_memories.append(m)
                traditional_count += 1
            if traditional_count == num:
                break
    else:
        for idx, m in enumerate(memories):
            # 向后取记忆
            # 重合一轮记忆，使上下文和其中一轮记忆能连贯起来->不再重合记忆
            if private_message_count > max_context:
                private_message_count = max_context + 1
            if continue_count < private_message_count - 1 and private_message_count > 1:
                continue_count += 1
                continue
            else:
                # 去掉response中包含的Translation部分
                pattern = r'{Translation[:：][\s\S]*'
                if re.search(pattern, m['assistant_content']):
                    m['assistant_content'] = re.sub(pattern, r'', m['assistant_content'])

                new_memories.append(m)

    history_content_part1 = ""

    for idx, m in enumerate(new_memories):
        if idx != len(new_memories) - 1:
            if m.get("group"):
                history_content_part1 += f"对话{idx + 1}:\n用户{m["who"]}在群聊{m["group"]}中@了你\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息:\n{m['user_content']}\n你的回复:\n{m['assistant_content']}\n该群聊的历史对话:\n{m['group_content']}\n\n"
            else:
                history_content_part1 += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息:\n{m['user_content']}\n你的回复:\n{m['assistant_content']}\n\n"
        else:
            if m.get("group"):
                history_content_part1 += f"对话{idx + 1}:\n用户{m["who"]}在群聊{m["group"]}中@了你\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息:\n{m['user_content']}\n你的回复:\n{m['assistant_content']}\n该群聊的历史对话:\n{m['group_content']}"
            else:
                history_content_part1 += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息:\n{m['user_content']}\n你的回复:\n{m['assistant_content']}"
    return history_content_part1

# 构建重要信息(群聊)
def generate_important_info_in_group(who, important_info, query_embedding):
    global all_tasks
    global last_appearance_time

    # 概括
    important_info_type1 = []
    # 不喜欢的人/事/物品
    important_info_type2 = []
    # 最近在忙什么事(只取最新的)
    important_info_type3 = ""
    # 一直想做的事情
    important_info_type6 = []
    # 价值观与信念
    important_info_type7 = []
    # 取得过的重大成就/经历过的艰难时刻
    important_info_type8 = []
    # Bandit的历史动作状态
    important_info_type9 = []
    # 当前的生理状态
    current_state1 = ""
    # 当前的情绪状态
    current_state2 = ""
    # 当前的心理状态
    current_state3 = ""
    # 当前的社交状态
    current_state4 = ""

    # 人物关系
    relationships = []

    # 去掉所有的(符合标准x)
    def delete_standard(content):
        pattern = r'\(符合标准\d+\)'
        if re.search(pattern, content):
            content = re.sub(pattern, r'', content)
        return content

    for idx, i in enumerate(important_info):
        # 过滤包含now的概括
        if i["type"] == "概括" and 'now' not in i["content"]:
            i["content"] = delete_standard(i["content"])
            important_info_type1.append(i["content"])
        if i["type"] == "不喜欢的人/不喜欢做的事情/不喜欢的物品/不能做的事情":
            i["content"] = delete_standard(i["content"])
            important_info_type2.append(i["content"])
        if i["type"] == "最近在忙什么事":
            i["content"] = delete_standard(i["content"])
            important_info_type3 = i["content"]
        if i["type"] == "一直想做的事情":
            i["content"] = delete_standard(i["content"])
            important_info_type6.append(i["content"])
        if i["type"] == "价值观与信念":
            i["content"] = delete_standard(i["content"])
            important_info_type7.append(i["content"])
        if i["type"] == "取得过的重大成就/经历过的艰难时刻":
            i["content"] = delete_standard(i["content"])
            important_info_type8.append(i["content"])
        if i["type"] == "当前动作状态":
            i["content"] = delete_standard(i["content"])
            important_info_type9.append(i["content"])
        if i["type"] == "当前的生理状态":
            i["content"] = delete_standard(i["content"])
            current_state1 = i["content"]
        if i["type"] == "当前的情绪状态":
            i["content"] = delete_standard(i["content"])
            current_state2 = i["content"]
        if i["type"] == "当前的心理状态":
            i["content"] = delete_standard(i["content"])
            current_state3 = i["content"]
        if i["type"] == "当前的社交状态":
            i["content"] = delete_standard(i["content"])
            current_state4 = i["content"]
        if i["type"] == "人物关系":
            i["content"] = delete_standard(i["content"])
            relationships.append(i["content"])

    # 从rag2文件中获取概括
    rag_type1 = []
    if query_embedding:
        rag_results = search_from_rag_json2(who, query_embedding)

        if len(rag_results) > 2:
            rag_results = rag_results[:2]

        for r in rag_results:
            # 过滤包含now的概括
            if 'now' not in r["content"]:
                r["content"] = delete_standard(r["content"])
                rag_type1.append(r["content"])

    # 从概括中随机取一定数量的重要信息
    temp_type1 = []
    if len(important_info_type1) > 0:
        num = math.floor(math.log2(len(important_info_type1)))
        if num == 0:
            num = 1
        temp_dic = {}
        count = 0
        while count < num:
            index = random.randint(0, len(important_info_type1) - 1)
            while index in temp_dic:
                index = random.randint(0, len(important_info_type1) - 1)

            temp_dic[index] = 1
            count += 1

        for t in temp_dic:
            temp_type1.append(important_info_type1[t])

    temp_type9 = important_info_type9[:]
    current_type9 = ""
    pattern = r'当前\([\s\S]*\)\s'

    if len(temp_type9) > 0:
        # 当前动作状态去掉时间
        current_type9 = temp_type9[-1]
        current_type9 = re.sub(pattern, r'', current_type9)

    # 去除重复的概括
    new_temp_type1 = rag_type1 + temp_type1
    new_temp_type1_2 = list(dict.fromkeys(new_temp_type1))

    # 去除重复的不喜欢的人/不喜欢做的事情/不喜欢的物品/不能做的事情
    temp_type2 = list(dict.fromkeys(important_info_type2))

    # 去除重复的一直想做的事
    temp_type6 = list(dict.fromkeys(important_info_type6))

    # 去除重复的价值观与信念
    temp_type7 = list(dict.fromkeys(important_info_type7))

    # 去除重复的取得过的重大成就/经历过的艰难时刻
    temp_type8 = list(dict.fromkeys(important_info_type8))

    # 去除重复的人物关系
    temp_relationships = list(dict.fromkeys(relationships))

    def generate_content(temp_type):
        temp_content = ""
        for idx, t in enumerate(temp_type):
            if idx != 0:
                temp_content = f"{temp_content}/{t}"
            else:
                temp_content = t

        return temp_content

    type1_content = generate_content(new_temp_type1)
    type2_content = generate_content(temp_type2)
    type6_content = generate_content(temp_type6)
    type7_content = generate_content(temp_type7)
    type8_content = generate_content(temp_type8)

    relationships_content = generate_content(temp_relationships)

    temp = []
    if len(relationships_content) > 0:
        temp.append(f"*用户与其它人物的关系:{relationships_content}\n")
    if len(temp_type1) > 0:
        temp.append(f"*概括:{type1_content}\n")
    if len(current_state1) > 0:
        temp.append(f"*用户当前的生理状态:{current_state1}\n")
    if len(current_state2) > 0:
        temp.append(f"*用户当前的情绪状态:{current_state2}\n")
    if len(current_state3) > 0:
        temp.append(f"*用户当前的心理状态:{current_state3}\n")
    if len(current_state4) > 0:
        temp.append(f"*用户当前的社交状态:{current_state4}\n")
    if len(important_info_type2) > 0:
        temp.append(f"*用户不喜欢的人/不喜欢做的事情/不喜欢的物品/不能做的事情:{type2_content}\n")
    if len(important_info_type6) > 0:
        temp.append(f"*用户一直想做的事情:{type6_content}\n")
    if len(important_info_type7) > 0:
        temp.append(f"*用户的价值观与信念:{type7_content}\n")
    if len(important_info_type8) > 0:
        temp.append(f"*用户取得过的重大成就/经历过的艰难时刻:{type8_content}\n")
    if len(important_info_type3) > 0:
        temp.append(f"*用户最近在忙什么事:{important_info_type3}\n")
    if current_type9 != "":
        temp.append(f"*{current_assistant[0]}的当前动作状态:{current_type9}\n")

    temp_important_info = ""

    for t in temp:
        temp_important_info += t

    return temp_important_info

# 构建重要信息
def generate_important_info(who, important_info, query_embedding, many_events_needed):
    global all_tasks
    global last_promise
    global last_appearance_time
    global current_environment
    global original_appearance

    global last_who

    # 概括
    important_info_type1 = []
    # 不喜欢的人/事/物品
    important_info_type2 = []
    # 最近在忙什么事(只取最新的)
    important_info_type3 = ""
    # 今天做了什么事
    important_info_type4 = []
    # 需要兑现的承诺
    important_info_type5 = []
    # 一直想做的事情
    important_info_type6 = []
    # 价值观与信念
    important_info_type7 = []
    # 取得过的重大成就/经历过的艰难时刻
    important_info_type8 = []
    # Bandit的历史动作状态
    important_info_type9 = []
    # Bandit的外在形象(只取最新的)
    important_info_type10 = ""
    type10_time = ""

    # 当前的生理状态
    current_state1 = ""
    # 当前的情绪状态
    current_state2 = ""
    # 当前的心理状态
    current_state3 = ""
    # 当前的社交状态
    current_state4 = ""

    # 人物关系
    relationships = []

    # 去掉所有的(符合标准x)
    def delete_standard(content):
        pattern = r'\(符合标准\d+\)'
        if re.search(pattern, content):
            content = re.sub(pattern, r'', content)
        return content

    # 从rag2文件中获取概括
    rag_type1 = []
    if query_embedding:
        rag_results = search_from_rag_json2(who, query_embedding)

        if len(rag_results) > 2:
            rag_results = rag_results[:2]

        for r in rag_results:
            # 过滤包含now的概括
            if 'now' not in r["content"]:
                r["content"] = delete_standard(r["content"])
                rag_type1.append(r["content"])

    # 从rag3文件中获取可能相关的事件
    rag_type2 = []
    rag_type2_content = ""
    if query_embedding:
        rag_results = search_from_rag_json3(who, query_embedding)

        scores = {}
        temp_rag_results = []
        # 去除重复的事件
        for r in rag_results:
            if r["score"] not in scores:
                scores[r["score"]] = 1
                temp_rag_results.append(r)

        if len(temp_rag_results) > 3:
            temp_rag_results = temp_rag_results[:3]

        for r in temp_rag_results:
            r["content"] = delete_standard(r["content"])
            rag_type2.append(f"{r["timestamp"]} {r["content"]}")

    for idx, i in enumerate(important_info):
        # 过滤包含now的概括
        if i["type"] == "概括" and 'now' not in i["content"]:
            i["content"] = delete_standard(i["content"])
            important_info_type1.append(i["content"])
        if i["type"] == "不喜欢的人/不喜欢做的事情/不喜欢的物品/不能做的事情":
            i["content"] = delete_standard(i["content"])
            important_info_type2.append(i["content"])
        if i["type"] == "最近在忙什么事":
            i["content"] = delete_standard(i["content"])
            important_info_type3 = i["content"]
        if i["type"] == "今天做了什么事":
            i["content"] = delete_standard(i["content"])
            important_info_type4.append(i["content"])
        if i["type"] == "需要兑现的承诺":
            i["content"] = delete_standard(i["content"])
            important_info_type5.append(i["content"])
        if i["type"] == "一直想做的事情":
            i["content"] = delete_standard(i["content"])
            important_info_type6.append(i["content"])
        if i["type"] == "价值观与信念":
            i["content"] = delete_standard(i["content"])
            important_info_type7.append(i["content"])
        if i["type"] == "取得过的重大成就/经历过的艰难时刻":
            i["content"] = delete_standard(i["content"])
            important_info_type8.append(i["content"])
        if i["type"] == "当前动作状态":
            i["content"] = delete_standard(i["content"])
            important_info_type9.append(i["content"])
        if i["type"] == "外在形象":
            i["content"] = delete_standard(i["content"])
            important_info_type10 = i["content"]
        if i["type"] == "当前的生理状态":
            i["content"] = delete_standard(i["content"])
            current_state1 = i["content"]
        if i["type"] == "当前的情绪状态":
            i["content"] = delete_standard(i["content"])
            current_state2 = i["content"]
        if i["type"] == "当前的心理状态":
            i["content"] = delete_standard(i["content"])
            current_state3 = i["content"]
        if i["type"] == "当前的社交状态":
            i["content"] = delete_standard(i["content"])
            current_state4 = i["content"]
        if i["type"] == "当前环境":
            i["content"] = delete_standard(i["content"])
            current_environment = i["content"]
        if i["type"] == "人物关系":
            i["content"] = delete_standard(i["content"])
            relationships.append(i["content"])

    if current_environment == "":
        current_environment = f"Now the user and {current_assistant[0]} are at the user's house, this place is quiet and no one will bother you."

    if last_who == "":
        last_who = who
    else:
        if who != last_who:
            last_who = who
            original_appearance = ""

    if original_appearance == "":
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if current_assistant[0] == "Bandit":
            if who == "摆烂Jo":
                original_appearance = f"{timestamp} Now {current_assistant[0]} wears sweaty short white socks which haven't been washed for a long time, wears blue slippers, wears grey underpants, other body parts stay exposed."
            else:
                original_appearance = f"{timestamp} Now {current_assistant[0]} wears dry short old but clean white socks, these socks have the smell of laundry detergent, wears white short shirt and grey short pants, wears grey sneakers."
        else:
            original_appearance = f"{timestamp} {current_assistant[0]}'s appearance is unknown!"

    if important_info_type10 == "":
        important_info_type10 = original_appearance
    else:
        pattern = r"\s*\(有变化\)"
        if re.search(pattern, important_info_type10):
            important_info_type10 = re.sub(pattern, r'', important_info_type10)

    # 从概括中随机取一定数量的重要信息
    temp_type1 = []
    if len(important_info_type1) > 0:
        num = math.floor(math.log2(len(important_info_type1)))
        if num == 0:
            num = 1
        temp_dic = {}
        count = 0
        while count < num:
            index = random.randint(0, len(important_info_type1) - 1)
            while index in temp_dic:
                index = random.randint(0, len(important_info_type1) - 1)

            temp_dic[index] = 1
            count += 1

        for t in temp_dic:
            temp_type1.append(important_info_type1[t])

    # 删除距离当前时间超过1.5天(129600秒)的事件或1小时之内未完成/被中断的事件
    # 2026-01-17: 已完成和无法完成的事件没有删除的必要，可以长时间保留，不然记忆能力会降低
    temp_type4 = []
    current_time = datetime.timestamp(datetime.now())
    pattern = r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)'
    date_format = "%Y-%m-%d %H:%M:%S"
    for i in important_info_type4:
        if re.search(pattern, i):
            temp_time = re.search(pattern, i).group()
            temp_time = datetime.strptime(temp_time, date_format)
            temp_time = temp_time.timestamp()

            time_difference = current_time - temp_time
            if '已完成' in i or '无法完成' in i:
                temp_type4.append(i)
            if time_difference < 7200 and '进行中' in i:
                temp_type4.append(i)
            if time_difference < 3600 and '未完成' in i:
                temp_type4.append(i)
            if time_difference < 3600 and '被中断' in i:
                temp_type4.append(i)

    # 在今天的事件中删除'未完成'的事件(如果该事件被更新为'已完成'/'无法完成'/'被中断'/'进行中')
    delete_index = {}
    for idx, t in enumerate(temp_type4):
        if '已完成' in t:
            pattern = rf'((([Tt]he user)|({current_assistant[0]}))[\s\S]*)\.\s*[(（]已完成[)）]'
            if re.search(pattern, t):
                event = re.search(pattern, t).group(1)
                for idx2, t2 in enumerate(temp_type4):
                    if idx2 >= idx:
                        break
                    # 删除之前的同名任务
                    if event in t2 and idx2 < idx and ('未完成' in t2 or '进行中' in t2 or '被中断' in t2):
                        delete_index[idx2] = 1

        if '进行中' in t:
            pattern = rf'((([Tt]he user)|({current_assistant[0]}))[\s\S]*)\.\s*[(（]进行中[)）]'
            if re.search(pattern, t):
                event = re.search(pattern, t).group(1)
                for idx2, t2 in enumerate(temp_type4):
                    if idx2 >= idx:
                        break
                    # 被中断的任务重新变为进行中，删除之前被中断和未完成的任务
                    if event in t2 and idx2 < idx and ('未完成' in t2 or '被中断' in t2):
                        delete_index[idx2] = 1
        if '被中断' in t:
            pattern = rf'((([Tt]he user)|({current_assistant[0]}))[\s\S]*)\.\s*[(（]被中断[)）]'
            if re.search(pattern, t):
                event = re.search(pattern, t).group(1)
                for idx2, t2 in enumerate(temp_type4):
                    if idx2 >= idx:
                        break
                    # 进行中的任务重新变为被中断，删除之前进行中和未完成的任务
                    if event in t2 and idx2 < idx and  ('未完成' in t2 or '进行中' in t2):
                        delete_index[idx2] = 1
        if '无法完成' in t:
            pattern = rf'((([Tt]he user)|({current_assistant[0]}))[\s\S]*)\.\s*[(（]无法完成[)）]'
            if re.search(pattern, t):
                event = re.search(pattern, t).group(1)
                for idx2, t2 in enumerate(temp_type4):
                    if idx2 >= idx:
                        break
                    # 删除之前的同名任务
                    if event in t2 and idx2 < idx and ('未完成' in t2 or '进行中' in t2 or '被中断' in t2):
                        delete_index[idx2] = 1
        # 去除重复的'已完成'任务
        if '已完成' in t:
            pattern = rf'((([Tt]he user)|({current_assistant[0]}))[\s\S]*)\.\s*[(（]已完成[)）]'
            index_list = []
            if re.search(pattern, t):
                event = re.search(pattern, t).group(1)
                for idx2, t2 in enumerate(temp_type4):
                    if event in t2 and '已完成' in t2:
                        index_list.append(idx2)

            if len(index_list) > 1:
                # ！保留最初的已完成的任务
                temp_list = index_list[1:]
                for t2 in temp_list:
                    delete_index[t2] = 1

        # 去除重复的'未完成'任务
        if '未完成' in t:
            pattern = rf'((([Tt]he user)|({current_assistant[0]}))[\s\S]*)\.\s*[(（]未完成[)）]'
            index_list = []
            if re.search(pattern, t):
                event = re.search(pattern, t).group(1)
                for idx2, t2 in enumerate(temp_type4):
                    if event in t2 and '未完成' in t2:
                        index_list.append(idx2)

            # 保留最新的未完成的任务
            temp_list = index_list[:len(index_list) - 1]
            for t2 in temp_list:
                delete_index[t2] = 1

        # 去除重复的'进行中'任务
        if '进行中' in t:
            pattern = rf'((([Tt]he user)|({current_assistant[0]}))[\s\S]*)\.\s*[(（]进行中[)）]'
            index_list = []
            if re.search(pattern, t):
                event = re.search(pattern, t).group(1)
                for idx2, t2 in enumerate(temp_type4):
                    if event in t2 and '进行中' in t2:
                        index_list.append(idx2)

            # 保留最新的未完成的任务
            temp_list = index_list[:len(index_list) - 1]
            for t2 in temp_list:
                delete_index[t2] = 1

        # 去除重复的'无法完成'任务
        if '无法完成' in t:
            pattern = rf'((([Tt]he user)|({current_assistant[0]}))[\s\S]*)\.\s*[(（]无法完成[)）]'
            index_list = []
            if re.search(pattern, t):
                event = re.search(pattern, t).group(1)
                for idx2, t2 in enumerate(temp_type4):
                    if event in t2 and '无法完成' in t2:
                        index_list.append(idx2)

            # 保留最新的无法完成的任务
            temp_list = index_list[:len(index_list) - 1]
            for t2 in temp_list:
                delete_index[t2] = 1

    # 如果无法完成的事件过多，只取最新的3个无法完成的事件
    # 记录所有无法完成事件的下标(不包含要删除的)
    unable_finished_events_index_list = []

    for idx, i in enumerate(temp_type4):
        if '无法完成' in i and idx not in delete_index:
            unable_finished_events_index_list.append(idx)

    if len(unable_finished_events_index_list) > 3:
        for idx, i in enumerate(unable_finished_events_index_list):
            if idx < len(unable_finished_events_index_list) - 3:
                delete_index[i] = 1

    # 如果未完成的事件过多，只取最新的3个未完成事件
    # 记录所有已完成事件的下标(不包含要删除的)
    unfinished_events_index_list = []

    for idx, i in enumerate(temp_type4):
        if '未完成' in i and idx not in delete_index:
            unfinished_events_index_list.append(idx)

    if len(unfinished_events_index_list) > 3:
        for idx, i in enumerate(unfinished_events_index_list):
            if idx < len(unfinished_events_index_list) - 3:
                delete_index[i] = 1

    # '被中断'事件在被改动之前是'进行中'的事件！
    # 如果被中断的事件过多，只取最新的3个被中断事件
    # 记录所有被中断事件的下标(不包含要删除的)
    interrupted_events_index_list = []

    for idx, i in enumerate(temp_type4):
        if '进行中' in i and idx not in delete_index:
            interrupted_events_index_list.append(idx)

    if len(interrupted_events_index_list) > 3:
        for idx, i in enumerate(interrupted_events_index_list):
            if idx < len(interrupted_events_index_list) - 3:
                delete_index[i] = 1

    # 不需要提及过往的事件，只取最新的3个已完成事件
    if not many_events_needed:
        # 记录所有已完成事件的下标(不包含要删除的)
        finished_events_index_list = []

        for idx, i in enumerate(temp_type4):
            if '已完成' in i and idx not in delete_index:
                finished_events_index_list.append(idx)

        if len(finished_events_index_list) > 3:
            for idx, i in enumerate(finished_events_index_list):
                if idx < len(finished_events_index_list) - 3:
                    delete_index[i] = 1
    # 需要提及的，取10个
    else:
        # 记录所有已完成事件的下标(不包含要删除的)
        finished_events_index_list = []

        for idx, i in enumerate(temp_type4):
            if '已完成' in i and idx not in delete_index:
                finished_events_index_list.append(idx)

        if len(finished_events_index_list) > 10:
            for idx, i in enumerate(finished_events_index_list):
                if idx < len(finished_events_index_list) - 10:
                    delete_index[i] = 1

    new_temp_type4 = []
    for idx, i in enumerate(temp_type4):
        if idx not in delete_index:
            new_temp_type4.append(i)

    all_tasks = new_temp_type4

    # 处于同一时间的进行中的任务的下标
    ongoing_tasks_at_the_same_time_index = {}
    # 最新的进行中的任务
    last_ongoing_task_index = -1
    for idx,n in enumerate(new_temp_type4):
        if '进行中' in n:
            last_ongoing_task_index = idx

    if last_ongoing_task_index != -1:
        # 提取最后一个进行中的事的时间，因为可能有多个同时进行中的任务
        pattern = '(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)'
        if re.search(pattern, new_temp_type4[last_ongoing_task_index]):
            temp_time = re.search(pattern, new_temp_type4[last_ongoing_task_index]).group()
            for idx,n in enumerate(new_temp_type4):
                if temp_time in n and '进行中' in n:
                    ongoing_tasks_at_the_same_time_index[idx] = 1

    for o in ongoing_tasks_at_the_same_time_index:
        # 给最新的所有处于同一时间的进行中的事件打上标记
        new_temp_type4[o] = f"(现在在和{current_assistant[0]}一起做的事) {new_temp_type4[o]}"

    # 将之前所有进行中的任务强制改为被中断
    for idx,n in enumerate(new_temp_type4):
        if idx not in ongoing_tasks_at_the_same_time_index and '进行中' in n:
            pattern = r'\(进行中\)'
            new_temp_type4[idx] = re.sub(pattern, "(被中断)", new_temp_type4[idx])

    # 处于同一时间的未完成的任务的下标
    unfinished_tasks_at_the_same_time = {}
    # 最新的未完成的任务
    last_unfinished_task_index = -1
    for idx,n in enumerate(new_temp_type4):
        if '未完成' in n:
            last_unfinished_task_index = idx

    if last_unfinished_task_index != -1:
        # 提取最后一个进行中的事的时间，因为可能有多个同时进行中的任务
        pattern = '(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)'
        if re.search(pattern, new_temp_type4[last_unfinished_task_index]):
            temp_time = re.search(pattern, new_temp_type4[last_unfinished_task_index]).group()
            for idx,n in enumerate(new_temp_type4):
                if temp_time in n and '未完成' in n:
                    unfinished_tasks_at_the_same_time[idx] = 1

    for o in unfinished_tasks_at_the_same_time:
        # 给最新的所有处于同一时间的进行中的事件打上标记
        new_temp_type4[o] = f"(最新的未完成的任务) {new_temp_type4[o]}"

    # 删除已兑现\不需要兑现\无法兑现的承诺
    temp_type5 = []
    delete_index = {}

    promising_index = []

    for idx, i in enumerate(important_info_type5):
        if '已兑现' in i:
            pattern = rf'({current_assistant[0]} [\s\S]*)\.\s*[(（]已兑现[)）]'
            if re.search(pattern, i):
                promise = re.search(pattern, i).group(1)
                for idx2, i2 in enumerate(important_info_type5):
                    if promise in i2:
                        delete_index[idx2] = 1
        if '不需要兑现' in i:
            pattern = rf'({current_assistant[0]} [\s\S]*)\.\s*[(（]不需要兑现[)）]'
            if re.search(pattern, i):
                promise = re.search(pattern, i).group(1)
                for idx2, i2 in enumerate(important_info_type5):
                    if promise in i2:
                        delete_index[idx2] = 1
        if '无法兑现' in i:
            pattern = rf'{current_assistant[0]} ([\s\S]*)\.\s*[(（]无法兑现[)）]'
            if re.search(pattern, i):
                promise = re.search(pattern, i).group(1)
                for idx2, i2 in enumerate(important_info_type5):
                    if promise in i2:
                        delete_index[idx2] = 1
        # '兑现中'的承诺去除'未兑现'的承诺
        if '兑现中' in i:
            pattern = rf'({current_assistant[0]} [\s\S]*)\.\s*[(（]兑现中[)）]'
            if re.search(pattern, i):
                promise = re.search(pattern, i).group(1)
                for idx2, i2 in enumerate(important_info_type5):
                    if promise in i2 and '未兑现' in i2:
                        delete_index[idx2] = 1

        # 去除重复的'未兑现'承诺
        if '未兑现' in i:
            pattern = rf'{current_assistant[0]} ([\s\S]*)\.\s*[(（]未兑现[)）]'
            index_list = []
            if re.search(pattern, i):
                promise = re.search(pattern, i).group(1)
                for idx2, i2 in enumerate(important_info_type5):
                    if promise in i2 and '未兑现' in i2:
                        index_list.append(idx2)

            # 保留最新的未兑现的承诺
            temp_list = index_list[:len(index_list) - 1]
            for t2 in temp_list:
                delete_index[t2] = 1

        # 去除重复的'兑现中'承诺
        if '兑现中' in i:
            pattern = rf'{current_assistant[0]} ([\s\S]*)\.\s*[(（]兑现中[)）]'
            index_list = []
            if re.search(pattern, i):
                promise = re.search(pattern, i).group(1)
                for idx2, i2 in enumerate(important_info_type5):
                    if promise in i2 and '兑现中' in i2:
                        index_list.append(idx2)

            # 保留最新的兑现中的承诺
            temp_list = index_list[:len(index_list) - 1]
            for t2 in temp_list:
                delete_index[t2] = 1

        # 去除重复的'无法兑现'承诺
        if '无法兑现' in i:
            pattern = rf'{current_assistant[0]} ([\s\S]*)\.\s*[(（]无法兑现[)）]'
            index_list = []
            if re.search(pattern, i):
                promise = re.search(pattern, i).group(1)
                for idx2, i2 in enumerate(important_info_type5):
                    if promise in i2 and '无法兑现' in i2:
                        index_list.append(idx2)

            # 保留最新的无法兑现的承诺
            temp_list = index_list[:len(index_list) - 1]
            for t2 in temp_list:
                delete_index[t2] = 1

        # 如果有很多'兑现中'的承诺，只保留最后一个
        if '兑现中' in i:
            promising_index.append(idx)

    temp_list = promising_index[:len(promising_index) - 1]
    for t2 in temp_list:
        delete_index[t2] = 1

    for idx, i in enumerate(important_info_type5):
        if idx not in delete_index:
            temp_type5.append(i)

    if len(temp_type5) > 0:
        last_promise = temp_type5[-1]

    # 处理所有动作状态
    temp_type9 = important_info_type9[:]
    history_type9 = []
    current_type9 = ""
    pattern = r'当前\(([\s\S]*)\)'
    pattern2 = r'当前\([\s\S]*\)'
    pattern3 = r'当前\([\s\S]*\)\s'
    # 5轮为单位记录历史动作状态，最多取10条
    if len(temp_type9) > 5:
        count = 0
        for i in range(len(temp_type9) - 6, 0, -5):
            if count >= 10:
                break
            if re.search(pattern, temp_type9[i]) and count < 10:
                # 历史动作状态去掉'当前'
                temp_time = re.search(pattern, temp_type9[i]).group(1)
                history_type9.append(re.sub(pattern2, temp_time, temp_type9[i]))

                count += 1

    if len(temp_type9) > 0:
        # 当前动作状态去掉时间
        current_type9 = temp_type9[-1]
        current_type9 = re.sub(pattern3, r'', current_type9)

    # 提取当前外在形象中的时间并前置
    pattern = '(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)'
    if re.search(pattern, important_info_type10):
        type10_time = re.search(pattern, important_info_type10).group()
        pattern2 = '(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)\s*'
        important_info_type10 = re.sub(pattern2, r'', important_info_type10)

        if who not in last_appearance_time:
            last_appearance_time[who] = type10_time

    # 去除重复的概括
    new_temp_type1 = rag_type1 + temp_type1
    new_temp_type1_2 = list(dict.fromkeys(new_temp_type1))

    # 去除重复的不喜欢的人/不喜欢做的事情/不喜欢的物品/不能做的事情
    temp_type2 = list(dict.fromkeys(important_info_type2))

    # 去除重复的一直想做的事
    temp_type6 = list(dict.fromkeys(important_info_type6))

    # 去除重复的价值观与信念
    temp_type7 = list(dict.fromkeys(important_info_type7))

    # 去除重复的取得过的重大成就/经历过的艰难时刻
    temp_type8 = list(dict.fromkeys(important_info_type8))

    # 去除重复的人物关系
    temp_relationships = list(dict.fromkeys(relationships))

    def generate_content(temp_type):
        temp_content = ""
        for idx, t in enumerate(temp_type):
            if idx != 0:
                temp_content = f"{temp_content}/{t}"
            else:
                temp_content = t

        return temp_content

    type1_content = generate_content(new_temp_type1_2)
    type2_content = generate_content(temp_type2)
    type6_content = generate_content(temp_type6)
    type7_content = generate_content(temp_type7)
    type8_content = generate_content(temp_type8)
    type4_content = generate_content(new_temp_type4)
    type5_content = generate_content(temp_type5)
    type9_content = generate_content(history_type9)

    rag_type2_content = generate_content(rag_type2)

    # 去掉'可能与当前话题相关的事件'中所有的(已完成)
    pattern = r'\(已完成\)\s*'
    rag_type2_content = re.sub(pattern, r'',rag_type2_content)

    relationships_content = generate_content(temp_relationships)

    temp = []
    temp_important_info_list = []
    if len(current_environment) > 0:
        temp.append(f"*当前环境:{current_environment}\n")
    if len(relationships_content) > 0:
        temp.append(f"*用户与其它人物的关系:{relationships_content}\n")
    if len(temp_type1) > 0:
        temp.append(f"*概括:{type1_content}\n")
    if len(current_state1) > 0:
        temp.append(f"*用户当前的生理状态:{current_state1}\n")
    if len(current_state2) > 0:
        temp.append(f"*用户当前的情绪状态:{current_state2}\n")
    if len(current_state3) > 0:
        temp.append(f"*用户当前的心理状态:{current_state3}\n")
    if len(current_state4) > 0:
        temp.append(f"*用户当前的社交状态:{current_state4}\n")
    if len(important_info_type2) > 0:
         temp.append(f"*用户不喜欢的人/不喜欢做的事情/不喜欢的物品/不能做的事情:{type2_content}\n")
    if len(important_info_type6) > 0:
        temp.append(f"*用户一直想做的事情:{type6_content}\n")
    if len(important_info_type7) > 0:
        temp.append(f"*用户的价值观与信念:{type7_content}\n")
    if len(important_info_type8) > 0:
        temp.append(f"*用户取得过的重大成就/经历过的艰难时刻:{type8_content}\n")
    if len(important_info_type3) > 0:
        temp.append(f"*用户最近在忙什么事:{important_info_type3}\n")
    if len(rag_type2_content) > 0:
        temp.append(f"*可能与当前话题相关的事件:{rag_type2_content}\n")
    if len(new_temp_type4) > 0:
        temp.append(f"*用户最近和{current_assistant[0]}一起做了什么事:{type4_content}\n")
    if len(temp_type5) > 0:
        temp.append(f"*{current_assistant[0]}需要兑现的承诺:{type5_content}\n")
    '''
    if len(history_type9) > 0:
        temp.append(f"*{current_assistant[0]}的历史动作状态:{type9_content}")
    '''
    if current_type9 != "":
        temp.append(f"*{current_assistant[0]}的当前动作状态:{current_type9}\n")
    if len(important_info_type10) > 0:
        temp.append(f"*{current_assistant[0]}的初始外在形象:{original_appearance}\n")
        temp.append(f"*{current_assistant[0]}的最新外在形象({type10_time}):{important_info_type10}")

    temp_important_info = ""

    for t in temp:
        temp_important_info += t

    temp_important_info_list.append(temp_important_info)

    temp = []
    if len(current_state1) > 0:
        temp.append(f"*用户当前的生理状态:{current_state1}\n")
    if len(current_state2) > 0:
        temp.append(f"*用户当前的情绪状态:{current_state2}\n")
    if len(current_state3) > 0:
        temp.append(f"*用户当前的心理状态:{current_state3}\n")
    if len(current_state4) > 0:
        temp.append(f"*用户当前的社交状态:{current_state4}\n")

    temp_important_info = ""

    for t in temp:
        temp_important_info += t

    temp_important_info_list.append(temp_important_info)

    temp = []
    if len(new_temp_type4) > 0:
        temp.append(f"*用户最近和{current_assistant[0]}一起做了什么事:{type4_content}\n")
    if len(temp_type5) > 0:
        temp.append(f"*{current_assistant[0]}需要兑现的承诺:{type5_content}\n")

    temp_important_info = ""

    for t in temp:
        temp_important_info += t

    temp_important_info_list.append(temp_important_info)

    temp = []
    if len(current_environment) > 0:
        temp.append(f"*当前环境:{current_environment}\n")
    if len(important_info_type10) > 0:
        temp.append(f"*{current_assistant[0]}的初始外在形象:{original_appearance}\n")
        temp.append(f"*{current_assistant[0]}的最新外在形象({type10_time}):{important_info_type10}")

    temp_important_info = ""

    for t in temp:
        temp_important_info += t

    temp_important_info_list.append(temp_important_info)

    return temp_important_info_list

# 获取当前用户的重要信息
def get_important_info(who):
    important_info = []

    path = f'{relative_path}/private/{who}/重要信息({current_assistant[0]}).json'

    if os.path.exists(path):
        try:
            important_info = read_json_file(path)
            return important_info
        except Exception as e:
            print(f"读取{who}的重要信息({current_assistant[0]}).json文件失败!\n")
            pass
    else:
        os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)
        return {}

# 重要信息处理，到json文件
def get_important_info_and_rewrite2(who, translation, assistant):
    global last_translation
    # 防止重复记录translation
    if last_translation != translation:
        last_translation = translation

        # 替换所有的{assistant}
        pattern = r'({)*assistant(})*'
        translation = re.sub(pattern, assistant, translation)

        important_info = []

        path = f'{relative_path}/private/{who}/重要信息({current_assistant[0]}).json'

        if os.path.exists(path):
            try:
                # 读取用户的重要信息
                with open(path, 'r', encoding='utf-8') as file:
                    important_info = read_json_file(path)
            except Exception as e:
                print(f"读取{who}的重要信息({current_assistant[0]}).json文件失败!\n")
                pass
        else:
            os.makedirs(f"{relative_path}/private/{who}", exist_ok=True)

        words_list = ['标准1', '标准3', '标准4']
        words_list2 = ['标准10', '标准11', '标准12', '标准13', '标准14']

        type = ""

        # 如果translation 包含多个部分，逐个添加
        translation_part1 = ""
        translation_group = []

        if "&&" not in translation:
            translation_group.append(translation)
        else:
            pattern = r'([^&&]*)&&'
            if re.search(pattern, translation):
                translation_part1 = re.search(pattern, translation).group(1)

            pattern = r'&&\s*[^&&]*'
            if re.search(pattern, translation):
                temp_group = re.findall(pattern, translation)
                for i in temp_group:
                    pattern = r'&&\s*'
                    t = re.sub(pattern, r'', i)
                    translation_group.append(t)

            translation_group.insert(0, translation_part1)

        # print(f"经处理，Tranlation可被分为{len(translation_group)}个部分。\n")

        for t_part in translation_group:
            contain_these_words = False
            for w in words_list2:
                if w in t_part:
                    contain_these_words = True
                    break

            if not contain_these_words:
                # 包含'标准1'、'标准3'、'标准4'的translation直接归类为'概括'
                for w in words_list:
                    if w in t_part:
                        # 临时想做的事情，加上时间标签
                        if "标准4" in t_part:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            t_part = timestamp + f" {t_part}"

                        type = "概括"
                        temp_info = {"content": t_part, "type": type}
                        important_info.append(temp_info)

                        # print("该translation被直接归类为'概括'并记录到重要信息中。\n")

                        embedding = get_query_embedding(t_part)

                        if embedding:
                            rag_dic = {
                                "content": t_part,
                                "embedding": embedding
                            }
                            write_in_rag2(who, rag_dic)

            # 包含'今天'的translation直接归类为'今天做了什么事'
            if '今天' in t_part:
                event = ''

                # 去除可能携带的时间信息，并重新添加上'今天'
                pattern = r'((([Tt]he)|(Bandit))[\s\S]*)'
                if re.search(pattern, t_part):
                    t_part = re.search(pattern, t_part).group()
                    event = t_part
                    t_part = f'今天 {t_part}'

                # 今天做了什么事，加上时间标签
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                pattern = r'今天'
                t_part = re.sub(pattern, timestamp, t_part)

                type = "今天做了什么事"
                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # 已完成的事件记录到rag3中、
                if '已完成' in event:
                    embedding = get_query_embedding(event)

                    if embedding:
                        rag_dic = {
                            "content": event,
                            'timestamp': timestamp,
                            "embedding": embedding
                        }
                        write_in_rag3(who, rag_dic)

                # print("translation包含'今天'，直接归类为'今天做了什么事'并记录到重要信息中。\n")

            # 包含'标准2'(不喜欢的人/不喜欢做的事情/不喜欢的物品/不能做的事情)
            if '标准2' in t_part:
                type = "不喜欢的人/不喜欢做的事情/不喜欢的物品/不能做的事情"
                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准2'，直接归类为'不喜欢的人/不喜欢做的事情/不喜欢的物品/不能做的事情'并记录到重要信息中。\n")

            # 包含'标准5'(一直想做的事情)
            if '标准5' in t_part:
                type = "一直想做的事情"
                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准5'，直接归类为'一直想做的事情'并记录到重要信息中。\n")

            # 包含'标准6'(价值观与信念)
            if '标准6' in t_part:
                type = "价值观与信念"
                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准6'，直接归类为'价值观与信念'并记录到重要信息中。\n")

            # 包含'标准7'(取得过的重大成就/经历过的艰难时刻)
            if '标准7' in t_part:
                type = "取得过的重大成就/经历过的艰难时刻"

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # 如果有时间标签，去掉上次的时间标签
                pattern = r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)'
                if re.search(pattern, t_part):
                    t_part = re.sub(pattern, timestamp, t_part)
                else:
                    # 加上时间标签
                    t_part = f"{timestamp} {t_part}"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准7'，直接归类为'取得过的重大成就/经历过的艰难时刻'并记录到重要信息中。\n")

            # 包含'标准8'(最近在忙什么事)
            if '标准8' in t_part:
                type = "最近在忙什么事"

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # 如果有时间标签，去掉上次的时间标签
                pattern = r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)'
                if re.search(pattern, t_part):
                    t_part = re.sub(pattern, timestamp, t_part)
                else:
                    # 加上时间标签
                    t_part = f"{timestamp} {t_part}"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准8'，直接归类为'最近在忙什么事'并记录到重要信息中。\n")

            # 包含'标准10'(当前的生理状态)
            if '标准10' in t_part:
                type = "当前的生理状态"

                # 加上时间标签
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                t_part = f"{timestamp} {t_part}"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准10'，直接归类为'当前的生理状态'并记录到重要信息中。\n")

            # 包含'标准11'(当前的情绪状态)
            if '标准11' in t_part:
                type = "当前的情绪状态"

                # 加上时间标签
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                t_part = f"{timestamp} {t_part}"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准11'，直接归类为'当前的情绪状态'并记录到重要信息中。\n")

            # 包含'标准12'(当前的心理状态)
            if '标准12' in t_part:
                type = "当前的心理状态"

                # 加上时间标签
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                t_part = f"{timestamp} {t_part}"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准12'，直接归类为'当前的心理状态'并记录到重要信息中。\n")

            # 包含'标准13'(当前的社交状态)
            if '标准13' in t_part:
                type = "当前的社交状态"

                # 加上时间标签
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                t_part = f"{timestamp} {t_part}"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准13'，直接归类为'当前的社交状态'并记录到重要信息中。\n")

            # 包含'标准14'(人物关系)
            if '标准14' in t_part:
                type = "人物关系"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'标准14'，直接归类为'人物关系'并记录到重要信息中。\n")

            # 需要兑现的承诺
            if '兑现' in t_part:
                type = "需要兑现的承诺"

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # 如果有时间标签，去掉上次的时间标签
                pattern = r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)'
                if re.search(pattern, t_part):
                    t_part = re.sub(pattern, timestamp, t_part)
                else:
                    # 加上时间标签
                    t_part = f"{timestamp} {t_part}"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'兑现'，直接归类为'需要兑现的承诺'并记录到重要信息中。\n")

            # 当前动作状态
            if '当前' in t_part:
                type = "当前动作状态"

                # 加上时间标签，以方便记录历史动作状态，增强后续动作的逻辑性
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pattern = r'当前'
                t_part = re.sub(pattern, f'当前({timestamp})', t_part)

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'当前'，直接归类为'当前动作状态'并记录到重要信息中。\n")

            # 外在形象
            if '有变化' in t_part:
                type = "外在形象"

                # 加上事件标签
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                t_part = f"{timestamp} {t_part}"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'有变化'，直接归类为'外在形象'并记录到重要信息中。\n")

            # 当前环境
            if '环境变化' in t_part:
                type = "当前环境"

                temp_info = {"content": t_part, "type": type}
                important_info.append(temp_info)

                # print("translation包含'环境变化'，直接归类为'当前环境'并记录到重要信息中。\n")


        # 打开文件，以写入模式创建文件对象
        with open(f'{relative_path}/private/{who}/重要信息({current_assistant[0]}).json', 'w', encoding='utf-8') as file:
            # indent=1 每个层级缩进1个空格
            file.write(json.dumps(important_info, indent=1, ensure_ascii=False))

        print(f"写入{who}的重要信息({current_assistant[0]}).json文件成功!\n")
        print(f"关于{who}的重要信息数量为{len(important_info)}\n")

    else:
        print("获取到的translation和上次相同，不进行处理!\n")
