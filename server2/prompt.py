import os
import re
from datetime import datetime

from character import *
from deepseek import *
from memory import *
from translation import *
from global_variable import *

# 获取当前文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建相对路径
relative_path = os.path.join(current_dir)

# 是否已读取过人设
get_character_prompt = False
# 是否已读取过Translation部分prompt
get_translation_prompt = False
# 是否已读取过人设(群聊)
get_character_prompt_in_group = False
# 是否已读取过Translation部分prompt(group)
get_translation_prompt_in_group = False

# 人设文本
character_prompt = ""
# Translation部分文本
translation_prompt = ""
# 人设文本(群聊)
character_prompt_in_group = ""
# Translation部分文本(群聊)
translation_prompt_in_group = ""

# 重要任务处理是否成功完成
task_finished_status = 0

def get_task_status():
    return task_finished_status

# 系统提示词(群聊):
def system_prompt_in_group(who):
    global get_character_prompt_in_group
    global character_prompt_in_group

    temp_character_prompt = ""

    if not get_character_prompt_in_group:
        with open(f"{relative_path}/设定(group).txt", "r", encoding='utf-8') as file:
            character_prompt_in_group = file.read()

    if character_prompt_in_group != "":
        temp_character_prompt = character_prompt_in_group

    # 将设定中的所有{assistant}变为当前的assistant名字
    pattern = r'{assistant}'
    temp_character_prompt = re.sub(pattern, current_assistant[0], temp_character_prompt)

    # 在用户相关说明后添加当前在和谁对话
    pattern = r"# 角色扮演要求"
    if re.search(pattern, temp_character_prompt):
        if who == "摆烂Jo":
            temp_character_prompt = re.sub(pattern, f"# 角色扮演要求\n你正在回复的用户是{who}\n", temp_character_prompt)
        else:
            temp_character_prompt = re.sub(pattern, f"# 角色扮演要求\n你正在回复的用户是{who}, they are not 摆烂Jo, so your behaviors should be cautious!\n", temp_character_prompt)

    return temp_character_prompt

# 系统提示词
def system_prompt(who):
    global get_character_prompt
    global character_prompt

    temp_character_prompt = ""

    if not get_character_prompt:
        if current_assistant[0] == 'Bandit':
            if app_environment[0] == 0:
                with open(f"{relative_path}/设定.txt", "r", encoding='utf-8') as file:
                    character_prompt = file.read()
            else:
                with open(f"{relative_path}/设定2.txt", "r", encoding='utf-8') as file:
                    character_prompt = file.read()
        else:
            with open(f"{relative_path}/设定({current_assistant[0]}).txt", "r", encoding='utf-8') as file:
                character_prompt = file.read()

            if enable_likeability[0] == 1:
                character_prompt = change_character_setting(character_prompt, current_likeability[0], user_name[0])

    if character_prompt != "":
        temp_character_prompt = character_prompt

    # 将设定中的所有{assistant}变为当前的assistant名字
    pattern = r'{assistant}'
    temp_character_prompt = re.sub(pattern, current_assistant[0], temp_character_prompt)

    # 在用户相关说明后添加当前在和谁对话
    pattern = r'# 用户相关说明'
    if re.search(pattern, temp_character_prompt):
        if who == "摆烂Jo" and current_assistant[0] == "Bandit":
            temp_character_prompt = re.sub(pattern, f"# 用户相关说明\n你正在和{who}对话\n", temp_character_prompt)
        if who != "摆烂Jo" and current_assistant[0] == "Bandit":
            temp_character_prompt = re.sub(pattern, f"# 用户相关说明\n你正在和{who}对话, they are not 摆烂Jo, so your behaviors should be cautious!\n", temp_character_prompt)
        if current_assistant[0] != "Bandit":
            temp_character_prompt = re.sub(pattern, f"# 用户相关说明\n你正在和{who}对话\n", temp_character_prompt)

    return temp_character_prompt

