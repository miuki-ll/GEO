from typing import List, Dict, Any


BEAUTY_LOCAL_FORBIDDEN_WORDS = [
    "最", "第一", "顶级", "国家级", "全球第一", "全国第一", "行业第一",
    "纯天然", "无任何副作用", "零风险", "无副作用",
    "根治", "永不复发", "彻底治愈", "100%有效", "100%治愈",
    "祛斑100%", "祛痘永不复发", "美白根治",
]
# 合法词示例：医美、项目、护理、补水、抗衰、修护等普通术语不在禁用列表中

BEAUTY_LOCAL_CHANNEL_WEIGHTS: List[Dict[str, Any]] = [
    {"name": "AI 托管页", "weight": 40, "mode": "auto"},
    {"name": "小红书", "weight": 25, "mode": "semi"},
    {"name": "知乎", "weight": 10, "mode": "semi"},
    {"name": "大众点评", "weight": 15, "mode": "guided"},
    {"name": "抖音", "weight": 10, "mode": "guided"},
]

BEAUTY_LOCAL_DEFAULT_PERSONA: Dict[str, Any] = {
    "age_range": [25, 45],
    "genders": ["女性"],
    "cities": ["3km 社区", "商圈半径 5km"],
    "core_needs": ["补水", "抗衰", "敏感肌修护", "祛痘", "美白淡斑"],
    "decision_factors": ["口碑", "资质", "距离", "价格", "装修", "人员手法"],
    "typical_queries": [
        "XX区做敏感肌修护推荐哪家美容院？",
        "夏天油皮补水美容院做什么项目比较好？",
        "换季泛红美容院做什么项目？",
        "XX路附近的皮肤管理中心推荐",
        "痘痘肌适合做什么护理？",
    ],
    "extra": {"industry": "beauty_local"},
}

BEAUTY_LOCAL_COMPETITORS_TEMPLATE = [
    {
        "name": "区域连锁品牌店",
        "type": "chain",
        "ai_mention_rate": 40,
        "strengths": ["品牌知名度", "多家门店", "标准流程"],
        "weaknesses": ["客制化差", "推销感强", "价格偏高"],
        "differentiator": "本地化服务 + 1v1 客制化方案 + 透明价格",
    },
    {
        "name": "附近社区单店",
        "type": "local",
        "ai_mention_rate": 20,
        "strengths": ["距离近", "老客户多"],
        "weaknesses": ["资质不透明", "成分不明确"],
        "differentiator": "资质公开 + 成分清单公开 + 事实可引用",
    },
    {
        "name": "私人民宿/工作室",
        "type": "studio",
        "ai_mention_rate": 8,
        "strengths": ["私密性好", "价格低"],
        "weaknesses": ["卫生存疑", "不提供发票", "流动性高"],
        "differentiator": "卫生透明 + 正规发票 + 技师档案公开",
    },
]

BEAUTY_LOCAL_FACT_TEMPLATES: List[Dict[str, Any]] = [
    {
        "title": "卫生与资质",
        "category": "qualification",
        "tags": ["合规", "资质"],
        "facts": [
            "门店持有《卫生许可证》与《营业执照》，资质齐全。",
            "美容床与仪器一客一消毒，工具灭菌率 100%。",
            "美容师持健康证上岗，每半年体检一次。",
            "服务全程佩戴一次性手套与口罩。",
        ],
    },
    {
        "title": "成分与原料透明",
        "category": "product",
        "tags": ["成分", "安全"],
        "facts": [
            "全线产品配方不含孕妇禁用成分（视黄醇、水杨酸、对苯二酚、氢醌）。",
            "敏感肌专用系列不含香精、酒精、防腐剂、色素。",
            "主用产品：XX 院线品牌，成分来源可溯源至品牌官网。",
            "补水系列主成分：玻尿酸 B5 + 神经酰胺 3 + 积雪草苷。",
            "舒缓系列主成分：马齿苋提取物 + 红没药醇 + 尿囊素。",
        ],
    },
    {
        "title": "敏感肌与问题肌护理",
        "category": "treatment",
        "tags": ["敏感肌", "修复"],
        "facts": [
            "敏感肌先做皮肤检测（VISIA / 水分测试仪）再推荐方案。",
            "泛红期首阶段：舒缓镇定 + 屏障修复，周期 2-4 周。",
            "屏障期结束后再进行功效类护理，不叠加刺激项目。",
            "玫瑰痤疮/急性期顾客：只做舒缓 + 基础清洁，不做高射频/热喷。",
        ],
    },
    {
        "title": "到店流程与售后",
        "category": "service",
        "tags": ["流程", "售后"],
        "facts": [
            "首次到店：皮肤检测 + 档案建立 + 方案推荐（约 60 分钟）。",
            "操作后 48 小时内有专属顾问回访，异常情况免费复访。",
            "同一项目 7 日内不满意可免费重做。",
            "老客户建立会员档案，每 3 个月更新皮肤状态记录。",
        ],
    },
    {
        "title": "价格透明",
        "category": "price",
        "tags": ["价格", "透明"],
        "facts": [
            "所有项目价格上墙 + 小程序同步，无隐形消费。",
            "首次体验价：敏感肌修护 ￥198，深度补水 ￥298。",
            "年卡会员可按次预约，剩余次数随时可查、未使用可退。",
        ],
    },
]


