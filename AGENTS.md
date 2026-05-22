将 **AI 剧本杀 / 谋杀之谜（Murder Mystery）** 细化为一个具体的 Side Project，不仅非常有趣，而且在技术上完全可行。市面上已经有一些非常优秀的尝试和开源项目，我们可以先看看**已有的实现**，再拆解**核心技术架构**。

---

### 1. 行业内与开源的类似实现

目前在这个方向，国内外已经有了一些非常惊艳的探索：

- **ScottishFold007 / ai-murder-mystery (GitHub 开源项目)** [[1]](https://github.com/ScottishFold007/ai-murder-mystery)：
  - 这是一个非常典型的开源 AI 剧本杀项目 [[1]](https://github.com/ScottishFold007/ai-murder-mystery)。它使用 **React + FastAPI** 架构，支持 Claude、GPT、DeepSeek 等多种 LLM [[1]](https://github.com/ScottishFold007/ai-murder-mystery)。
  - **核心特色**：每个 NPC 都是一个独立的 AI Agent，拥有独特的人格、记忆和不为人知的秘密 [[1]](https://github.com/ScottishFold007/ai-murder-mystery)。游戏设计了**证物系统**和 **AI 侦探搭档**，玩家通过与不同的 AI 嫌疑人对话、搜证来推理出真凶 [[1]](https://github.com/ScottishFold007/ai-murder-mystery)。
- **Krimi.ai (商业/独立游戏)** [[2]](https://krimi.ai/)[[3]](https://www.reddit.com/r/IndieGaming/comments/1k4k1ke/ai_based_murder_mystery_krimiai/)：
  - 一个主打“AI 侦探模拟器”的网页游戏 [[2]](https://krimi.ai/)。玩家扮演侦探，去审问由 AI 驱动的嫌疑人 [[2]](https://krimi.ai/)[[3]](https://www.reddit.com/r/IndieGaming/comments/1k4k1ke/ai_based_murder_mystery_krimiai/)。
  - **核心特色**：AI 嫌疑人有情绪波动和心理防线 [[2]](https://krimi.ai/)。如果你态度不好，或者没有拿出关键证据，他们会撒谎或拒绝配合 [[2]](https://krimi.ai/)[[4]](https://store.steampowered.com/app/3220670/Murder_Mystery_Mayhem_AI/)。你需要通过逻辑漏洞和证据去“破防”他们 [[2]](https://krimi.ai/)[[4]](https://store.steampowered.com/app/3220670/Murder_Mystery_Mayhem_AI/)。
- **学术界研究：LARP (Language-Agent Role Play) 框架** [[5]](https://www.reddit.com/r/machinelearningnews/comments/18z97v7/this_paper_introduces_larp_an_artificial/)：
  - 专门针对开放世界游戏和角色扮演提出的认知架构 [[5]](https://www.reddit.com/r/machinelearningnews/comments/18z97v7/this_paper_introduces_larp_an_artificial/)。它包含**记忆处理、决策助手、环境交互反馈**以及**性格对齐**模块，是多 Agent 跑团的理论基石 [[5]](https://www.reddit.com/r/machinelearningnews/comments/18z97v7/this_paper_introduces_larp_an_artificial/)。

---

### 2. 核心架构设计：如何用代码实现？

要实现一个体验良好的 AI 剧本杀，你需要解决三个核心痛点：**剧情不跑偏（状态机控制）**、**NPC 不胡说八道（记忆与秘密隔离）**、**游戏有可玩性（搜证与推理机制）**。

推荐采用 **LangGraph (或 CrewAI) + FastAPI + React** 的技术栈。

#### 架构图：

```
                      ┌─────────────────┐
                      │   玩家 (Web UI)  │
                      └────────┬────────┘
                               │ (WebSocket / HTTP)
                               ▼
                      ┌─────────────────┐
                      │  游戏主控引擎    │ ◄─── 状态机 (State Machine)
                      └────────┬────────┘      控制：开局 -> 搜证 -> 投票
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
   ┌───────────┐         ┌───────────┐         ┌───────────┐
   │  DM Agent │         │ NPC Agent │         │ NPC Agent │
   └─────┬─────┘         └─────┬─────┘         └─────┬─────┘
         │                     │                     │
         ▼                     ▼                     ▼
   【 公开时间线 】       【 专属记忆库 】       【 专属记忆库 】
   (共享短期记忆)         (私有长期记忆)         (私有长期记忆)
```

---

### 3. 三大核心模块详细设计

#### 模块一：Memory（记忆）系统 ── 解决“保守秘密”与“记住线索”

在剧本杀中，**信息差**是核心。如果把所有剧本信息都塞给一个大模型，它很容易在聊天中把别人的秘密“说漏嘴”。因此，必须做**记忆隔离**。

1.  **私有长期记忆 (Private Long-term Memory)**：
    - **实现方式**：为每个 NPC Agent 配置独立的向量数据库（如 ChromaDB）或独立的 JSON 剧本片段 [[6]](https://github.com/FareedKhan-dev/Multi-Agent-AI-System)[[7]](https://www.youtube.com/watch?v=ob-TOPfQmbk)。
    - **内容**：NPC 的个人背景、案发当晚的时间线、他的杀人动机、他隐藏的秘密（例如：_“我当晚去过书房，但我没有杀人，我只是去偷借条”_）。
2.  **共享短期记忆 (Shared Short-term Memory)**：
    - **实现方式**：一个公共的“案情看板”（Shared State） [[6]](https://github.com/FareedKhan-dev/Multi-Agent-AI-System)[[8]](https://fasttrackfemme.substack.com/p/how-i-became-ceo-of-a-synthetic-company)。
    - **内容**：当前已被玩家搜出来的证据（如：_“在花园发现了一把带血的匕首”_）、大家已知的时间线。当证据被公开后，所有 NPC 的 Prompt 都会自动注入这些新信息，以便他们对新证据做出反应。
3.  **动态好感/警惕度记忆 (Dynamic Relation Memory)**：
    - **实现方式**：用一个简单的 Key-Value 结构记录玩家与 NPC 的关系数值（如 `{"player_trust": 40, "fear_level": 80}`）。
    - **效果**：如果玩家态度粗暴，NPC 的警惕度（fear_level）上升，LLM 在生成对话时会变得防备、甚至撒谎 [[4]](https://store.steampowered.com/app/3220670/Murder_Mystery_Mayhem_AI/)。

#### 模块二：Skills（技能）系统 ── 赋予 Agent 游戏交互能力

Agent 不能只是陪聊，它们需要有“动作”。

1.  **搜证技能 (Search Tool)**：
    - 玩家可以对特定地点（如“死者书房”）使用“搜证”技能。
    - **后台逻辑**：触发一个 Tool，查询数据库中“书房”关联的未公开线索，随机或根据推理进度释放给玩家。
2.  **测谎/观察技能 (Insight Tool)**：
    - 玩家在质问 NPC 时，可以消耗“精力值”使用测谎技能。
    - **后台逻辑**：调用一个专门的 Evaluator Agent（裁判），对比 NPC 刚才说的话与 NPC 数据库里的“真实秘密”。如果 NPC 撒谎了，裁判 Agent 提示玩家：_“他的眼神有些飘忽，似乎隐瞒了去过二楼的事实”_ [[2]](https://krimi.ai/)。
3.  **对质技能 (Confront Tool)**：
    - 玩家向 NPC 展示某件物证。
    - **后台逻辑**：将物证的 ID 和描述作为 Input 传给 NPC Agent，强制触发 NPC 的“辩解逻辑”（例如：看到匕首后，NPC 必须解释为什么匕首上有他的指纹）。

#### 模块三：状态机（Game Flow Controller） ── 保证游戏不崩盘

利用 **LangGraph** 的 State 机制，将游戏划分为不同阶段：

- **Phase 1: 故事导入**。DM Agent 介绍背景，分发角色。
- **Phase 2: 自由质询与搜证**。玩家可以自由选择 NPC 聊天，或者去不同房间搜证。
- **Phase 3: 指控与投票**。玩家必须指明凶手、作案手法和动机。
- **Phase 4: 复盘**。DM Agent 根据玩家的指控，对比真实剧本，给出评分和真相复盘。

---

### 4. 极简的 Python 代码实现思路 (基于 LangGraph 伪代码)

你可以用以下结构来搭建你的多 Agent 剧本杀雏形：

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
import openai

# 1. 定义游戏全局状态
class GameState(TypedDict):
    player_input: str          # 玩家输入
    current_phase: str         # 当前阶段 (investigate / vote)
    discovered_clues: list     # 已公开的线索
    npc_suspects: dict         # NPC 的状态（好感度、是否被怀疑）
    chat_history: list         # 对话历史

# 2. 定义 NPC Agent 节点
def butler_agent(state: GameState):
    """管家 Agent 的决策逻辑"""
    # 注入管家的私有记忆（剧本）
    private_script = "你是管家。你当晚在准备晚餐，但你偷偷看到女仆进了死者房间。你不能主动说，除非玩家拿女仆的项链质问你。"

    # 检查是否有相关线索被公开
    clues_context = ", ".join(state['discovered_clues'])

    prompt = f"{private_script}\n当前已被发现的线索: {clues_context}\n玩家对你说: {state['player_input']}\n请给出你的回答（保持角色扮演）："

    # 调用大模型
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"chat_history": state['chat_history'] + [f"管家: {response.choices[0].message.content}"]}

# 3. 定义 DM (主持人) Agent 节点
def dm_agent(state: GameState):
    """主持人负责引导游戏和判定"""
    if "指控" in state['player_input'] or state['current_phase'] == "vote":
        # 进入投票判定逻辑
        return {"current_phase": "vote"}
    return {"current_phase": "investigate"}

# 4. 构建 LangGraph 工作流
workflow = StateGraph(GameState)

# 添加节点
workflow.add_node("DM", dm_agent)
workflow.add_node("Butler", butler_agent)

# 设置入口和连线
workflow.set_entry_point("DM")

# 动态路由：根据 DM 判定的阶段决定下一步
def route_next(state: GameState):
    if state['current_phase'] == "vote":
        return "end_game"
    return "Butler" # 默认去和管家对话

workflow.add_conditional_edges(
    "DM",
    route_next,
    {
        "end_game": END,
        "Butler": "Butler"
    }
)
workflow.add_edge("Butler", END)

app = workflow.compile()
```

### 5. 为什么这个项目非常适合作为 Side Project？

1.  **极佳的视觉与交互展示**：你可以用 React 做一个复古、精致的 UI（比如羊皮纸风格的线索墙、聊天气泡、搜证地图） [[9]](https://gitcode.csdn.net/69edb30554b52172bc701c14.html)，在简历或 GitHub 上非常吸睛。
2.  **技术深度可深可浅**：
    - _初级版_：只用 Prompt Engineering 区分不同 NPC，用简单的 `input()` 进行命令行对话。
    - _高级版_：引入 **Mem0** 做 NPC 的记忆渐忘与加深 [[6]](https://github.com/FareedKhan-dev/Multi-Agent-AI-System)；引入**语音合成（TTS）**让 AI 嫌疑人直接开口说话 [[10]](https://github.blog/open-source/maintainers/from-mcp-to-multi-agents-the-top-10-open-source-ai-projects-on-github-right-now-and-why-they-matter/)；甚至引入 **Multi-Agent 对抗**（让两个 AI NPC 在群聊里互相推卸责任，玩家在旁围观吃瓜） [[11]](https://developer.aliyun.com/article/909969)。

---

Learn more:

1. [ScottishFold007/ai-murder-mystery: 🕵️ AI剧本杀— 多智能体LLM驱动的沉浸式谋杀悬疑推理游戏 - GitHub](https://github.com/ScottishFold007/ai-murder-mystery)
2. [Krimi | Solve murder mystery cases](https://krimi.ai/)
3. [AI based Murder Mystery: Krimi.ai : r/IndieGaming - Reddit](https://www.reddit.com/r/IndieGaming/comments/1k4k1ke/ai_based_murder_mystery_krimiai/)
4. [Murder Mystery Mayhem AI on Steam](https://store.steampowered.com/app/3220670/Murder_Mystery_Mayhem_AI/)
5. [This Paper Introduces LARP: An Artificial Intelligence Framework for Role-Playing Language Agents Tailored for Open-World Games : r/machinelearningnews - Reddit](https://www.reddit.com/r/machinelearningnews/comments/18z97v7/this_paper_introduces_larp_an_artificial/)
6. [FareedKhan-dev/Multi-Agent-AI-System - GitHub](https://github.com/FareedKhan-dev/Multi-Agent-AI-System)
7. [Build apps & agents that scale with VS Code, GitHub Copilot, and Agent Framework](https://www.youtube.com/watch?v=ob-TOPfQmbk)
8. [How I became CEO of a synthetic company - by Stevie Bennett - Fast Track Femme](https://fasttrackfemme.substack.com/p/how-i-became-ceo-of-a-synthetic-company)
9. [AI剧本杀对局全流程界面设计报告\_游戏 - AtomGit开源社区](https://gitcode.csdn.net/69edb30554b52172bc701c14.html)
10. [From MCP to multi-agents: The top 10 new open source AI projects on GitHub right now and why they matter](https://github.blog/open-source/maintainers/from-mcp-to-multi-agents-the-top-10-open-source-ai-projects-on-github-right-now-and-why-they-matter/)
11. [和AI 一起玩剧本杀真“上头”：没想到AI 比我还入戏](https://developer.aliyun.com/article/909969)
