"""Disease profiles — data-driven so the framework migrates across diseases.

Term lists are written in simplified Chinese for readability and normalized to
traditional at load time (the corpus is traditional), so matching works
regardless of the input script.  To add a disease (骨质疏松 / 类风湿 / 湿疹 …),
write another DiseaseProfile and register it in DISEASE_PROFILES — no agent
code changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..knowledge.s2t import to_traditional as T


@dataclass
class DiseaseProfile:
    disease_id: str
    display_name: str
    modern_subtypes: list[str]
    # subtype → phenotype feature words (the 表型组合检索 schema)
    phenotype_schema: dict[str, list[str]]
    core_terms: list[str]                       # ancient disease names (broad recall)
    morphology_terms: list[str]                 # 形态学精筛 vocabulary
    # special subtype → {"anchors": [...], "qualifiers": [...], "window": N}
    special_subtypes: dict[str, dict]
    exclusion_terms: list[str]                  # differential diseases to exclude
    differential_notes: dict[str, str]          # exclusion term → why
    pathogenesis_terms: list[str]               # 病机 ontology layer
    treatment_terms: list[str]                  # 治法 ontology layer
    extra_herbs: list[str] = field(default_factory=list)  # disease-specific herbs

    def __post_init__(self) -> None:
        self.core_terms = [T(t) for t in self.core_terms]
        self.morphology_terms = [T(t) for t in self.morphology_terms]
        self.exclusion_terms = [T(t) for t in self.exclusion_terms]
        self.pathogenesis_terms = [T(t) for t in self.pathogenesis_terms]
        self.treatment_terms = [T(t) for t in self.treatment_terms]
        self.extra_herbs = [T(t) for t in self.extra_herbs]
        self.phenotype_schema = {k: [T(w) for w in v]
                                 for k, v in self.phenotype_schema.items()}
        self.differential_notes = {T(k): v for k, v in self.differential_notes.items()}
        for spec in self.special_subtypes.values():
            spec["anchors"] = [T(a) for a in spec.get("anchors", [])]
            spec["qualifiers"] = [T(q) for q in spec.get("qualifiers", [])]
            spec.setdefault("window", 15)

    def core_query(self) -> str:
        return "(" + " OR ".join(self.core_terms) + ")"

    def all_phenotype_terms(self) -> list[str]:
        out: list[str] = []
        for v in self.phenotype_schema.values():
            out.extend(v)
        return sorted(set(out), key=len, reverse=True)


PSORIASIS = DiseaseProfile(
    disease_id="psoriasis",
    display_name="银屑病",
    modern_subtypes=["寻常型", "脓疱型", "红皮病型", "关节型", "头皮型", "甲型"],
    phenotype_schema={
        "vulgaris": ["白屑", "皮枯", "脱屑", "如钱文", "匡郭", "隐胗", "鳞屑", "燥"],
        "pustular": ["黄水", "脓水", "脓疱", "津水", "搔之有汁", "流水", "泡疮"],
        "erythrodermic": ["遍身", "全身", "浸淫", "赤黑", "成片", "痒不可忍"],
        "arthropathic": ["关节", "筋骨", "骨节", "拘急", "屈伸不利", "四肢", "顽痹"],
        "nail": ["甲", "爪", "指甲", "厚", "脱", "黑", "枯"],
        "scalp": ["头", "头发", "发际", "白壳", "脱屑", "眉"],
    },
    core_terms=["癣", "疕", "疥", "疮", "白疕", "干癣", "顽癣", "松皮癣",
                "蛇虱", "牛皮癣", "白癣", "头癣", "脓癣"],
    morphology_terms=["如钱文", "地图", "斑块", "环形", "圆形", "点滴", "斑点",
                      "带状", "隐胗", "成片", "剥落", "结痂", "脱屑", "匡郭",
                      "渐渐增长", "皮枯索", "白皮"],
    special_subtypes={
        "arthropathic": {
            "anchors": ["关节", "筋骨", "骨节", "四肢", "手足"],
            "qualifiers": ["痛", "拘急", "不利", "麻木", "变形", "僵直",
                           "屈伸", "顽痹"],
            "window": 15},
        "nail": {
            "anchors": ["甲", "爪", "指甲"],
            "qualifiers": ["黑", "厚", "脱", "枯", "变形", "剥离", "黄"],
            "window": 10},
        "scalp": {
            "anchors": ["头", "头发", "发际", "眉", "面"],
            "qualifiers": ["屑", "痒", "结痂", "白壳", "脱屑"],
            "window": 12},
    },
    exclusion_terms=["圆癣", "金钱癣", "股癣", "手足癣", "秃疮", "疥疮",
                     "麻风", "痤疮", "癞", "丹毒", "疱疹", "水痘", "圆癣"],
    differential_notes={
        "金钱癣": "环形真菌感染（体癣），非银屑病",
        "圆癣": "环形真菌感染（体癣），非银屑病",
        "股癣": "腹股沟真菌感染，非银屑病",
        "手足癣": "手足真菌感染，非银屑病",
        "秃疮": "头部脓癣/真菌感染伴脱发，需鉴别",
        "疥疮": "疥螨所致，剧痒夜甚、指缝隧道，非银屑病",
        "麻风": "麻风分枝杆菌所致，麻木、结节、脱眉，非银屑病",
        "痤疮": "毛囊皮脂腺炎症，非银屑病",
        "癞": "古义多指麻风或顽恶皮病，语义宽泛需鉴别",
        "丹毒": "急性红肿热痛感染，非银屑病",
        "疱疹": "簇集水疱，病毒所致，非银屑病",
        "水痘": "全身散在水疱伴发热，病毒所致，非银屑病",
    },
    pathogenesis_terms=["风湿", "风热", "风燥", "血热", "血燥", "血瘀", "湿热",
                        "血气相搏", "寒湿", "风毒", "风邪", "虫淫", "营血亏虚",
                        "肌肤失养", "阴虚血燥", "腠理"],
    treatment_terms=["养血润燥", "祛风", "清热解毒", "凉血", "活血化瘀", "杀虫",
                     "祛风止痒", "养血祛风", "清热利湿", "外洗", "熏洗", "针刺",
                     "艾灸", "外敷", "内服"],
    extra_herbs=["白芷", "防风", "荆芥", "苦参", "蛇床子", "白鲜皮", "地肤子",
                 "土茯苓", "苍术", "黄柏", "生地黄", "牡丹皮", "紫草", "蝉蜕",
                 "乌梢蛇", "全蝎", "皂角", "硫黄", "雄黄", "轻粉", "水银"],
)


DISEASE_PROFILES: dict[str, DiseaseProfile] = {
    PSORIASIS.disease_id: PSORIASIS,
    "银屑病": PSORIASIS,
}


def get_profile(name: str) -> DiseaseProfile:
    if name in DISEASE_PROFILES:
        return DISEASE_PROFILES[name]
    if T(name) in DISEASE_PROFILES:
        return DISEASE_PROFILES[T(name)]
    raise KeyError(
        f"unknown disease profile: {name}; available: "
        f"{sorted(set(p.disease_id for p in DISEASE_PROFILES.values()))}")
