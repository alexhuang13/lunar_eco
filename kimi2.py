#!/usr/bin/env python3
"""
kimi2 —— 一个会记住历史的命令行 Claude Agent。

历史会自动保存在 ~/.kimi2/history.json,
每次启动自动加载,所以它能记住你之前所有的对话。

对话中可用的命令:
    /help     查看帮助
    /reset    清空所有历史(包括硬盘上保存的),重新开始
    /system   设定/修改 Agent 的角色
    /save     把当前对话另存为一个 txt 文件
    /exit     退出(quit / 退出 也可以)
"""

import os
import sys
import json
import datetime
import anthropic

# ---------- 配置 ----------
MODEL = "claude-opus-4-7"
MAX_TOKENS = 16000
BASE_URL = "https://api.openai-next.com"
DEFAULT_SYSTEM = "你是一个友好、务实的中文助手,回答清晰、直接、有条理。你能记住与用户之前的所有对话。"

# 历史文件就存在本脚本所在的同一个文件夹里(自包含,方便搬运/备份)
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
# --------------------------


def get_client():
    api_key = os.environ.get("VECTRUST_API_KEY")
    if not api_key:
        print("没有找到 API Key。请先设置环境变量 VECTRUST_API_KEY。")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key, base_url=BASE_URL)


def load_history():
    """启动时从硬盘读取历史。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("system", DEFAULT_SYSTEM), data.get("messages", [])
        except Exception:
            pass
    return DEFAULT_SYSTEM, []


def persist(system_prompt, messages):
    """每轮对话后把历史写回硬盘。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"system": system_prompt, "messages": messages},
                      f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("(历史保存失败: %s)" % e)


def print_help():
    print("""
可用命令:
  /help     查看本帮助
  /reset    清空所有历史(含硬盘保存),重新开始
  /system   设定/修改 Agent 的角色
  /save     把当前对话另存为 txt
  /exit     退出(quit / 退出 也可以)
""")


def export_txt(system_prompt, messages):
    if not messages:
        print("(对话还是空的)")
        return
    fname = "chat_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write("【System】" + system_prompt + "\n\n")
        for m in messages:
            who = "你" if m["role"] == "user" else "Claude"
            f.write("【%s】%s\n\n" % (who, m["content"]))
    print("已另存到 %s" % fname)


def main():
    client = get_client()
    system_prompt, messages = load_history()

    print("=" * 52)
    print(" kimi2 已启动 (模型: %s)" % MODEL)
    if messages:
        print(" 已加载历史对话 %d 条,我记得我们之前聊过的内容。" % len(messages))
    print(" 输入 /help 查看命令,输入 /exit 退出")
    print("=" * 52 + "\n")

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!历史已保存,下次还记得。")
            break

        if not user_input:
            continue

        low = user_input.lower()
        if low in ("/exit", "quit", "exit", "退出"):
            print("再见!历史已保存,下次还记得。")
            break
        if low == "/help":
            print_help()
            continue
        if low == "/reset":
            messages = []
            persist(system_prompt, messages)
            print("所有历史已清空(硬盘上的也清了)。\n")
            continue
        if low == "/system":
            new_sys = input("请输入新的角色设定: ").strip()
            if new_sys:
                system_prompt = new_sys
                persist(system_prompt, messages)
                print("角色已更新(历史保留)。\n")
            continue
        if low == "/save":
            export_txt(system_prompt, messages)
            continue

        messages.append({"role": "user", "content": user_input})
        print("Claude: ", end="", flush=True)

        reply = ""
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    reply += text
            print("\n")
            messages.append({"role": "assistant", "content": reply})
            persist(system_prompt, messages)   # 每轮都存,随时退出都不丢
        except Exception as e:
            print("\n出错了: %s\n" % e)
            messages.pop()


if __name__ == "__main__":
    main()