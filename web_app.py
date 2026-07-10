"""何总销售助手 - 纯云端版"""
import streamlit as st
import json
from datetime import datetime
from core.knowledge import KnowledgeBase
from core.llm import llm
from core.history import qa_history, training, conversations

st.set_page_config(page_title="何总销售助手", page_icon="💼", layout="wide")

if "kb" not in st.session_state: st.session_state.kb = KnowledgeBase()
if "conv_name" not in st.session_state: st.session_state.conv_name = datetime.now().strftime("%Y-%m-%d")
if "messages" not in st.session_state:
    saved = conversations.load(st.session_state.conv_name)
    st.session_state.messages = saved or [{"role": "assistant", "content": "你好！我是何总销售知识助手。\n\n问任何TOB销售问题，我会结合何总方法论+医药行业场景给出答案 👇"}]

kb = st.session_state.kb
SYSTEM_PROMPT = f"""你是何总的销售知识助手，为山东朱氏药业TOB销售员提供实战指导。
知识来自抖音博主"何总"的销售培训内容。回答简洁有力，结合医药行业场景，引用何总金句。

## 何总销售知识库
{kb.format_for_prompt()}
"""

def save_conv():
    conversations.save(st.session_state.conv_name, st.session_state.messages)

# ─── Sidebar ──────────────────────────────
with st.sidebar:
    st.title("💼 何总销售助手")
    st.caption("山东朱氏药业 · 纯云端版")

    info = training.get()
    c1, c2 = st.columns(2)
    with c1: st.metric("🔥", f"{info['streak']}天")
    with c2: st.metric("⭐", f"{info['best_streak']}天")
    if not info["checked_in"]:
        if st.button("☀️ 打卡", type="primary", use_container_width=True):
            training.checkin()
            st.rerun()
    else:
        st.success("✅ 已打卡")

    st.divider()

    st.subheader("💬 会话")
    convs = conversations.list()
    current = st.session_state.conv_name
    if current not in convs: convs.insert(0, current)
    selected = st.selectbox("选择", convs, index=convs.index(current) if current in convs else 0, label_visibility="collapsed")
    if selected != current:
        st.session_state.conv_name = selected
        st.session_state.messages = conversations.load(selected) or [{"role": "assistant", "content": "你好 👇"}]
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        new_name = st.text_input("新建", placeholder="名称", label_visibility="collapsed")
        if new_name and st.button("➕", use_container_width=True):
            st.session_state.conv_name = new_name
            st.session_state.messages = [{"role": "assistant", "content": "新会话！"}]
            conversations.save(new_name, st.session_state.messages)
            st.rerun()
    with c2:
        if st.button("🗑️", use_container_width=True):
            conversations.delete(current)
            st.session_state.conv_name = datetime.now().strftime("%Y-%m-%d")
            st.session_state.messages = [{"role": "assistant", "content": "新会话 👇"}]
            st.rerun()

    st.divider()
    hs = qa_history.stats
    st.caption(f"📝 {hs['total']}条问答 | 今日{hs['today']}条")
    st.caption(f"📚 {kb.stats['modules']}个知识模块")

    st.divider()
    st.subheader("📍 试试")
    for ex in ["客户已读不回怎么办？","怎么开发新药厂客户？","报价后失踪怎么追？"]:
        if st.button(ex, use_container_width=True): st.session_state.pending = ex; st.rerun()

# ─── Tabs ─────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["💬 问答", "📊 训练", "📝 历史", "📚 知识库"])