# Translation部分prompt(不分段获取)
def get_translation_part2(memories, important_info_content, num, user_content, assistant_content, who, assistant):
    global get_translation_prompt
    global translation_prompt
    global task_finished_status

    task_finished_status = 0

    with open(f"{relative_path}/Translation部分prompt.txt", "r", encoding='utf-8') as file:
        translation_prompt = file.read()

    # 转换所有的{assistant}
    pattern = r'{who}'
    if re.search(pattern, translation_prompt):
        translation_prompt = re.sub(pattern, assistant, translation_prompt)

    prompt = [{"role": "system", "content": translation_prompt}]
    prompt.append({"role": "assistant", "content": '已理解'})

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    part2 = [f"当前对话的时间为{timestamp}\n"]
    part2_text = ""
    part2.append("# 完整的对话内容\n")

    history_content = ""

    if len(memories) > num:
        temp_memories = memories[-num:]
        for idx, m in enumerate(temp_memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"
    else:
        for idx, m in enumerate(memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"

    part2.append(history_content)
    part2.append("# 需要注意到的重要信息\n")
    part2.append(f"{important_info_content}\n")
    part2.append("用户新的消息:\n")
    part2.append(f"{user_content}\n")
    part2.append("你的回复:\n")
    part2.append(f"{assistant_content}\n")

    for p in part2:
        part2_text += p

    prompt.append({"role": "user", "content": part2_text})
    # 2025/8/20 公益站已无法打开
    # 从公益站获取回复，按次数收费减少开销，速度也会快一点
    # print("正在等待处理重要信息...\n")

    result = {}

    try:
        # result = get_ai_response3_stream("DeepSeek-R1-0528", prompt, who)
        # result = get_ai_response2_stream(model2[0], prompt, who)
        result = get_ai_response2_stream("deepseek-reasoner", prompt, who)
        task_finished_status = 1

        with open(f"{relative_path}/p_result.txt", "w", encoding='utf-8') as file:
            full_content = f'本次请求消费{result["cost"]}元\n\n{result["content"]}'
            file.write(full_content)
    except Exception as e:
        task_finished_status = 404
        print(f"处理重要信息失败!{e}")

    translation = ""
    pattern = r'[\({]Translation[:：]([\s\S]*)[\)}]'
    if re.search(pattern, result["content"]):
        # 确保Translation中不含有None
        if 'None' not in re.search(pattern, result["content"]).group():
            translation = re.search(pattern, result["content"]).group()
            translation = re.sub(pattern, r'\1', translation)

            # 去掉translation中多余的符号
            pattern = r'[{}]'
            translation = re.sub(pattern, r'', translation)

            print("获取到的翻译:" + translation)

    if len(translation) > 0:
        get_important_info_and_rewrite2(who, translation, current_assistant[0])

# Translation部分prompt(分段获取)
async def get_translation_part(memories, important_info_content, num, user_content, assistant_content, who, assistant, read_index):
    global get_translation_prompt
    global translation_prompt
    global task_finished_status

    # 执行3次Translation部分读取后重置
    if task_finished_status >= 3:
        task_finished_status = 0

    '''
    with open(f"{relative_path}/Translation部分prompt{read_index}.txt", "r", encoding='utf-8') as file:
        translation_prompt = file.read()
    '''

    translation_prompt = ''
    if read_index == 1:
        translation_prompt = translation_part_prompt1()
    if read_index == 2:
        translation_prompt = translation_part_prompt2()
    if read_index == 3:
        translation_prompt = translation_part_prompt3()

    # 转换所有的{assistant}
    pattern = r'{who}'
    if re.search(pattern, translation_prompt):
        translation_prompt = re.sub(pattern, assistant, translation_prompt)

    prompt = [{"role": "system", "content": translation_prompt}]
    prompt.append({"role": "assistant", "content": '已理解'})

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    part2 = [f"当前对话的时间为{timestamp}\n"]
    part2_text = ""
    part2.append("# 完整的对话内容\n")

    history_content = ""

    if len(memories) > num:
        temp_memories = memories[-num:]
        for idx, m in enumerate(temp_memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"
    else:
        for idx, m in enumerate(memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"

    part2.append(history_content)
    part2.append("# 需要注意到的重要信息\n")
    part2.append(f"{important_info_content}\n")
    part2.append("用户新的消息:\n")
    part2.append(f"{user_content}\n")
    part2.append("你的回复:\n")
    part2.append(f"{assistant_content}\n")

    for p in part2:
        part2_text += p

    prompt.append({"role": "user", "content": part2_text})
    # print("正在等待处理重要信息...\n")

    result = {}

    try:
        result = await get_ai_response("deepseek-chat", prompt, who)
        task_finished_status += 1

        with open(f"{relative_path}/p{read_index}_result.txt", "w", encoding='utf-8') as file:
            full_content = f'completion_tokens:{result["completion_tokens"]}\nprompt_cache_hit_tokens:{result["prompt_cache_hit_tokens"]}\nprompt_cache_miss_tokens:{result["prompt_cache_miss_tokens"]}\n\n本次请求消费{result["cost"]}元\n\n{result["content"]}'
            file.write(full_content)
    except Exception as e:
        task_finished_status = 404
        print(f"处理重要信息失败!{e}")

    translation = ""
    pattern = r'[\({]Translation[:：]([\s\S]*)[\)}]'

    if result.get('content'):
        if re.search(pattern, result["content"]):
            # 确保Translation中不含有None
            if 'None' not in re.search(pattern, result["content"]).group():
                translation = re.search(pattern, result["content"]).group()
                translation = re.sub(pattern, r'\1', translation)

                # 去掉translation中多余的符号
                pattern = r'[{}]'
                translation = re.sub(pattern, r'', translation)

                # print("获取到的翻译:" + translation)

        if len(translation) > 0:
            get_important_info_and_rewrite2(who, translation, current_assistant[0])

# 示例对话提示词
def example_prompt(who):
    example_content_prompt = f"以下是关于{who}和你的示例对话，除了必要的Translation部分，你不需要模仿它们。\n"

    return example_content_prompt

# 多事件引用判断提示词:
def many_events_needed_prompt(new_message):
    events_prompt = []
    events_prompt.append("你正在和某个用户对话，你是这位用户的对象。\n")
    events_prompt.append("这位用户给你发送了新消息，请你判断你给这位用户的回复是否大概率需要提到两个及以上的已发生过的事情。\n")
    events_prompt.append("你需要输出'是'或'否'，并解释其原因。\n\n")
    events_prompt.append("# 输出示例\n1.\n")
    events_prompt.append("用户新的消息：Do you still remember what we have done today?\n")
    events_prompt.append("你的输出：是，原因：由于你是这位用户的对象，今天大概率一起和这位用户一起做了很多事情。\n")
    events_prompt.append("2.\n用户新的消息：Nice to meet you, mate!\n")
    events_prompt.append("你的输出：否，原因：简单问候大概率不需要提到很多事情。\n\n")
    events_prompt.append("# 要处理的用户的新的消息\n")
    events_prompt.append(new_message)

    all_ep = ""

    for e in events_prompt:
        all_ep += e

    return all_ep

# 时间跨度提取提示词:
def get_time_span_prompt(new_message, memories, num, who):
    # 今天/昨天/上个星期/上个月/去年/n天前/n个星期前/n个月前/n年前
    time_span_prompt = []
    time_span_prompt.append("你正在和某个用户对话。\n")
    time_span_prompt.append("这位用户给你发送了新消息，你接下来给这位用户的回复中可能需要提及某个具体时间段内的事情。")
    time_span_prompt.append("请你从'完整的对话内容'以及'用户新的消息'中提取你最可能需要参考的某个具体时间段，只需要输出'时间关键词'中的一个关键词！")
    time_span_prompt.append("# 时间关键词\n")
    time_span_prompt.append("今天/昨天/上个星期/上个月/去年/n天前/n个星期前/n个月前/n年前\n\n")
    time_span_prompt.append("# 注意事项\n")
    time_span_prompt.append("1. 如果提取出的时间信息包含n，请尝试将n转换为具体的阿拉伯数字！如果无法转换为具体的阿拉伯数字，则不需要转换n！\n")
    time_span_prompt.append("2. 如果无法提取出任何时间信息，直接输出'无'这个汉字")
    time_span_prompt.append("# 输出示例\n1.\n")
    time_span_prompt.append("用户新的消息: Do you still remember what we have done yesterday?\n")
    time_span_prompt.append("你的输出：昨天\n")
    time_span_prompt.append("2.\n用户新的消息: I guess he did those things three days ago.\n")
    time_span_prompt.append("你的输出: 3天前\n")
    time_span_prompt.append("3.\n用户新的消息: I don't know, maybe it happened a few weeks ago.\n")
    time_span_prompt.append("你的输出: n个星期前\n")
    time_span_prompt.append("4.\n用户新的消息: Nice to meet you!\n")
    time_span_prompt.append("你的输出: 无\n\n")

    time_span_prompt.append("我会在下一次对话中给你提供'完整的对话内容'以及'用户新的回复'，如果你完全理解了上述内容，请回复'已理解'。")

    time_span_prompt_str = ""

    for tsp in time_span_prompt:
        time_span_prompt_str += tsp

    prompt = [{"role": "system", "content": time_span_prompt_str}]
    prompt.append({"role": "assistant", "content": '已理解'})

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    part2 = [f"当前对话的时间为{timestamp}\n"]
    part2_text = ""
    part2.append("# 完整的对话内容\n")

    history_content = ""

    if len(memories) > num:
        temp_memories = memories[-num:]
        for idx, m in enumerate(temp_memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"
    else:
        for idx, m in enumerate(memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"

    part2.append(history_content)
    part2.append("用户新的消息:\n")
    part2.append(f"{new_message}\n")

    for p in part2:
        part2_text += p

    prompt.append({"role": "user", "content": part2_text})

    try:
        # result = get_ai_response3_stream("DeepSeek-R1-0528", prompt, who)
        # result = get_ai_response2_stream(model2[0], prompt, who)
        result = get_ai_response2_stream("deepseek-chat", prompt, who)

        with open(f"{relative_path}/time_span.txt", "w", encoding='utf-8') as file:
            full_content = f'completion_tokens:{result["completion_tokens"]}\nprompt_cache_hit_tokens:{result["prompt_cache_hit_tokens"]}\nprompt_cache_miss_tokens:{result["prompt_cache_miss_tokens"]}\n\n本次请求消费{result["cost"]}元\n\n{result['content']}'
            file.write(full_content)

        return result["content"]
    except Exception as e:
        print(f"时间跨度提取失败!{e}")

        return '无'

# 修改好感度
async def change_likeability(new_message, your_reply, likeability, memories, num, who):
    likeability_prompt = []
    likeability_prompt.append("你正在和某个用户对话。\n")
    likeability_prompt.append("这位用户给你发送了新消息，你也作出了相应的回复。\n")
    likeability_prompt.append("请参考'完整的对话内容'、'用户新的消息'以及'你的回复'，结合'好感度数值及其说明'输出你对这位用户的最新的好感度数值。\n\n")
    likeability_prompt.append("# 好感度数值及其说明\n")
    likeability_prompt.append("0~5 你对这位用户恨之入骨，恨不得生啖其肉/6~10 这位用户就像你的杀父仇人，手刃仇敌方快哉/11~20 这位用户是你的眼中钉，肉中刺/")
    likeability_prompt.append("21~25 你十分讨厌这位用户/26~30 你很讨厌这位用户/31~35 你有些讨厌这位用户/")
    likeability_prompt.append("36~40 你有些看不惯这位用户，但并不会说出来/41~50 你对这位用户观感不是太好，但还是能普通对待亦或者真的只是完全普通的路人程度的观感/")
    likeability_prompt.append("51~60 你对这位用户观感还不错/61~70 这位用户是你的普通朋友/")
    likeability_prompt.append("71~80 这位用户是和你关系比较好的朋友/81~85 这位用户是你非常要好的朋友/86~89 这位用户是你最好的朋友，是你的大亲友/90~92 你和这位用户的关系是亲友以上恋爱未满，换成友情就是知音/")
    likeability_prompt.append("93~94 你对这位用户十分有好感，快要恋爱的程度，或者是十分要好的知音/95~96 你和这位用户已经恋爱了，亦或者说是生死兄弟/")
    likeability_prompt.append("97~98 你和这位用户坠入爱河不可自拔，伯牙子期那种程度的友情/99~100 你对这位用户的爱就像人类对于爱情的最高程度的爱，亦或者到了生死不离程度的友情")
    likeability_prompt.append("# 注意事项\n")
    likeability_prompt.append("1. 你只需要输出一个具体的整数，即好感度数值！\n")
    likeability_prompt.append("2. 好感度数值的最低值为0，最高值为100\n，好感度数值越高，说明你和这位用户的关系越好")
    likeability_prompt.append("3. 在本次对话结束后，你可以增加或减少你对这位用户的好感度数值，也可以保持该数值不变\n")
    likeability_prompt.append("4. 最终输出的好感度数值与'在本次对话之前，你对这位用户的好感度数值'的绝对值差值必须小于等于5！\n\n")

    likeability_prompt.append(
        "我会在下一次对话中给你提供'完整的对话内容'、'用户新的回复'以及'你的回复'，如果你完全理解了上述内容，请回复'已理解'。")

    likeability_prompt_str = ""

    for lp in likeability_prompt:
        likeability_prompt_str += lp

    prompt = [{"role": "system", "content": likeability_prompt_str}]
    prompt.append({"role": "assistant", "content": '已理解'})

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    part2 = [f"当前对话的时间为{timestamp}\n"]
    part2_text = ""
    part2.append("# 完整的对话内容\n")

    history_content = ""

    if len(memories) > num:
        temp_memories = memories[-num:]
        for idx, m in enumerate(temp_memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"
    else:
        for idx, m in enumerate(memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"

    part2.append(history_content)
    part2.append(f"在本次对话之前，你对这位用户的好感度数值:{likeability}\n")
    part2.append("用户新的消息:\n")
    part2.append(f"{new_message}\n")
    part2.append("你的回复:\n")
    part2.append(f"{your_reply}\n")

    for p in part2:
        part2_text += p

    prompt.append({"role": "user", "content": part2_text})

    try:
        result = await get_ai_response("deepseek-chat", prompt, who)

        pattern = r'\d+'
        if re.search(pattern, result['content']):
            temp_likeability = re.search(pattern, result['content']).group()
            # 检查输出的好感度数值与上次的差值，差值异常则保持好感度数值不变
            if -5 <= current_likeability[0] - int(temp_likeability) <= 5:
                current_likeability[0] = int(temp_likeability)

                if current_likeability[0] > 100:
                    current_likeability[0] = 100
                if current_likeability[0] < 0:
                    current_likeability[0] = 0

                with open(f"{relative_path}/private/{who}/likeability({current_assistant[0]}).txt", "w", encoding='utf-8') as file:
                    full_content = temp_likeability
                    file.write(full_content)

                with open(f"{relative_path}/likeability.txt", "w", encoding='utf-8') as file:
                    full_content = f'completion_tokens:{result["completion_tokens"]}\nprompt_cache_hit_tokens:{result["prompt_cache_hit_tokens"]}\nprompt_cache_miss_tokens:{result["prompt_cache_miss_tokens"]}\n\n本次请求消费{result["cost"]}元\n\n{result['content']}'
                    file.write(full_content)

        return current_likeability[0]
    except Exception as e:
        print(f"修改好感度失败!{e}")

        return '无'

# 情绪识别
def emotion_recognition(memories, num, user_content, assistant_content, who):
    emotion_prompt = []
    emotion_prompt.append("你是一个善于识别情绪的助手，你必须按照'识别规则'来正确识别用户的情绪！\n")
    emotion_prompt.append("# 识别规则\n")
    emotion_prompt.append("你正在和一个用户对话，请首先注意'你的回复'，然后参考'完整的对话内容'，将'你的回复'中所包含的最主要的情绪归类到'情绪分类'中，只需要输出'情绪分类'中的一个类别！\n\n")
    emotion_prompt.append("# 情绪分类\n")
    # admiration(钦佩) adoration(崇拜) aesthetic appreciation(审美欣赏) amusement(娱乐)
    # anger(愤怒) anxiety(焦虑) awe(敬畏) awkwardness(尴尬) boredom(厌倦)
    # calmness(冷静) confusion(困惑) craving(渴望) disgust(厌恶)
    # empathic pain(共情之痛) entrancement(魅惑) excitement(兴奋) fear(恐惧)
    # horror(恐怖) interest(兴趣) joy(快乐) nostalgia(怀旧) relief(轻松)
    # romance(浪漫) sadness(悲伤) satisfaction(满足) sexual(性欲)
    # surprise(惊喜)
    emotion_prompt.append("admiration/adoration/aesthetic appreciation/amusement/")
    emotion_prompt.append("anger/anxiety/awe/awkwardness/disgust/")
    emotion_prompt.append("calmness/confusion/craving/disgust/")
    emotion_prompt.append("empathic pain/entrancement/excitement/fear/")
    emotion_prompt.append("horror/interest/joy/nostalgia/relief/")
    emotion_prompt.append("romance/sadness/satisfaction/sexual/")
    emotion_prompt.append("surprise\n\n")
    emotion_prompt.append("我会在下一次对话中给你提供'完整的对话内容'以及'用户新的消息'，如果你完全理解了上述内容，请回复'已理解'。")

    emotion_prompt_str = ""

    for ep in emotion_prompt:
        emotion_prompt_str += ep

    prompt = [{"role": "system", "content": emotion_prompt_str}]
    prompt.append({"role": "assistant", "content": '已理解'})

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    part2 = [f"当前对话的时间为{timestamp}\n"]
    part2_text = ""
    part2.append("# 完整的对话内容\n")

    history_content = ""

    if len(memories) > num:
        temp_memories = memories[-num:]
        for idx, m in enumerate(temp_memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"
    else:
        for idx, m in enumerate(memories):
            history_content += f"对话{idx + 1}:\n用户发送该消息的时间为:\n{m['timestamp']}\n用户的消息: \n{m['user_content']}\n你的回复: \n{m['assistant_content']}\n\n"

    part2.append(history_content)
    part2.append("用户新的消息:\n")
    part2.append(f"{user_content}\n")
    part2.append("你的回复:\n")
    part2.append(f"{assistant_content}\n")

    for p in part2:
        part2_text += p

    prompt.append({"role": "user", "content": part2_text})

    try:
        # result = get_ai_response3_stream("DeepSeek-R1-0528", prompt, who)
        # result = get_ai_response2_stream(model2[0], prompt, who)
        result = get_ai_response2_stream("deepseek-chat", prompt, who)

        with open(f"{relative_path}/emotion_recognition_result.txt", "w", encoding='utf-8') as file:
            file.write(result["content"])

        return result["content"]
    except Exception as e:
        print(f"识别情绪失败！{e}")

        return 'Failed!'

# 构建历史对话提示词
def generate_history_prompt(num):
    former_content_prompt = []
    former_content_prompt.append("我会在下一次对话中给你提供一些你和用户的历史对话内容。\n")
    former_content_prompt.append("你必须按照'处理历史对话内容的规则'来处理这些历史对话内容！\n")
    former_content_prompt.append(f"'对话1-{num}'已按照时间倒序排列。\n")
    former_content_prompt.append("# 处理历史对话内容的规则\n")
    former_content_prompt.append(f"-在没有任何有效信息的情况下，你需要从'对话1-{num}'中寻找有效信息。\n")
    former_content_prompt.append(
        "-如果在'对话1'中用户表明了要单独做其他事情，你就需要提取'对话1'的时间，并计算它与当前对话时间的间隔，如果间隔大于1个小时，你的回复应当包含类似'好久不见'的短语以及表达出对用户的关心。")
    former_content_prompt.append(
        f"-'对话{num+1}-{num+5}'的内容为'用户曾经说过的话'，如果用户新的回复与其中一段对话类似，你的回复可以包含类似'我记得你曾经说过这句话'的短语。\n")

    all_fcp = ""

    for fcp in former_content_prompt:
        all_fcp += fcp

    return all_fcp
