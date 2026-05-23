# AI 剧本杀 / Murder Mystery 初版

一个基于 **FastAPI + Python DeepAgents + 阿里通义千问 DashScope SDK + React** 的 AI 剧本杀 side project 原型。

## 功能

- 多 NPC：管家、女仆、侄子，每个 NPC 有独立私有记忆与秘密。
- 游戏状态机：导入、调查、指控、复盘。
- 证据系统：按地点搜证，公开证据会进入共享案情看板。
- 对质系统：向 NPC 展示证据，触发辩解逻辑。
- 关系记忆：记录 NPC 的信任、警惕、压力值。
- 持久化：SQLite 保存案件脚本、游戏会话、聊天、证据发现状态和关系值。
- 私有记忆：每个 NPC 都是独立 Agent，人格设定和私有记忆写入 Chroma collection，回复时只检索当前 NPC 的记忆，避免串戏泄密。
- 流式对话：NPC 对话走 SSE 流式输出，前端边生成边展示。
- 图片生成：可接入 Qwen-Image-2.0 为案件封面、场景图和 NPC 头像生成图片；未配置时使用本地 SVG 占位图。
- 案件管理：支持删除动态案件，并同步清理会话与 NPC 私有记忆。
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

## Docker Compose 部署

先准备环境变量文件：

```bash
cp .env.example .env
# 可选：填入 DASHSCOPE_API_KEY；不填时系统会使用本地 mock 回复
```

启动服务：

```bash
docker compose up -d --build
```

打开 `http://localhost:18080`。

默认端口不会占用常见的 `80` / `8000`：

- 前端：宿主机 `18080` -> 容器 `80`。
- 后端：宿主机 `18000` -> 容器 `8000`。

如需自定义端口，可在 `.env` 中添加：

```bash
FRONTEND_PORT=18080
BACKEND_PORT=18000
```

常用命令：

```bash
docker compose logs -f
docker compose down
```

Compose 会启动：

- `backend`：FastAPI 服务，容器内监听 `8000`，默认映射到宿主机 `18000`。
- `frontend`：Nginx 托管前端静态文件，并反向代理 `/api` 和 `/assets/generated` 到后端。
- `backend-data`：持久化 SQLite、Chroma、生成图片和 LLM 调用日志。

## 环境变量

- `DASHSCOPE_API_KEY`：阿里云百炼 / DashScope API Key。
- `QWEN_MODEL`：默认 `qwen-plus`。
- `QWEN_IMAGE_MODEL`：默认 `qwen-image-2.0-pro`。
- `QWEN_IMAGE_SIZE`：默认 `1328*1328`。
- `DASHSCOPE_BASE_URL`：DeepAgents 走 OpenAI 兼容模式时使用，默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`。
- `DASHSCOPE_IMAGE_BASE_URL`：Qwen-Image API base URL，默认 `https://dashscope.aliyuncs.com/api/v1`。
- `GAME_DB_PATH`：SQLite 数据库路径，默认 `backend/data/game.db`。
- `CHROMA_PATH`：Chroma 持久化目录，默认 `backend/data/chroma`。
- `GENERATED_ASSETS_DIR`：生成图片保存目录，默认 `backend/data/generated`。
- `GENERATED_ASSETS_URL_PREFIX`：生成图片访问前缀，默认 `/assets/generated`。
- `LLM_LOG_PATH`：LLM 调用 JSONL 日志路径，默认 `backend/data/logs/llm_calls.jsonl`。

## 项目结构

```text
backend/app/main.py              FastAPI 入口
backend/app/game/models.py       Pydantic 请求/响应模型
backend/app/game/engine.py       游戏状态机与工具逻辑
backend/app/game/media.py        内置 SVG 占位图生成
backend/app/game/storage.py      SQLite 持久化与 Chroma 私有记忆检索
backend/app/agents/npc_agent.py  独立 NPC Agent 与私有记忆注入
backend/app/agents/qwen.py       DashScope SDK 适配
backend/app/agents/qwen_image.py Qwen-Image-2.0 图片生成适配
backend/app/agents/deep_dm.py    DeepAgents 可选 DM 编排层
frontend/src/App.jsx             React 主界面
frontend/src/api.js              后端 API client
```
