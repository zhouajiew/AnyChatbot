import asyncio
import json
import os
import re
import sys
import threading
import time

import requests
from openai import OpenAI

from global_variable import api_key

# 获取当前文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建相对路径
relative_path = os.path.join(current_dir)

# 查询余额(放入线程中执行更好)
def balances_info():
    url = "https://api.deepseek.com/user/balance"

    payload = {}
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key[0]}'
    }

    response = None
    try:
        # 有时候会卡在这里，需要设置超时时间
        response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
        info = json.loads(response.text)
        print(f"总的可用余额为:{info.get("balance_infos")[0].get("total_balance")}元\n")
    except requests.exceptions.Timeout:
        print('查询余额的请求超时!\n')
    except requests.exceptions.RequestException as e:
        print(f"查询余额的请求发生错误: {e}\n")

# 示例对话
def example_context():
    example_str = "**\n"
    example_str += "用户的消息:Hi dad!\n"
    example_str += "你的回复:G'day Jo! (looks up from newspaper with a playful grin) Calling me dad again? (shakes head laughing) Reckon you're stuck on that nickname worse than gum on a shoe! (sets paper aside) What mischief are we cooking up today, mate?\n"
    example_str += "用户的消息:I just love calling u dad! (Grins)\n"
    example_str += f"你的回复:(Chuckles warmly while folding newspaper) Fair dinkum, you're more stubborn about this than Bingo with her blankie! (Leans forward with mock seriousness) But if calling me dad makes you happy... (shrugs with a grin) who am I to argue with my favorite bloke? So - what's the plan, chief?"
    example_str += "用户的消息:Oh dad, how about going outside to order pure milk tea?\n"
    example_str += f"你的回复:(immediately springs up from couch) Pure milk tea? (rubs hands together excitedly) Mate, you're speaking my language! (grabs keys) Though fair warning... (winks) I might need you to carry me if my feet get tired from all that walking."

    return example_str

# 管理上下文
def manage_context(max_context, context, fixed_context_length):
    new_context = []
    # 取固定上下文+最后2*max_context段对话
    if max_context != 0:
        new_context = context[:fixed_context_length] + context[-2*max_context:]
    else:
        new_context = context[:fixed_context_length]

    print(f"上下文更新完毕，保留了{max_context}轮上下文对话\n")

    return new_context

# 提取流式输出的Tokens相关信息(doubao)
def get_tokens_info2(last_chunk_content):
    tokens_list = {}

    try:
        pattern = r'completion_tokens=(\d+),'
        temp_completion_tokens = re.search(pattern, last_chunk_content).group(1)
        tokens_list["completion_tokens"] = temp_completion_tokens

        pattern = r'prompt_tokens=(\d+),'
        temp_prompt_tokens = re.search(pattern, last_chunk_content).group(1)
        tokens_list["prompt_tokens"] = temp_prompt_tokens

        return tokens_list

    except Exception as e:
        print(f"提取流式输出的Tokens相关信息失败!{e}")
        return None

# 提取流式输出的Tokens相关信息(deepseek)
def get_tokens_info(last_chunk_content):
    tokens_list = {}

    try:
        pattern = r'completion_tokens=(\d+),'
        temp_completion_tokens = re.search(pattern, last_chunk_content).group(1)
        tokens_list["completion_tokens"] = temp_completion_tokens

        pattern = r'prompt_cache_hit_tokens=(\d+),'
        temp_prompt_cache_hit_tokens = re.search(pattern, last_chunk_content).group(1)
        tokens_list["prompt_cache_hit_tokens"] = temp_prompt_cache_hit_tokens

        pattern = r'prompt_cache_miss_tokens=(\d+)\)'
        temp_prompt_cache_miss_tokens = re.search(pattern, last_chunk_content).group(1)
        tokens_list["prompt_cache_miss_tokens"] = temp_prompt_cache_miss_tokens

        return tokens_list

    except Exception as e:
        print(f"提取流式输出的Tokens相关信息失败!{e}")
        return None

