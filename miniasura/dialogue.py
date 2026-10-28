# V2.2 对话系统 —— 数据驱动（dialogue.txt 进 mpak），播放走 io 抽象（CLI/GUI 通用）。
# 不存状态：看了没有由任务层记（talk 事件），本模块只管"按序播放 + 跳过"。
def load(text):
    """dialogue.txt → {id: [行]}；# 开头 = 舞台指示（旁白/动作）。"""
    blocks, cur = {}, None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("[") and s.endswith("]"):
            cur = s[1:-1]
            blocks[cur] = []
        elif cur:
            blocks[cur].append(s)
    return blocks


def play(io, blocks, did, interactive=True):
    """播放一段对话。返回是否完整看完（输入 s 略过 → False，talk 任务不推进）。"""
    lines = blocks.get(did)
    if not lines:
        io.say(f"（找不到对话 {did}——检查 dialogue.txt 与引用方）")
        return False
    for ln in lines:
        io.say(("    —— " + ln[1:].strip()) if ln.startswith("#") else "  " + ln)
    if not interactive:
        return True
    if io.ask("（回车看完 / 输入 s 略过）> ").strip().lower() == "s":
        io.say("（你略过了这段话。）")
        return False
    return True


def block_text(blocks, did):
    """重看用：把一段对话拼成纯文本（GUI 弹窗展示，不推进任务）。"""
    lines = blocks.get(did)
    if not lines:
        return f"（找不到对话 {did}）"
    return "\n".join(
        ("—— " + ln[1:].strip()) if ln.startswith("#") else ln for ln in lines)
