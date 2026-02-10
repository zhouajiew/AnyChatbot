import asyncio
import json
import math
import os
import random
import re
import threading
import time
from datetime import datetime
from time import sleep

from flask_socketio import SocketIO, send
from flask import Flask, render_template, jsonify

from config import *
from memory import *
from rag import *
from message import *
from prompt import *

from global_variable import *

already_get_character1 = False

character1 = ""
character2 = ""

# 获取到的人设prompt
custom_prompt = ""

# 所有的新消息
new_messages_list = []

private_message_count = 0

max_context = 0

context_list = []

# 最新外在形象的时间(防止反复询问)
latest_appearance_time = {}

# 获取当前文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建相对路径
relative_path = os.path.join(current_dir)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('c')
def client_connected():
    print('Client connected')
    init_config()
    read_config()
    if enable_likeability[0] == 1:
        current_likeability[0] = get_likeability(user_name[0])

@socketio.on('save_character2')
def save_character2(message):
    global custom_prompt

    print('保存自定义人设请求')
    if current_assistant[0] != "Bandit":
        custom_prompt = message
        path = f'{relative_path}/设定({current_assistant[0]}).txt'

        # 打开文件，以写入模式创建文件对象
        with open(path, 'w', encoding='utf-8') as file:
            file.write(message)

        print(f"写入设定({current_assistant[0]}).txt文件成功!\n")
    else:
        print('不修改默认人设')

@socketio.on('save_config')
def save_config(message):
    print('保存设置请求')
    data = json.loads(message)
    set_config(data)

@socketio.on('get_api_response')
def get_api_response(message):
    new_messages_list.append(message)
    print('获取API回复请求')

@socketio.on('get_memories')
def get_memories(message):
    if user_name[0] == "default":
        sleep(0.1)

    print('获取记忆请求')
    data = json.loads(message)
    count = data[0].get('count')
    #print(f'count:{count}')
    memories = get_latest_memories(user_name[0])
    #print(f'获取到的记忆数量:{len(memories)}')
    temp_memories = []

    num = 5

    if count > math.ceil(len(memories) / num):
        socketio.emit("memories", [])
    else:
        if num * count < len(memories):
            #print(f'{len(memories) - num * count}:{len(memories) - num * (count - 1)}')
            temp_memories = memories[len(memories) - num * count:len(memories) - num * (count - 1)]
        else:
            #print(f'0:{len(memories) - num * (count - 1)}')
            temp_memories = memories[:len(memories) - num * (count - 1)]

        #print(temp_memories)
        socketio.emit("memories", temp_memories)


@socketio.on('message')
def handle_message(message):
    global character1
    global character2

    if message == "get_default_character":
        print('获取默认人设请求')
        get_default_character()
        socketio.emit("character", character1)
    if message == "get_character2":
        print('获取自定义人设请求')
        get_character2()
        if len(character2) > 0:
            socketio.emit("character2", character2)
        else:
            socketio.emit("character2", 'No data!')
    if message == "get_config":
        print('获取模型设置请求')
        data = read_config()
        if data:
            json_str = json.dumps(data)
            socketio.emit("config", json_str)

@app.route('/index')
def index():
    return render_template('index.html',
                          title='Flask Template',
                          name='摆烂Jo',
                          messages=["0", "0"])

def get_character2():
    global character2

    path = f'{relative_path}/设定({current_assistant[0]}).txt'
    if os.path.exists(path):
        try:
            with open(f"{relative_path}/设定({current_assistant[0]}).txt", "r", encoding='utf-8') as file:
                character2 = file.read()
        except Exception as e:
            print(f"读取设定({current_assistant[0]}).txt文件失败!")
            pass
    else:
        character2 = ""

def get_default_character():
    global character1
    global already_get_character1

    if not already_get_character1:
        if app_environment[0] == 0:
            path = f'{relative_path}/设定.txt'
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding='utf-8') as file:
                        character1 = file.read()
                        return character1
                except Exception as e:
                    print(f"读取设定.txt文件失败!")
                    pass
        else:
            path = f'{relative_path}/设定2.txt'
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding='utf-8') as file:
                        character1 = file.read()
                        return character1
                except Exception as e:
                    print(f"读取设定.txt文件失败!")
                    pass
    else:
        return character1