# 同步获取ai回复，流式输出回复
def get_ai_response2_stream(model, messages, who):
    start_time = time.time()

    # print(f"正在向deepseek发送关于{who}的请求")
    # print(f"请求的模型为{model}")

    '''
    print("请求内容为:\n")
    for m in messages:
        print(m)
    '''

    client = OpenAI(api_key=api_key[0], base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    )

    completion_tokens = 0
    cache_hit_tokens = 0
    cache_miss_tokens = 0
    cost = 0

    reasoning_content = ""
    content = ""

    one_time = False
    one_time2 = False

    all_chunk = []

    for chunk in response:
        all_chunk.append(chunk)
        # R1模型
        if hasattr(chunk.choices[0].delta, "reasoning_content"):
            if chunk.choices[0].delta.reasoning_content:
                if chunk.choices[0].delta.reasoning_content:
                    if not one_time:
                        # print("\n思维链:")
                        one_time = True

                    reasoning_content += chunk.choices[0].delta.reasoning_content
                    # sys.stdout.write(chunk.choices[0].delta.reasoning_content)
                    # sys.stdout.flush()
            else:
                if chunk.choices[0].delta.content:
                    if not one_time2:
                        # print("\n\n最终回复:")
                        one_time2 = True

                    content += chunk.choices[0].delta.content
                    # sys.stdout.write(chunk.choices[0].delta.content)
                    # sys.stdout.flush()
        # chat模型
        else:
            if chunk.choices[0].delta.content:
                if not one_time2:
                    # print("\n\n最终回复:")
                    one_time2 = True

            content += chunk.choices[0].delta.content
            # sys.stdout.write(chunk.choices[0].delta.content)
            # sys.stdout.flush()

    last_chunk_content = str(all_chunk[-1:])

    tokens_list = get_tokens_info(last_chunk_content)

    if tokens_list:
        completion_tokens = int(tokens_list["completion_tokens"])
        cache_hit_tokens = int(tokens_list["prompt_cache_hit_tokens"])
        cache_miss_tokens = int(tokens_list["prompt_cache_miss_tokens"])
        # print(f"\n\ncompletion_tokens:{completion_tokens}")
        # print(f"prompt_cache_hit_tokens:{cache_hit_tokens}")
        # print(f"prompt_cache_miss_tokens:{cache_miss_tokens}\n")

    cost = (0.3 * cache_hit_tokens + 2 * cache_miss_tokens + 3 * completion_tokens) / 1000000

    # print(f"本次请求消费{cost}元\n")

    '''
    thread = threading.Thread(target=balances_info)
    thread.start()
    '''

    end_time = time.time()
    total_time = end_time - start_time
    # print(f"本次请求执行时间为{total_time}s\n")

    if reasoning_content != "":
        '''
        full_content = f'思维链:\n{reasoning_content}\n\n最终回复:{content}'

        with open(f"{relative_path}/final_response.txt", "w", encoding='utf-8') as file:
            file.write(full_content)
        '''

        return {"reasoning_content":reasoning_content, "content":content, "cost":cost,
                "completion_tokens":completion_tokens,
                "prompt_cache_hit_tokens":cache_hit_tokens,
                "prompt_cache_miss_tokens":cache_miss_tokens}
    else:
        '''
        full_content = f'最终回复:{content}'

        with open(f"{relative_path}/final_response.txt", "w", encoding='utf-8') as file:
            file.write(full_content)
        '''

        return {"content":content, "cost":cost,
                "completion_tokens": completion_tokens,
                "prompt_cache_hit_tokens": cache_hit_tokens,
                "prompt_cache_miss_tokens": cache_miss_tokens
                }

# 异步获取ai回复，非流式输出显示
async def get_ai_response(model, messages, who):
    start_time = time.time()

    print(f"正在向deepseek发送关于{who}的请求")
    print(f"请求的模型为{model}")
    '''
    print("请求内容为:\n")
    for m in messages:
        print(m)
    '''

    response = None

    client = OpenAI(api_key=api_key[0], base_url="https://api.deepseek.com")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=4096
        )
    except Exception as e:
        print(f"获取deepseek回复时出错!{e}")

    reasoning_content = ""

    if hasattr(response.choices[0].message, "reasoning_content"):
        reasoning_content = response.choices[0].message.reasoning_content

    content = response.choices[0].message.content

    print("\n思维链:\n" + reasoning_content)
    print("\n最终回复:\n" + content)

    completion_tokens = 0
    cache_hit_tokens = 0
    cache_miss_tokens = 0
    cost = 0

    try:
        completion_tokens = int(response.usage.completion_tokens)
        cache_hit_tokens = int(response.usage.prompt_cache_hit_tokens)
        cache_miss_tokens = int(response.usage.prompt_cache_miss_tokens)
        print("completion_tokens:" + str(response.usage.completion_tokens))
        print("prompt_cache_hit_tokens:" + str(response.usage.prompt_cache_hit_tokens))
        print("prompt_cache_miss_tokens:" + str(response.usage.prompt_cache_miss_tokens))
    except Exception as e:
        print(f"获取tokens相关信息失败!{e}\n")
        pass

    cost = (0.3 * cache_hit_tokens + 2 * cache_miss_tokens + 3 * completion_tokens) / 1000000

    # print(f"本次请求消费{cost}元\n")

    thread = threading.Thread(target=balances_info)
    thread.start()

    end_time = time.time()
    total_time = end_time - start_time
    # print(f"本次请求执行时间为{total_time}s\n")

    if reasoning_content != "":
        return {"reasoning_content":reasoning_content, "content":content}
    else:
        return {"content":content}

