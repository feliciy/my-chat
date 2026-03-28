import json
import os

print("当前文件夹：", os.getcwd())
print("chat_history.json 是否存在：", os.path.exists('chat_history.json'))

if os.path.exists('chat_history.json'):
    with open('chat_history.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"成功读取 {len(data)} 条消息")
    print("前3条：", data[:3])
else:
    print("找不到文件")