# Tab 1: 问答
with tab1:
    st.title("💼 何总销售知识助手")
    st.caption(f"会话: {st.session_state.conv_name} · DeepSeek · 流式响应")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    prompt = st.session_state.pop("pending", None) or st.chat_input("输入销售问题...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full = ""
            try:
                for token in llm.ask(SYSTEM_PROMPT, prompt, stream=True):
                    full += token; placeholder.markdown(full + "▌")
                placeholder.markdown(full)
                qa_history.add(prompt, full)
                st.session_state.messages.append({"role": "assistant", "content": full})
                save_conv()
            except Exception as e:
                placeholder.error(f"请求失败: {e}")

# Tab 2: 训练进度（完整打卡+复盘）
with tab2:
    info = training.get()
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("🔥 连胜", f"{info['streak']} 天")
    with c2: st.metric("⭐ 最佳", f"{info['best_streak']} 天")
    with c3: st.metric("📅 累计", f"{info['total_days']} 天")

    st.divider()

    # 早晚打卡
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("☀️ 晨间打卡")
        if info["checked_in"]:
            st.success("✅ 今日已打卡")
        else:
            if st.button("点击打卡", type="primary"):
                training.checkin()
                st.rerun()

    with col_right:
        st.subheader("🌙 晚间复盘")
        if info["today_completed"]:
            st.success("✅ 今日已完成")
        elif info["checked_in"]:
            st.info("请完成最小可行日后点击复盘")

            tasks = info["today_tasks"]
            all_done = True
            for key, desc in [("1_金句","背诵今日金句"),("2_电话","打1个电话"),("3_复盘","AI问1个问题")]:
                done = st.checkbox(desc, value=tasks.get(key, False), key=f"t_{key}")
                all_done = all_done and done

            st.divider()
            st.caption("加分项（可选）:")
            bonus_tasks = {}
            for key, desc in [
                ("金句背诵","晨会金句抄一遍+背出来"),
                ("客户数据","筛选5条新客户数据"),
                ("开发电话","上午打20个电话"),
                ("追踪客户","给客户发追踪消息"),
            ]:
                bonus_tasks[key] = st.checkbox(desc, value=tasks.get(key, False), key=f"b_{key}")

            if st.button("📝 提交复盘", type="primary", disabled=not all_done):
                all_tasks = {f"1_金句": tasks.get("1_金句",False),
                            f"2_电话": tasks.get("2_电话",False),
                            f"3_复盘": tasks.get("3_复盘",False)}
                for k, v in bonus_tasks.items():
                    if v: all_tasks[k] = True
                # Directly write to progress file
                data = training._load()
                from datetime import date
                today = date.today().isoformat()
                data["history"][today]["tasks"] = all_tasks
                # Force completion
                from datetime import timedelta
                data["history"][today]["completed"] = True
                yesterday = (date.today() - timedelta(days=1)).isoformat()
                if yesterday in data.get("history",{}) and data["history"][yesterday].get("completed"):
                    data["streak"] = data.get("streak",0) + 1
                else:
                    data["streak"] = 1
                data["best_streak"] = max(data.get("best_streak",0), data["streak"])
                data["total_days"] = data.get("total_days",0) + 1
                training._save(data)
                st.rerun()
        else:
            st.info("请先晨间打卡")

    st.divider()
    st.subheader("📅 最近7天")
    cols = st.columns(7)
    icons = {"completed":"✅","checked_in":"📋","empty":"⬜"}
    for i, day in enumerate(info["recent"]):
        with cols[i]:
            st.caption(day["date"][5:])
            st.write(icons.get(day["status"],"⬜"))

# Tab 3: 历史
with tab3:
    st.subheader("📝 问答历史")
    hs = qa_history.stats
    c1, c2 = st.columns(2)
    with c1: st.metric("总数", hs["total"])
    with c2: st.metric("今日", hs["today"])
    search = st.text_input("🔍 搜索", placeholder="关键词…")
    items = qa_history.search(search) if search else qa_history.get_all()
    if not items: st.info("暂无记录")
    else:
        for item in reversed(items):
            with st.expander(f"{item['time']} | {item['question'][:35]}…"):
                st.caption(f"**Q:** {item['question']}")
                st.markdown(f"**A:** {item['answer']}")
    if st.button("🗑️ 清空全部", type="secondary"): qa_history.clear(); st.rerun()

# Tab 4: 知识库
with tab4:
    st.subheader("📚 知识库总览")
    st.caption(f"{kb.stats['modules']} 个模块 · 22条何总视频蒸馏")
    for mod_name in kb.modules:
        mod = kb.get_module(mod_name)
        if isinstance(mod, list):
            with st.expander(f"{mod_name} ({len(mod)} 项)"):
                for item in mod:
                    if isinstance(item, dict):
                        title = item.get("名称") or item.get("原则") or item.get("阶段") or item.get("故事") or ""
                        if "步骤" in item: title = f"第{item['步骤']}步: {title}"
                        core = item.get("核心") or item.get("核心观点") or item.get("解释") or ""
                        st.markdown(f"**{title}**")
                        if core: st.caption(core)
                    elif isinstance(item, str): st.caption(f"- {item}")
        elif isinstance(mod, dict):
            with st.expander(f"{mod_name} ({len(mod)} 项)"):
                for k, v in mod.items():
                    if isinstance(v, list):
                        st.caption(f"**{k}**:")
                        for x in v: st.caption(f"  - {x}")
                    elif isinstance(v, str): st.caption(f"**{k}**: {v}")

st.divider()
st.caption("纯云端 · DeepSeek · 流式 · 零本地依赖")
