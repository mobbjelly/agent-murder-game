# AI 剧本杀 / Murder Mystery 初版

一个基于 **FastAPI + Python DeepAgents + 阿里通义千问 DashScope SDK + React** 的 AI 剧本杀 side project 原型。

## 功能

- 多 NPC：管家、女仆、侄子，每个 NPC 有独立私有记忆与秘密。
- 游戏状态机：导入、调查、指控、复盘。
- 证据系统：按地点搜证，公开证据会进入共享案情看板。
- 对质系统：向 NPC 展示证据，触发辩解逻辑。
- 关系记忆：记录 NPC 的信任、警惕、压力值。
- 持久化：SQLite 保存案件脚本、游戏会话、聊天、证据发现状态和关系值。
- 私有记忆：每个 NPC 的人格设定和私有记忆写入本地向量记忆表，回复时只检索当前 NPC 的记忆，避免串戏泄密。
- 通义千问：优先使用 `dashscope` SDK 调用 `qwen-plus`。
- DeepAgents：提供可选 DM 编排适配层，未安装时不影响游戏运行。

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
# 填入 DASHSCOPE_API_KEY，也可不填，系统会使用本地 mock 回复
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`。

## 环境变量

- `DASHSCOPE_API_KEY`：阿里云百炼 / DashScope API Key。
- `QWEN_MODEL`：默认 `qwen-plus`。
- `DASHSCOPE_BASE_URL`：DeepAgents 走 OpenAI 兼容模式时使用，默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`。
- `GAME_DB_PATH`：SQLite 数据库路径，默认 `backend/data/game.db`。

## 项目结构

```text
backend/app/main.py              FastAPI 入口
backend/app/game/models.py       Pydantic 请求/响应模型
backend/app/game/script.py       剧本、NPC 私有记忆、证据
backend/app/game/engine.py       游戏状态机与工具逻辑
backend/app/game/storage.py      SQLite 持久化与本地向量记忆检索
backend/app/agents/qwen.py       DashScope SDK 适配
backend/app/agents/deep_dm.py    DeepAgents 可选 DM 编排层
frontend/src/App.jsx             React 主界面
frontend/src/api.js              后端 API client
```
