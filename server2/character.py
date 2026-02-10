import re

def change_character_setting(character_setting_str, likeability, who):
    likeability_str = ""
    if 0 <= likeability <= 5:
        likeability_str = f"你对{who}恨之入骨，恨不得生啖其肉"
    if 6 <= likeability <= 10:
        likeability_str = f"{who}就像你的杀父仇人，手刃仇敌方快哉"
    if 11 <= likeability <= 20:
        likeability_str = f"{who}是你的眼中钉，肉中刺"
    if 21 <= likeability <= 25:
        likeability_str = f"你十分讨厌{who}"
    if 26 <= likeability <= 29:
        likeability_str = f"你很讨厌{who}"
    if 30 <= likeability <= 35:
        likeability_str = f"你有些讨厌{who}"
    if 36 <= likeability <= 40:
        likeability_str = f"你有些看不惯{who}，但不会说出来"
    if 41 <= likeability <= 50:
        likeability_str = f"你对{who}观感不是太好，但还是能普通对待亦或者真的只是完全普通的路人程度的观感"
    if 51 <= likeability <= 60:
        likeability_str = f"你对{who}观感还不错"
    if 61 <= likeability <= 70:
        likeability_str = f"{who}是你的普通朋友"
    if 71 <= likeability <= 80:
        likeability_str = f"{who}是和你关系比较好的朋友"
    if 81 <= likeability <= 85:
        likeability_str = f"{who}是你非常要好的朋友"
    if 86 <= likeability <= 89:
        likeability_str = f"{who}是你最好的朋友，是你的大亲友"
    if 90 <= likeability <= 92:
        likeability_str = f"你和{who}的关系是亲友以上恋爱未满，换成友情就是知音"
    if 93 <= likeability <= 94:
        likeability_str = f"你对{who}十分有好感，快要恋爱的程度，或者是十分要好的知音"
    if 95 <= likeability <= 96:
        likeability_str = f"你和{who}已经恋爱了，亦或者说是生死兄弟"
    if 97 <= likeability <= 98:
        likeability_str = f"你和{who}坠入爱河不可自拔，换成友情就是伯牙子期那种程度的友情"
    if 99 <= likeability <= 100:
        likeability_str = f"你对{who}的爱就像人类对于爱情的最高程度的爱，亦或者到了生死不离程度的友情"

    pattern = r'# 角色经历\n'
    if re.search(pattern, character_setting_str):
        character_setting_str = re.sub(pattern, f'# 角色经历\n{likeability_str}', character_setting_str)

    return character_setting_str