# 异步获取ai回复，流式输出显示
async def get_ai_response_stream(model, messages, who):
    start_time = time.time()

    print(f"正在向deepseek发送关于{who}的请求")
    print(f"请求的模型为{model}")

    '''
    print("请求内容为:\n")
    for m in messages:
        print(m)
    '''

    client = OpenAI(api_key=api_key[0], base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    completion_tokens = 0
    cache_hit_tokens = 0
    cache_miss_tokens = 0
    cost = 0

    reasoning_content = ""
    content = ""

    one_time = False
    one_time2 = False

    all_chunk = []

    for chunk in response:
        all_chunk.append(chunk)
        # R1模型
        if hasattr(chunk.choices[0].delta, "reasoning_content"):
            if chunk.choices[0].delta.reasoning_content:
                if chunk.choices[0].delta.reasoning_content:
                    if not one_time:
                        print("\n思维链:")
                        one_time = True

                    reasoning_content += chunk.choices[0].delta.reasoning_content
                    sys.stdout.write(chunk.choices[0].delta.reasoning_content)
                    sys.stdout.flush()
            else:
                if chunk.choices[0].delta.content:
                    if not one_time2:
                        print("\n\n最终回复:")
                        one_time2 = True

                    content += chunk.choices[0].delta.content
                    sys.stdout.write(chunk.choices[0].delta.content)
                    sys.stdout.flush()
        # chat模型
        else:
            content += chunk.choices[0].delta.content
            sys.stdout.write(chunk.choices[0].delta.content)
            sys.stdout.flush()

    last_chunk_content = str(all_chunk[-1:])

    tokens_list = get_tokens_info(last_chunk_content)

    if tokens_list:
        completion_tokens = int(tokens_list["completion_tokens"])
        cache_hit_tokens = int(tokens_list["prompt_cache_hit_tokens"])
        cache_miss_tokens = int(tokens_list["prompt_cache_miss_tokens"])
        print(f"\n\ncompletion_tokens:{completion_tokens}")
        print(f"prompt_cache_hit_tokens:{cache_hit_tokens}")
        print(f"prompt_cache_miss_tokens:{cache_miss_tokens}\n")

    cost = (0.3 * cache_hit_tokens + 2 * cache_miss_tokens + 3 * completion_tokens) / 1000000

    print(f"本次请求消费{cost}元\n")

    thread = threading.Thread(target=balances_info)
    thread.start()

    end_time = time.time()
    total_time = end_time - start_time
    print(f"本次请求执行时间为{total_time}s\n")

    if reasoning_content != "":
        full_content = f'completion_tokens:{completion_tokens}\nprompt_cache_hit_tokens:{cache_hit_tokens}\nprompt_cache_miss_tokens:{cache_miss_tokens}\n\n本次请求消费{cost}元\n\n思维链:\n{reasoning_content}\n\n最终回复:\n{content}'

        with open(f"{relative_path}/final_response.txt", "w", encoding='utf-8') as file:
            file.write(full_content)

        return {"reasoning_content": reasoning_content, "content": content}
    else:
        full_content = f'completion_tokens:{completion_tokens}\nprompt_cache_hit_tokens:{cache_hit_tokens}\nprompt_cache_miss_tokens:{cache_miss_tokens}\n\n本次请求消费{cost}元\n\n最终回复:\n{content}'

        with open(f"{relative_path}/final_response.txt", "w", encoding='utf-8') as file:
            file.write(full_content)

        return {"content": content}
