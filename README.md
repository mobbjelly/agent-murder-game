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

### 1. 准备环境变量

Docker Compose 会读取项目根目录的 `.env.example` 和可选的 `.env`。

首次部署建议复制一份根目录 `.env`：

```bash
cp .env.example .env
```

如果需要动态生成案件或生成图片，请在根目录 `.env` 中配置：

```bash
DASHSCOPE_API_KEY=你的 DashScope API Key
```

不配置 `DASHSCOPE_API_KEY` 时，普通 NPC 对话会使用本地 mock 回复；但“动态案件生成”会提示需要配置 API Key。

### 2. 启动服务

在项目根目录执行：

```bash
docker compose up -d --build
```

打开 `http://localhost:18080`。

### 3. 端口说明

默认宿主机端口不会占用常见的 `80` / `8000`：

- 前端：宿主机 `18080` -> 容器 `80`。
- 后端：宿主机 `18000` -> 容器 `8000`。

如需自定义端口，可在 `.env` 中添加：

```bash
FRONTEND_PORT=18080
BACKEND_PORT=18000
```

前端生产环境默认请求同源 `/api`，由 Nginx 反向代理到 Docker 网络内的 `backend:8000`，不会直接请求浏览器本机的 `localhost:8000`。

### 4. 常用命令

```bash
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend
docker compose ps
docker compose down
```

修改 `.env` 后，需要重建或重新创建后端容器：

```bash
docker compose up -d --force-recreate backend frontend
```

检查 API Key 是否进入容器：

```bash
docker compose exec backend printenv DASHSCOPE_API_KEY
```

### 5. 镜像构建说明

Compose 会启动：

- `backend`：FastAPI 服务，容器内监听 `8000`，默认映射到宿主机 `18000`。
- `frontend`：Nginx 托管前端静态文件，并反向代理 `/api` 和 `/assets/generated` 到后端；生成案件等长请求代理超时为 10 分钟。
- `backend-data`：持久化 SQLite、Chroma、生成图片和 LLM 调用日志。

后端镜像基于 `python:3.12-slim`：

- Debian apt 源默认替换为清华源：`https://mirrors.tuna.tsinghua.edu.cn/debian`。
- pip 安装默认使用阿里云 PyPI 镜像：`https://mirrors.aliyun.com/pypi/simple/`。

如动态案件生成耗时较长，前端 Nginx 已将 `/api` 代理读取超时设置为 `600s`。如果仍然出现 `504 Gateway Time-out`，请查看后端日志确认 DashScope 或图片生成调用是否仍在运行：

```bash
docker compose logs -f backend
```

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
backend/Dockerfile               后端 Docker 镜像
backend/app/main.py              FastAPI 入口
backend/app/game/models.py       Pydantic 请求/响应模型
backend/app/game/engine.py       游戏状态机与工具逻辑
backend/app/game/media.py        内置 SVG 占位图生成
backend/app/game/storage.py      SQLite 持久化与 Chroma 私有记忆检索
backend/app/agents/npc_agent.py  独立 NPC Agent 与私有记忆注入
backend/app/agents/qwen.py       DashScope SDK 适配
backend/app/agents/qwen_image.py Qwen-Image-2.0 图片生成适配
backend/app/agents/deep_dm.py    DeepAgents 可选 DM 编排层
frontend/Dockerfile              前端 Docker 多阶段构建
frontend/nginx.conf              前端静态服务与反向代理配置
frontend/vite.config.ts          Vite 开发代理配置
frontend/src/App.tsx             React 主界面
frontend/src/api.ts              后端 API client
docker-compose.yml               Docker Compose 编排文件
```
