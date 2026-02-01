# 切割文本
import re

# 是否为英文字母
def contains_alpha(s):
    return bool(re.search('[a-zA-Z]', s))

# 由于qq只能发送单次被动回复5条消息，尝试每n句话合并一下
def split_content2(content):
    # 将所有换行符转为空格
    # 考虑到换行符后面还有\s字符的情况
    pattern = r'\n+\s*'
    content = re.sub(pattern, r' ', content)

    # change:将句号、问号、感叹号、小写句号+空格(. 前面必须是非数字)(分割点后面必须为空白字符)等作为分隔点 (但保留这些标点)
    # . 前面是非数字的情况也可能是单词缩写(不好判断，不处理了)
    # 如果特殊符号(' " () [])中有分隔符，则不分割。(过于麻烦，不处理了)
    pattern = r'(\D\. )|([\!?]\s+)|([。！？])'
    parts = re.split(pattern, content)

    new_parts = []
    for p in parts:
        if p is not None:
            new_parts.append(p)

    parts = new_parts

    # 优化有举例回复的显示(1. XXX; 2. XXX)
    pattern = r'(\d\.)|(\d\. )'
    new_parts = []
    for p in parts:
        # \1会保留匹配值
        new_parts.append(re.sub(pattern, r'\n\1', p))

    parts = new_parts

    # 重新组合分割后的内容，保留标点符号
    merged_parts = []
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            merged_parts.append(parts[i] + parts[i + 1])
        else:
            merged_parts.append(parts[i])

    merged_parts2 = []
    for m in range(0, len(merged_parts) - 2, 2):
        merged_parts2.append(merged_parts[m] + merged_parts[m + 1])

    def append_last_elements(n):
        nonlocal merged_parts
        nonlocal merged_parts2

        if len(merged_parts) % n != 0:
            temp_merged_parts = ""
            for mp in range(len(merged_parts) % n):
                # 是英文回复的情况下，要加上空格
                if contains_alpha(merged_parts[-(mp + 1)][0]):
                    temp_merged_parts = merged_parts[-(mp + 1)] + ' ' + temp_merged_parts
                else:
                    temp_merged_parts = merged_parts[-(mp + 1)] + temp_merged_parts

            merged_parts2.append(temp_merged_parts)
        else:
            temp_merged_parts = ""
            for mp in range(n):
                # 是英文回复的情况下，要加上空格
                if contains_alpha(merged_parts[-(mp + 1)][0]):
                    temp_merged_parts = merged_parts[-(mp + 1)] + ' ' + temp_merged_parts
                else:
                    temp_merged_parts = merged_parts[-(mp + 1)] + temp_merged_parts

            merged_parts2.append(temp_merged_parts)

    append_last_elements(2)
    # 单次合并多少句话
    merge_sentence_num = 2

    # 合并后仍超过5句话的，尝试增大merge_sentence_num的值继续合并
    while len(merged_parts2) > 5:
        merge_sentence_num += 1

        merged_parts2 = []
        for m in range(0, len(merged_parts) - merge_sentence_num, merge_sentence_num):
            temp_merged_parts = ""
            for msn in range(merge_sentence_num):
                # 是英文回复的情况下，要加上空格
                if contains_alpha(merged_parts[m + msn][0]):
                    temp_merged_parts += f' {merged_parts[m + msn]}'
                else:
                    temp_merged_parts += merged_parts[m + msn]

            merged_parts2.append(temp_merged_parts)

        append_last_elements(merge_sentence_num)

    # 去掉长度为0的元素
    merged_parts3 = []
    for m in merged_parts2:
        if len(m) > 0:
            merged_parts3.append(m)

    return merged_parts3

def split_content(content):
    # 将所有换行符转为空格
    # 考虑到换行符前面以及后面还有\s字符的情况
    pattern = r'\s*\n+\s*'
    content = re.sub(pattern, r' ', content)

    # change:将句号、问号、感叹号、小写句号+空格(. 前面必须是非数字)(分割点后面必须为空白字符)等作为分隔点 (但保留这些标点)
    # . 前面是非数字的情况也可能是单词缩写(不好判断，不处理了)
    # 如果特殊符号(' " () [])中有分隔符，则不分割。(过于麻烦，不处理了)
    pattern = r'(\D\. )|([\!?]\s+)|([。！？])'
    parts = re.split(pattern, content)

    new_parts = []
    for p in parts:
        if p is not None:
            new_parts.append(p)

    parts = new_parts

    # 优化有举例回复的显示(1. XXX; 2. XXX)
    pattern = r'(\d\.)|(\d\. )'
    new_parts = []
    for p in parts:
        # \1会保留匹配值
        new_parts.append(re.sub(pattern, r'\n\1', p))

    parts = new_parts

    # 重新组合分割后的内容，保留标点符号
    merged_parts = []
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            merged_parts.append(parts[i] + parts[i + 1])
        else:
            merged_parts.append(parts[i])

    # 去掉长度为0的元素
    merged_parts2 = []
    for m in merged_parts:
        if len(m) > 0:
            merged_parts2.append(m)

    return merged_parts2
