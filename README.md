# 何总销售知识蒸馏助手

> 抖音博主"何总"销售培训内容的 AI 蒸馏 + RAG 个人助手

## 项目简介

蒸馏抖音博主"何总"（TOB 销售培训）的视频内容，结合大模型构建个人销售知识助手。

- 📚 **知识蒸馏**: 22/36 条视频 → 18 个结构化知识模块
- 🔍 **RAG 检索**: ChromaDB 向量库 + 硅基流动 Embedding
- 💬 **对话问答**: CLI 命令行 + Streamlit Web 界面
- 🚀 **生产部署**: systemd + nginx 反向代理

## 项目结构

```
├── web_app.py              # Streamlit Web 问答台
├── sales_assistant.py      # CLI 命令行助手
├── init_chroma.py          # ChromaDB 向量库初始化脚本
├── Dockerfile              # Docker 部署
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量模板
├── data/
│   ├── knowledge/
│   │   └── 何总_知识框架.json   # 蒸馏后的结构化知识库
│   ├── transcripts/            # 视频转录文本（已 gitignore）
│   └── chroma/                 # 向量数据库（已 gitignore）
└── Stratex 知识蒸馏与LLM赋能交付体.md  # Agent 角色配置
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入硅基流动 API Key
# 注册: https://siliconflow.cn
```

### 3. 初始化向量库

```bash
python init_chroma.py
```

### 4. 启动

**Web 问答台:**
```bash
streamlit run web_app.py
```

**CLI 命令行:**
```bash
python sales_assistant.py
```

## 部署

### Docker

```bash
docker build -t sales-assistant .
docker run -d -p 8501:8501 \
  -e SILICONFLOW_API_KEY=your-key \
  -v $(pwd)/data:/app/data \
  sales-assistant
```

### systemd

```bash
cp sales-assistant.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now sales-assistant
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 转录 | 硅基流动 SenseVoiceSmall |
| 蒸馏 | DeepSeek V4 Pro (via 硅基流动) |
| Embedding | BAAI/bge-large-zh-v1.5 |
| 向量库 | ChromaDB |
| LLM | DeepSeek V4 Flash (via 硅基流动) |
| Web UI | Streamlit |
| 部署 | nginx + systemd |

## 知识库覆盖

| 模块 | 内容 |
|------|------|
| 三大原则 | 训练控制意愿、工具控制行为、流程控制结果 |
| 七步销售法 | 计划→准备→接触→追踪→促成→售后→转介绍 |
| 销售三阶段 | 售前开发、售中追踪、售后维护 |
| 销售管理六法则 | 招聘/培训/考核/激励/淘汰/文化 |
| 行业选择指南 | TOB vs TOC、高薪行业推荐 |
| 销售段位体系 | 青铜→王者分级 |
| 客户追踪方法论 | 三种不回消息情况 + 逼单技巧 |
| 促成心法 | 让客户占便宜 |
| 口才与能力培养 | 铜头铁嘴橡皮肚子飞毛腿 |
| 邀约成交率 | 90% 邀约 + 80% 成交方法论 |
| 更多... | TOB 求职、出差实战、金融大客户 |

## License

MIT