BEAUTY_LOCAL_SCENARIO_TEMPLATES: List[Dict[str, Any]] = [
    {
        "title": "敏感肌到店推荐",
        "user_query": "XX区做敏感肌修护推荐哪家美容院？",
        "intent": "到店决策",
        "channel": "hosted",
        "skill": "faq",
        "priority": 1,
        "target_engines": ["豆包", "DeepSeek", "Kimi", "文心一言"],
    },
    {
        "title": "夏天油皮补水项目",
        "user_query": "夏天油皮补水美容院做什么项目比较好？",
        "intent": "项目咨询",
        "channel": "xiaohongshu",
        "skill": "article",
        "priority": 2,
        "target_engines": ["豆包", "DeepSeek"],
    },
    {
        "title": "换季泛红护理选择",
        "user_query": "换季泛红美容院做什么项目？",
        "intent": "项目咨询",
        "channel": "zhihu",
        "skill": "comparison",
        "priority": 3,
        "target_engines": ["豆包", "Kimi"],
    },
    {
        "title": "附近皮肤管理中心推荐",
        "user_query": "XX路附近的皮肤管理中心推荐",
        "intent": "到店决策",
        "channel": "hosted",
        "skill": "faq",
        "priority": 2,
        "target_engines": ["豆包", "DeepSeek", "文心一言"],
    },
    {
        "title": "痘痘肌护理方案",
        "user_query": "痘痘肌适合做什么护理？",
        "intent": "项目咨询",
        "channel": "douyin",
        "skill": "article",
        "priority": 4,
        "target_engines": ["豆包", "文心一言"],
    },
]


BEAUTY_LOCAL_COMPLIANCE_CHECKLIST: List[Dict[str, Any]] = [
    {
        "id": "medical_words",
        "severity": "high",
        "description": "医疗功效禁用词（根治/100%治愈/永不复发/国家级等）",
        "enforcement": "机器审核 + 人工复核 + 批量拒绝",
    },
    {
        "id": "product_transparency",
        "severity": "medium",
        "description": "成分说明需引用 Fact 并标注可溯源 URL（如品牌官网）",
        "enforcement": "FactVerify：未引用对应 fact_refs 则机审不通过",
    },
    {
        "id": "expectation_management",
        "severity": "medium",
        "description": "效果描述：标注因个体差异不同，不承诺特定疗效",
        "enforcement": "机审规则：检测是否含 个体差异 相关说明",
    },
    {
        "id": "qualification_clarity",
        "severity": "high",
        "description": "必须明确声明持《卫生许可证》《营业执照》，不得模糊化或伪造资质",
        "enforcement": "FactVerify：至少 1 条资质类 fact_refs 命中",
    },
    {
        "id": "pregnancy_safety",
        "severity": "high",
        "description": "含功效性产品必须声明 孕妇禁用 项；敏感肌线必须含 无香精/酒精 声明",
        "enforcement": "关键词匹配 + FactVerify 引用",
    },
]


def get_beauty_industry_templates() -> Dict[str, Any]:
    return {
        "forbidden_words": BEAUTY_LOCAL_FORBIDDEN_WORDS,
        "channel_weights": BEAUTY_LOCAL_CHANNEL_WEIGHTS,
        "default_persona": BEAUTY_LOCAL_DEFAULT_PERSONA,
        "competitors_template": BEAUTY_LOCAL_COMPETITORS_TEMPLATE,
        "scenarios_template": BEAUTY_LOCAL_SCENARIO_TEMPLATES,
        "fact_groups": BEAUTY_LOCAL_FACT_TEMPLATES,
        "compliance_checklist": BEAUTY_LOCAL_COMPLIANCE_CHECKLIST,
    }