async def merge_msgs():
    global new_messages_list
    global private_message_count
    global max_context
    global latest_appearance_time

    count = 0
    # 合并的消息
    merge_result = ""

    for m in new_messages_list:
        count += 1

    start_time = time.time()

    if count != 0:
        try:
            end_time = time.time()
            # 等待7秒
            count2 = 0
            while end_time - start_time < 7:
                await asyncio.sleep(0.5)
                end_time = time.time()
                for m in new_messages_list:
                    count2 += 1
                if count2 > count:
                    count = count2
                    start_time = time.time()
                count2 = 0

            for idx, m in enumerate(new_messages_list):
                merge_result = f"{merge_result} {m}"

            new_messages_list = []

            # 去掉开头的空格:
            pattern = r' '
            merge_result = re.sub(pattern, r'', merge_result, count=1)

            print(f"消息合并结果:{merge_result}\n")
            socketio.emit("merge_result", 'merge over!')
        except Exception as e:
            print(f"合并结果时出错:{e}")

        '''
        # 多事件引用判断(弃用，采用时间跨度提取)
        event_prompt = many_events_needed_prompt(merge_result)
        result = {}
        many_events_needed = False

        try:
            event_prompt2 = [{"role": "user", "content": event_prompt}]

            result = get_ai_response2_stream("deepseek-chat", event_prompt2, user_name[0])

            pattern = r'是[,，]'
            if re.search(pattern, result["content"]):
                many_events_needed = True

            with open(f"{relative_path}/many_events_needed.txt", "w", encoding='utf-8') as file:
                full_content = f'completion_tokens:{result["completion_tokens"]}\nprompt_cache_hit_tokens:{result["prompt_cache_hit_tokens"]}\nprompt_cache_miss_tokens:{result["prompt_cache_miss_tokens"]}\n\n本次请求消费{result["cost"]}元\n\n{result["content"]}'
                file.write(full_content)
        except Exception as e:
            print(f"获取多事件引用判断失败!{e}")
        '''

        # 获取当前用户的最新记忆
        memories = get_latest_memories(user_name[0])
        # 时间跨度提取
        time_span = get_time_span_prompt(merge_result, memories, 3, user_name[0])

        # 创建query的嵌入向量进行查询
        rag_content = ""
        query_embedding = None
        try:
            if len(merge_result) > 10:
                print("正在查询语义相似的用户消息\n")
                query_embedding = get_query_embedding(merge_result)

                # 查询rag.json
                rag_results = search_from_rag_json(user_name[0], query_embedding)
                rag_results = rag_results[:5]
                rag_content = generate_rag_content(5, rag_results)
        except Exception as e:
            print(f"创建query的嵌入向量时出错:{e}")

        # 获取AI回复
        try:
            read_config()

            private_message_count += 1

            temp_context = []

            history_prompt = generate_history_prompt(5)
            history_content = generate_history_content(
                5,
                memories,
                private_message_count,
                max_context,
            )

            # 获取当前用户的重要信息
            important_info = get_important_info(user_name[0])

            # 当前用户的长下文长度
            context_length = 0

            # 获取当前用户的上下文
            for c in context_list:
                if c["who"] == user_name[0]:
                    temp_context.append({"role": "user", "content": c["user_content"]})
                    temp_context.append({"role": "assistant", "content": c["assistant_content"]})
                    context_length += 2

            # print(f"获取到{who}的上下文内容:")
            '''
            for t in temp_context:
                if t["role"] == "user":
                    print(f"用户的消息:{t["content"]}")
                if t["role"] == "assistant":
                    print(f"你的回复:{t["content"]}")
            '''

            # 构造多轮对话
            # 系统提示词
            if custom_prompt == "":
                context = [{"role": "system", "content": system_prompt(user_name[0])}]
            else:
                context = [{"role": "system", "content": custom_prompt}]

            # 固定内容数量
            fixed_context_length = 0

            '''
            # 示例对话
            example = example_prompt(who)
            example += example_context()
            context.append({"role": "user", "content": example})
            context.append({"role": "assistant", "content": "Got it!"})
            '''

            # 历史对话提示词
            context.append({"role": "user", "content": history_prompt})
            context.append({"role": "assistant", "content": "Got it!"})
            # 历史对话内容(memory+rag)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_content = f"当前对话时间:{timestamp}\n\n以下是历史对话内容:\n**\n{history_content}\n\n"

            both_content = history_content + rag_content
            # print(f"{both_content}\n")

            with open(f"{relative_path}/historical_dialogs.txt", "w", encoding='utf-8') as file:
                file.write(both_content)

            context.append({"role": "user", "content": both_content})
            context.append({"role": "assistant", "content": "I will handle these contents properly!"})
            # 重要信息
            important_info_content = generate_important_info(user_name[0], important_info, query_embedding, time_span)
            temp_important_info_content = important_info_content

            important_info_content[0] = "以下是'需要注意到的重要信息'，你应当根据当前场景有选择性地参考他们，而不是全部参考他们。分数越高的信息越重要。\n\n" + important_info_content[0]

            # print(f"{important_info_content[0]}\n")
            with open(f"{relative_path}/important_info.txt", "w", encoding='utf-8') as file:
                file.write(important_info_content[0])

            context.append({"role": "user", "content": important_info_content[0]})
            context.append({"role": "assistant", "content": "Got it!"})

            fixed_context_length = len(context)

            for t in temp_context:
                context.append(t)

            # 管理上下文
            if context_length > 2*max_context:
                context = manage_context(max_context,context,fixed_context_length)

            temp_last_task = get_all_tasks()
            temp_last_promise = get_last_promise()

            task_type = 0

            if len(temp_last_task) > 1:
                for t in temp_last_task[-2:]:
                    if '进行中' in t:
                        task_type = 1
                        break

            if len(temp_last_task) > 0:
                # 最新的任务显示已完成 and 有has helped
                if '已完成' in temp_last_task[-1] and f'{current_assistant[0]} has helped' in temp_last_task[-1]:
                    task_type = 2

            if '兑现中' in temp_last_promise:
                task_type = 1

            date_format = "%Y-%m-%d %H:%M:%S"
            current_time = datetime.timestamp(datetime.now())

            temp_time = 0

            temp_time = datetime.strptime(get_last_appearance_time(user_name[0]), date_format)
            temp_time = temp_time.timestamp()

            if user_name[0] not in latest_appearance_time and temp_time != 0:
                latest_appearance_time[user_name[0]] = temp_time

            if task_type == 0:
                # 距离上次形象变化超过20分钟，提醒注意形象变化
                if current_time - latest_appearance_time[user_name[0]] > 1200:
                    # 防止因外貌未发生变化导致的反复询问
                    latest_appearance_time[user_name[0]] = current_time

                    # 最近两件事中，无进行中和已完成的任务，强调这些提示以注意到可能的外在形象变化以及使用多样化语句
                    merge_result = f"{merge_result} (<系统提示>check whether your appearance will change for some reasons (don't mention your appearance if your appearance has no changes!) and try to use various but straightforward sentences and behaviors that are not similar to former dialogs</系统提示>)"
                else:
                    merge_result = f"{merge_result} (<系统提示>try to use various but straightforward sentences and behaviors that are not similar to former dialogs</系统提示>)"
            else:
                # 距离上次形象变化超过20分钟，提醒注意形象变化
                if current_time - latest_appearance_time[user_name[0]] > 1200:
                    # 防止因外貌未发生变化导致的反复询问
                    latest_appearance_time[user_name[0]] = current_time

                    merge_result = f"{merge_result} (<系统提示>check whether your appearance will change for some reasons (don't mention your appearance if your appearance has no changes!)</系统提示>)"

            if task_type == 1:
                # 有进行中的任务，强调这些提示以推动情节发展
                merge_result = f"{merge_result} (<系统提示>response to the user properly and use straightforward sentences to describe the next scene detailedly</系统提示>)"
            if task_type == 2:
                # 最新的任务是已完成的状态，强调这些提示以关心用户的当前状态
                merge_result = f"{merge_result} (<系统提示>check whether the user's current status is good and response to the user properly with straightforward sentences</系统提示>)"

            context.append({"role": "user", "content": merge_result})

            print(f"向AI发送的最新消息:{merge_result}\n")

            # 获取deepseek回复
            # 用流式输出显示进度
            task = asyncio.create_task(get_ai_response_stream(model[0], context, user_name[0]))
            result = await task

            socketio.emit('final_response', result.get('content'))

            change_likeability_task = None
            if enable_likeability[0] == 1:
                change_likeability_task = asyncio.create_task(change_likeability(merge_result, result["content"], current_likeability[0], memories, 3, user_name[0]))
                # change_likeability_thread = threading.Thread(target=change_likeability, args=(merge_result, result["content"], current_likeability[0], memories, 3, user_name[0]))
                # change_likeability_thread.start()

            if len(memories) > 3:
                # 获取Translation部分
                t1 = asyncio.create_task(get_translation_part(memories[-3:], temp_important_info_content[1], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 1))
                t2 = asyncio.create_task(get_translation_part(memories[-3:], temp_important_info_content[2], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 2))
                t3 = asyncio.create_task(get_translation_part(memories[-3:], temp_important_info_content[3], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 3))
                if enable_likeability[0] == 0:
                    await t1
                    await t2
                    await t3
                    await asyncio.sleep(2)
                else:
                    await t1
                    await t2
                    await t3
                    await change_likeability_task
                    await asyncio.sleep(2)
                    socketio.emit('likeability', current_likeability[0])
                '''
                t1 = threading.Thread(target=get_translation_part, args=(
                memories[-3:], temp_important_info_content[1], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 1))
                t2 = threading.Thread(target=get_translation_part, args=(
                memories[-3:], temp_important_info_content[2], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 2))
                t3 = threading.Thread(target=get_translation_part, args=(
                memories[-3:], temp_important_info_content[3], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 3))

                t1.start()
                await asyncio.sleep(2)
                t2.start()
                await asyncio.sleep(2)
                t3.start()
                '''
            else:
                # 获取Translation部分
                t1 = asyncio.create_task(get_translation_part(memories, temp_important_info_content[1], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 1))
                t2 = asyncio.create_task(get_translation_part(memories, temp_important_info_content[2], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 2))
                t3 = asyncio.create_task(get_translation_part(memories, temp_important_info_content[3], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 3))
                if enable_likeability[0] == 0:
                    await t1
                    await t2
                    await t3
                    await asyncio.sleep(2)
                else:
                    await t1
                    await t2
                    await t3
                    await change_likeability_task
                    await asyncio.sleep(2)
                    socketio.emit('likeability', current_likeability[0])
                '''
                t1 = threading.Thread(target=get_translation_part, args=(
                memories, temp_important_info_content[1], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 1))
                t2 = threading.Thread(target=get_translation_part, args=(
                memories, temp_important_info_content[2], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 2))
                t3 = threading.Thread(target=get_translation_part, args=(
                memories, temp_important_info_content[3], 3, merge_result, result["content"], user_name[0],
                current_assistant[0], 3))

                t1.start()
                await asyncio.sleep(2)
                t2.start()
                await asyncio.sleep(2)
                t3.start()
                '''

            '''
            # 处理重要信息的任务执行情况
            task_status = 0
            while task_status < 3:
                await asyncio.sleep(1)
                task_status = get_task_status()
            '''

            # 去掉所有的hint
            pattern = r"\s*\(<系统提示>check whether your appearance will change for some reasons \(don't mention your appearance if your appearance has no changes!\)</系统提示>\)"
            merge_result = re.sub(pattern, r'', merge_result)
            pattern = r"\s*\(<系统提示>check whether your appearance will change for some reasons \(don't mention your appearance if your appearance has no changes!\) and try to use various but straightforward sentences and behaviors that are not similar to former dialogs</系统提示>\)"
            merge_result = re.sub(pattern, r'', merge_result)
            pattern = r"\s*\(<系统提示>response to the user properly and use straightforward sentences to describe the next scene detailedly</系统提示>\)"
            merge_result = re.sub(pattern, r'', merge_result)
            pattern = r"\s*\(<系统提示>check whether the user's current status is good and response to the user properly with straightforward sentences</系统提示>\)"
            merge_result = re.sub(pattern, r'', merge_result)
            pattern = r"\s*\(<系统提示>try to use various but straightforward sentences and behaviors that are not similar to former dialogs</系统提示>\)"
            merge_result = re.sub(pattern, r'', merge_result)

            # 添加到上下文中
            context_list.append({"who": user_name[0],
                                 "user_content": merge_result,
                                 "assistant_content": result["content"]})

            # 添加到记忆json中
            # 如果启用了好感度的话，加上likeability
            if enable_likeability[0] == 0:
                add_to_memory([
                    {"timestamp": timestamp,
                     "user_content": merge_result,
                     "assistant_content": result["content"],
                     "assistant_name": current_assistant[0]}
                ], user_name[0])
            else:
                add_to_memory([
                    {"timestamp": timestamp,
                     "user_content": merge_result,
                     "assistant_content": result["content"],
                     "assistant_name": current_assistant[0],
                     "likeability": current_likeability[0]}
                ], user_name[0])

            # 将用户的消息embedding到rag中
            # 太短的merge_result不发送
            if len(merge_result) > 10:
                user_content_embedding = get_query_embedding(merge_result)

                if user_content_embedding:
                    rag_dic = {
                        "timestamp": timestamp,
                        "user_content": merge_result,
                        "assistant_content": result["content"],
                        "embedding": user_content_embedding
                    }

                    write_in_rag(user_name[0], rag_dic)
            else:
                print(f"合并的消息太短，不添加到{user_name[0]}_rag.json中\n")

            '''
            # 处理重要信息的任务执行失败的话，不进行记录
            if task_status == 3:

            else:
                await asyncio.sleep(2)
                socketio.emit('error', "Oops! An error has occurred! Please try to send a message again!")
            '''

        except Exception as e:
            print(f"回复消息时出错:{e}")

async def main():
    while True:
        await asyncio.sleep(0.1)
        if len(new_messages_list) > 0:
            task = asyncio.create_task(merge_msgs())
            await task

def run_app():
    # app.run(debug=True)
    socketio.run(app, port=5005, allow_unsafe_werkzeug=True)

app_thread = threading.Thread(target=run_app)
app_thread.start()

asyncio.run(main())
