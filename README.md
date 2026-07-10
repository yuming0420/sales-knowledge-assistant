# 何总销售知识助手

> 抖音博主"何总"TOB销售培训内容 AI 蒸馏 · 纯云端 · 零本地依赖

## 使用

打开浏览器访问：

**http://81.70.25.234/sales/**

所有功能通过 Web 完成，无需安装任何本地软件：

| 功能 | 位置 |
|------|------|
| 💬 AI 问答 | 「问答」标签页 |
| ☀️🌙 打卡复盘 | 「训练」标签页 |
| 📝 历史记录 | 「历史」标签页 |
| 📚 知识库 | 「知识库」标签页 |
| 💬 多会话 | 侧边栏切换 |

## 技术栈

- **LLM**: DeepSeek (deepseek-chat)，流式响应
- **知识库**: 22条视频蒸馏 → 18个模块 → System Prompt 注入
- **Web**: Streamlit + nginx 反向代理
- **部署**: systemd 自启，OpenCloudOS 9

## 项目结构

```
├── core/
│   ├── knowledge.py   # 知识库加载/格式化
│   ├── llm.py         # DeepSeek 客户端（流式）
│   └── history.py     # 问答历史 + 训练进度 + 多会话
├── web_app.py         # Streamlit Web 界面
├── sales_assistant.py # CLI 备用入口
├── data/
│   ├── knowledge/     # 蒸馏知识 JSON
│   └── conversations/ # 多会话存档
└── .env.example       # 环境变量模板
```
