from urllib.parse import quote

from app.game.models import CaseSummary, Clue, NPCState, SceneImage


def svg_data(title: str, subtitle: str, bg: str, accent: str) -> str:
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 800'>
      <defs>
        <linearGradient id='g' x1='0' x2='1' y1='0' y2='1'>
          <stop offset='0' stop-color='{bg}'/>
          <stop offset='1' stop-color='#16100d'/>
        </linearGradient>
        <filter id='noise'><feTurbulence type='fractalNoise' baseFrequency='.75' numOctaves='3' stitchTiles='stitch'/><feColorMatrix type='saturate' values='.22'/><feBlend mode='soft-light' in2='SourceGraphic'/></filter>
      </defs>
      <rect width='800' height='800' fill='url(#g)'/>
      <circle cx='640' cy='140' r='170' fill='{accent}' opacity='.24'/>
      <circle cx='130' cy='680' r='230' fill='#fff5cf' opacity='.09'/>
      <path d='M80 560 C180 500 250 610 360 540 S590 480 720 590' fill='none' stroke='{accent}' stroke-width='18' opacity='.36'/>
      <rect x='96' y='112' width='608' height='576' rx='34' fill='rgba(255,246,214,.10)' stroke='rgba(255,246,214,.38)' stroke-width='7'/>
      <text x='400' y='375' text-anchor='middle' font-family='Arial, sans-serif' font-size='68' font-weight='700' fill='#fff6d6'>{title}</text>
      <text x='400' y='452' text-anchor='middle' font-family='Arial, sans-serif' font-size='34' fill='#ead7b6'>{subtitle}</text>
    </svg>
    """
    return f"data:image/svg+xml;charset=UTF-8,{quote(svg)}"


SCENES = {
    "suite": svg_data("私人套房", "壁炉 · 暴雪窗", "#493225", "#d39b5d"),
    "bedroom": svg_data("死者卧室", "门锁 · 茶盘", "#33414b", "#b88f66"),
    "teacup": svg_data("碎裂茶杯", "稀有毒素残留", "#5b2e2a", "#f1d18a"),
}

AVATARS = {
    "alistair": svg_data("阿", "商业合伙人", "#384046", "#e7b85f"),
    "isla": svg_data("伊", "科技记者", "#3f3431", "#e0783d"),
    "gareth": svg_data("盖", "政治新星", "#2e343c", "#d9c09a"),
}

CLUE_IMAGES = {
    "tea": svg_data("草本茶", "苦杏仁气味", "#4d3427", "#d8b26b"),
    "ledger": svg_data("账本", "收购文件缺页", "#2f3835", "#9cc0a8"),
    "badge": svg_data("记者证", "深夜通行痕迹", "#403139", "#d08aa4"),
    "keycard": svg_data("门禁卡", "茶室进入记录", "#30384b", "#86a8ff"),
    "vial": svg_data("小药瓶", "山月桂提取物", "#263c2f", "#95db9d"),
    "note": svg_data("备忘录", "伦理委员会电话", "#4b352c", "#e6c487"),
}

CASE = CaseSummary(
    id="harmony_springs",
    title="和泉山庄阴谋案",
    difficulty="medium",
    status="unsolved",
    created_label="创建于 33 分钟前",
    updated_label="未侦破",
    days_left=3,
    cover_images=[SCENES["suite"], SCENES["bedroom"], SCENES["teacup"]],
)

INTRO = (
    "科技巨头劳伦斯·博蒙特被发现死在和泉山庄的私人套房里。这里是科罗拉多阿斯彭郊外的一处豪华山地度假庄园。"
    "初步报告显示死因疑似中毒：他的草本茶中检测到一种罕见毒素。现场没有强行闯入痕迹，说明凶手很可能熟悉度假村流程，"
    "拥有通行权限，并且有足够动机。案发前一晚，劳伦斯曾与三名同行者发生激烈争执。"
)

LOCATIONS = ["私人套房", "死者卧室", "茶室", "服务走廊"]

SCENE_IMAGES = [
    SceneImage(id="suite", name="案发套房", location="私人套房", image_url=SCENES["suite"], caption="劳伦斯倒下的壁炉套房。"),
    SceneImage(id="bedroom", name="死者卧室", location="死者卧室", image_url=SCENES["bedroom"], caption="上锁卧室与药品柜。"),
    SceneImage(id="teacup", name="碎裂茶杯", location="茶室", image_url=SCENES["teacup"], caption="从地毯上回收的瓷杯碎片。"),
]

TRUTH = {
    "killer_id": "gareth",
    "method": "盖瑞斯使用临时门禁卡进入茶室，在晚餐前将山月桂提取物加入劳伦斯的草本茶。",
    "motive": "劳伦斯准备揭露盖瑞斯的非法竞选资金，并将他踢出科罗拉多再开发交易。",
}

NPCS = {
    "alistair": {
        "state": NPCState(
            id="alistair",
            name="阿利斯泰尔·考德威尔",
            title="商业合伙人",
            public_profile="劳伦斯多年的商业合伙人，也是度假村收购基金对外露面的负责人。",
            avatar_url=AVATARS["alistair"],
        ),
        "private_memory": (
            "你是阿利斯泰尔·考德威尔。你曾因一本隐藏账本与劳伦斯争吵，但你没有杀他。"
            "你知道劳伦斯很忌惮盖瑞斯背后的政治势力。除非玩家问到账本或竞选资金，否则不要主动透露这点。"
        ),
    },
    "isla": {
        "state": NPCState(
            id="isla",
            name="伊斯拉·德弗罗",
            title="科技记者",
            public_profile="以强硬调查报道闻名的科技记者，长期追踪劳伦斯旗下公司的黑幕。",
            avatar_url=AVATARS["isla"],
        ),
        "private_memory": (
            "你是伊斯拉·德弗罗。你偷偷进入服务走廊，是为了拍下门禁记录。你没有毒杀劳伦斯。"
            "你发现盖瑞斯深夜进入过茶室。只有当玩家赢得你的信任，或拿出记者证线索时，你才愿意透露这件事。"
        ),
    },
    "gareth": {
        "state": NPCState(
            id="gareth",
            name="盖瑞斯·斯坦福",
            title="政坛新星",
            public_profile="科罗拉多政坛冉冉升起的新星，与劳伦斯关系密切，外表迷人但手段强硬。",
            avatar_url=AVATARS["gareth"],
        ),
        "private_memory": (
            "你是盖瑞斯·斯坦福，真正的凶手。你用山月桂提取物毒杀了劳伦斯。"
            "你的动机是保护非法竞选资金和再开发交易。没有关键证据时要冷静否认；"
            "当玩家拿出门禁卡记录、毒瓶或竞选备忘录对质时，你会变得防备，并用半真半假的解释拖延。"
        ),
    },
}

CLUES = [
    Clue(id="poisoned_tea", name="被下毒的草本茶", location="私人套房", description="茶杯散发淡淡苦杏仁味，残液中检测出山月桂毒素。", image_url=CLUE_IMAGES["tea"], is_key=True),
    Clue(id="hidden_ledger", name="隐藏的收购账本", location="死者卧室", description="账本将劳伦斯、阿利斯泰尔和一笔可疑的科罗拉多再开发基金联系起来。", image_url=CLUE_IMAGES["ledger"]),
    Clue(id="press_badge", name="磨损的记者证", location="服务走廊", description="伊斯拉的记者证出现在员工专用楼梯附近，时间接近午夜。", image_url=CLUE_IMAGES["badge"]),
    Clue(id="keycard_log", name="套房门禁记录", location="服务走廊", description="盖瑞斯的临时门禁卡在劳伦斯最后一次饮茶前十二分钟打开过茶室。", image_url=CLUE_IMAGES["keycard"], is_key=True),
    Clue(id="toxin_vial", name="空毒素小瓶", location="茶室", description="一个来自植物实验室的小瓶被藏在进口茶罐后方。", image_url=CLUE_IMAGES["vial"], is_key=True),
    Clue(id="campaign_note", name="竞选备忘录", location="死者卧室", description="劳伦斯原计划第二天早上向伦理委员会举报盖瑞斯的捐款网络。", image_url=CLUE_IMAGES["note"], is_key=True),
]

CASES = [CASE]
