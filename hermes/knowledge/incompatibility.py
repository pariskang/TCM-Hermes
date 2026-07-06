"""Herb incompatibility & toxicity screening (十八反 / 十九畏 / 毒性 / 妊娠).

Deterministic, lexicon-driven safety layer for prescription-facing surfaces
(match-prescription, physician workbench, MCP tools).  All tables follow the
classical sources — 十八反 per《儒門事親》歌訣, 十九畏 per《醫經小學》歌訣 —
with membership groups so processed/derivative names (川烏/草烏/附子,
栝蔞實/栝蔞根/天花粉…) hit the same rule after `normalize_herb`.

The screen is advisory: classical formulas themselves occasionally combine
反藥 on purpose (甘遂半夏湯), so a hit is surfaced as a red-flag note for a
practitioner, never as an automated verdict.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# membership groups — normalized herb name → group key
# ---------------------------------------------------------------------------

_GROUPS: dict[str, set[str]] = {
    "烏頭類": {"烏頭", "川烏", "草烏", "附子", "天雄", "烏喙"},
    "半夏": {"半夏", "法半夏", "薑半夏", "清半夏"},
    "瓜蔞類": {"栝蔞實", "栝蔞根", "栝蔞", "栝樓", "瓜蔞", "天花粉", "瓜蔞皮", "瓜蔞仁"},
    "貝母": {"貝母", "川貝母", "浙貝母", "土貝母"},
    "白蘞": {"白蘞"},
    "白及": {"白及", "白芨"},
    "甘草": {"甘草"},
    "甘遂": {"甘遂"},
    "大戟": {"大戟", "京大戟", "紅大戟"},
    "海藻": {"海藻"},
    "芫花": {"芫花"},
    "藜蘆": {"藜蘆"},
    "人參": {"人參"},
    "沙參": {"沙參", "南沙參", "北沙參"},
    "丹參": {"丹參"},
    "玄參": {"玄參", "元參"},
    "苦參": {"苦參"},
    "細辛": {"細辛"},
    "芍藥": {"芍藥", "白芍", "赤芍"},
    # 十九畏 members
    "硫黃": {"硫黃", "硫磺"},
    "朴硝": {"朴硝", "芒硝", "牙硝", "玄明粉"},
    "水銀": {"水銀"},
    "砒霜": {"砒霜", "信石"},
    "狼毒": {"狼毒"},
    "密陀僧": {"密陀僧"},
    "巴豆": {"巴豆"},
    "牽牛": {"牽牛", "牽牛子", "黑丑", "白丑"},
    "丁香": {"丁香", "母丁香", "公丁香"},
    "鬱金": {"鬱金", "郁金"},
    "犀角": {"犀角"},
    "三稜": {"三稜", "三棱"},
    "官桂": {"官桂", "肉桂", "桂心"},
    "赤石脂": {"赤石脂", "白石脂", "石脂"},
    "五靈脂": {"五靈脂"},
}

_MEMBER_TO_GROUP: dict[str, str] = {
    m: g for g, members in _GROUPS.items() for m in members}

# 十八反: 甘草反甘遂大戟海藻芫花；烏頭反半夏瓜蔞貝母白蘞白及；藜蘆反諸參辛芍
EIGHTEEN_ANTAGONISMS: list[tuple[str, str]] = [
    ("甘草", "甘遂"), ("甘草", "大戟"), ("甘草", "海藻"), ("甘草", "芫花"),
    ("烏頭類", "半夏"), ("烏頭類", "瓜蔞類"), ("烏頭類", "貝母"),
    ("烏頭類", "白蘞"), ("烏頭類", "白及"),
    ("藜蘆", "人參"), ("藜蘆", "沙參"), ("藜蘆", "丹參"), ("藜蘆", "玄參"),
    ("藜蘆", "苦參"), ("藜蘆", "細辛"), ("藜蘆", "芍藥"),
]

# 十九畏（歌訣配對）
NINETEEN_INCOMPATIBILITIES: list[tuple[str, str]] = [
    ("硫黃", "朴硝"), ("水銀", "砒霜"), ("狼毒", "密陀僧"), ("巴豆", "牽牛"),
    ("丁香", "鬱金"), ("烏頭類", "犀角"), ("朴硝", "三稜"), ("官桂", "赤石脂"),
    ("人參", "五靈脂"),
]

# 毒性/炮製警示（常見於傷寒金匱方的品種優先）
TOXIC_HERBS: dict[str, dict] = {
    "附子": {"level": "high", "note": "有毒，須炮製並先煎久煎；生附子毒性大"},
    "烏頭": {"level": "high", "note": "大毒，須炮製久煎；烏頭鹼中毒風險"},
    "川烏": {"level": "high", "note": "大毒，須炮製久煎"},
    "草烏": {"level": "high", "note": "大毒，須炮製久煎"},
    "天雄": {"level": "high", "note": "大毒，烏頭屬"},
    "半夏": {"level": "medium", "note": "生半夏有毒，入湯劑須薑製/法製"},
    "天南星": {"level": "medium", "note": "生品有毒，須炮製"},
    "甘遂": {"level": "high", "note": "峻下逐水，有毒，多入丸散"},
    "大戟": {"level": "high", "note": "峻下逐水，有毒"},
    "芫花": {"level": "high", "note": "峻下逐水，有毒，醋製"},
    "巴豆": {"level": "high", "note": "大毒峻下，嚴格控量"},
    "藜蘆": {"level": "high", "note": "湧吐峻藥，有毒"},
    "水銀": {"level": "high", "note": "劇毒，現代禁用於內服"},
    "砒霜": {"level": "high", "note": "劇毒，嚴格管制"},
    "細辛": {"level": "medium", "note": "有小毒，傳統有用量警示（細辛不過錢之說）"},
    "杏仁": {"level": "low", "note": "含苦杏仁苷，過量有毒"},
    "桃仁": {"level": "low", "note": "含苦杏仁苷，過量有毒"},
    "硃砂": {"level": "high", "note": "含汞，不宜久服過量"},
    "雄黃": {"level": "high", "note": "含砷，不宜久服，忌火煅"},
    "馬錢子": {"level": "high", "note": "大毒，嚴格炮製控量"},
    "斑蝥": {"level": "high", "note": "大毒"},
    "蜀椒": {"level": "low", "note": "小毒，炒去汗用"},
    "皂莢": {"level": "low", "note": "小毒"},
    "葶藶子": {"level": "low", "note": "瀉肺峻藥，注意用量"},
    "商陸": {"level": "high", "note": "有毒，峻下逐水"},
    "狼毒": {"level": "high", "note": "大毒"},
    "牽牛": {"level": "medium", "note": "峻下，有毒"},
}

# 妊娠禁忌（禁用/慎用，取傷寒金匱語境常見者）
PREGNANCY_FORBIDDEN: set[str] = {
    "巴豆", "牽牛", "大戟", "芫花", "甘遂", "商陸", "斑蝥", "水蛭", "虻蟲",
    "麝香", "三稜", "莪朮", "水銀", "砒霜", "藜蘆", "馬錢子", "烏頭", "川烏",
    "草烏", "天雄",
}
# 注：桂枝不列入——《金匱》妊娠篇本以桂枝湯為首方，列入將造成大面积误报
PREGNANCY_CAUTION: set[str] = {
    "附子", "乾薑", "肉桂", "官桂", "半夏", "大黃", "芒硝", "朴硝",
    "桃仁", "紅花", "牛膝", "枳實", "厚朴", "葶藶子", "代赭石", "雄黃", "硃砂",
}

DISCLAIMER = ("以上为古籍配伍禁忌与毒性知识的自动筛查，仅供执业医师参考，"
              "不构成用药建议；经方中偶有反药同用之特例（如甘遂半夏湯），"
              "取舍须由医师判断。")


def _group_of(herb: str) -> str | None:
    return _MEMBER_TO_GROUP.get(herb)


def check_safety(herbs: list[str]) -> dict:
    """Screen a normalized-or-raw herb list; returns pairs/toxicity/pregnancy.

    Input names are normalized via `normalize_herb` (simplified input,
    processing prefixes and dose suffixes are handled there).
    """
    from ..lineage.prescription import normalize_herb
    normalized = []
    for h in herbs:
        h = (h or "").strip()
        if h:
            normalized.append(normalize_herb(h))
    present: dict[str, list[str]] = {}
    for h in normalized:
        g = _group_of(h)
        if g:
            present.setdefault(g, [])
            if h not in present[g]:
                present[g].append(h)

    pairs = []
    for kind, table in (("十八反", EIGHTEEN_ANTAGONISMS),
                        ("十九畏", NINETEEN_INCOMPATIBILITIES)):
        for a, b in table:
            if a in present and b in present:
                pairs.append({"type": kind,
                              "herb_a": "、".join(present[a]),
                              "herb_b": "、".join(present[b]),
                              "rule": f"{a} × {b}"})

    toxic = [{"herb": h, **TOXIC_HERBS[h]}
             for h in dict.fromkeys(normalized) if h in TOXIC_HERBS]
    pregnancy = (
        [{"herb": h, "grade": "禁用"} for h in dict.fromkeys(normalized)
         if h in PREGNANCY_FORBIDDEN]
        + [{"herb": h, "grade": "慎用"} for h in dict.fromkeys(normalized)
           if h in PREGNANCY_CAUTION and h not in PREGNANCY_FORBIDDEN])

    if pairs or any(t["level"] == "high" for t in toxic):
        risk = "high"
    elif toxic or pregnancy:
        risk = "caution"
    else:
        risk = "none"
    return {"input_herbs": normalized, "incompatible_pairs": pairs,
            "toxic_herbs": toxic, "pregnancy_cautions": pregnancy,
            "risk_level": risk, "disclaimer": DISCLAIMER}


def formula_safety(formula: str) -> dict | None:
    """Screen a classical formula's canonical composition (None if unknown)."""
    from .lexicon import LEXICON
    info = LEXICON.canonical_formulas.get(formula)
    if not info:
        return None
    report = check_safety(list(info["herbs"]))
    report["formula"] = formula
    return report
