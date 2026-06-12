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


# ---------------------------------------------------------------------------
# 骨质疏松（古籍对应：骨痿 / 骨枯 / 骨痹 / 骨极 / 虚劳腰痛）
# 内经/本草色彩浓，伤寒金匮语料较少（金匮「虚劳腰痛…八味肾气丸」可命中）。
# ---------------------------------------------------------------------------

OSTEOPOROSIS = DiseaseProfile(
    disease_id="osteoporosis",
    display_name="骨质疏松",
    modern_subtypes=["原发性", "绝经后", "老年性", "继发性"],
    phenotype_schema={
        "bone_loss": ["骨痿", "骨枯", "髓减", "髓枯", "骨软", "骨弱", "腰脊不举"],
        "pain": ["腰痛", "腰脊痛", "腰膝酸软", "骨节疼痛", "脊痛", "背痛", "胫酸"],
        "deformity": ["伛偻", "驼背", "腰曲", "不能久立", "行则振掉", "脊以代头"],
        "frailty": ["虚劳", "羸瘦", "足痿", "行立不能", "骨重", "懈惰"],
    },
    core_terms=["骨痿", "骨枯", "骨极", "骨痹", "骨蚀", "髓枯", "虚劳腰痛",
                "腰痛", "痿", "骨重"],
    morphology_terms=["伛偻", "驼背", "腰脊不举", "腰曲", "不能久立",
                      "行则振掉", "脊以代头", "髓减", "骨软"],
    special_subtypes={
        "spine": {"anchors": ["腰", "脊", "背", "膂"],
                  "qualifiers": ["痛", "酸", "不举", "曲", "重", "不能俯仰"],
                  "window": 12},
        "limb": {"anchors": ["膝", "胫", "足", "股", "髀"],
                 "qualifiers": ["酸", "软", "痿", "弱", "不能久立"],
                 "window": 12},
    },
    exclusion_terms=["附骨疽", "骨疽", "骨痈", "骨瘤", "骨蒸", "历节", "鹤膝风",
                     "脚气", "龟背"],
    differential_notes={
        "附骨疽": "化脓性骨感染（骨髓炎类），非骨质疏松",
        "骨疽": "骨部痈疽，感染性，非骨质疏松",
        "骨蒸": "多为痨瘵（结核）骨蒸潮热，非骨质疏松",
        "历节": "关节红肿剧痛属类风湿/痛风类，非骨质疏松",
        "鹤膝风": "膝关节肿大属痹证类，需鉴别",
        "脚气": "古义近脚气病/下肢痿弱，病因不同",
        "龟背": "小儿佝偻或脊柱畸形，病因需鉴别",
    },
    pathogenesis_terms=["肾虚", "肾精亏虚", "精亏", "髓减", "髓虚", "脾虚",
                        "肝肾不足", "肝肾亏虚", "阳虚", "气血亏虚", "血瘀",
                        "冲任虚衰"],
    treatment_terms=["补肾", "填精", "益髓", "强骨", "壮骨", "健脾", "温阳",
                     "滋补肝肾", "益气养血", "活血", "补益肝肾", "调补冲任"],
    extra_herbs=["熟地黄", "生地黄", "杜仲", "续断", "骨碎补", "淫羊藿", "巴戟天",
                 "肉苁蓉", "枸杞子", "龟板", "鹿角胶", "鹿茸", "牛膝", "山茱萸",
                 "菟丝子", "补骨脂", "狗脊", "黄芪", "当归", "白朮", "茯苓",
                 "附子", "桂枝", "山药", "泽泻", "牡丹皮"],
)


# ---------------------------------------------------------------------------
# 类风湿关节炎（古籍对应：历节 / 痹证 / 尪痹 / 鹤膝风 / 白虎历节）
# 金匮「中风历节病脉证并治」直接命中，--use-corpus 可在现有语料检出真实条文。
# ---------------------------------------------------------------------------

RHEUMATOID = DiseaseProfile(
    disease_id="rheumatoid_arthritis",
    display_name="类风湿关节炎",
    modern_subtypes=["活动期", "缓解期", "晚期畸形", "尪痹"],
    phenotype_schema={
        "joint_pain": ["肢节疼痛", "骨节疼痛", "关节疼痛", "历节痛", "掣痛",
                       "诸肢节疼痛", "疼痛", "痛"],
        "swelling": ["脚肿如脱", "关节肿", "肿大", "肿", "焮肿"],
        "deformity": ["不可屈伸", "屈伸不利", "尪羸", "身体尪羸", "变形",
                      "拘挛", "强直", "鹤膝"],
        "systemic": ["短气", "头眩", "温温欲吐", "黄汗", "脚肿"],
    },
    core_terms=["历节", "痹", "风痹", "寒痹", "湿痹", "着痹", "行痹", "痛痹",
                "尪痹", "鹤膝风", "白虎历节", "周痹", "顽痹", "历节风"],
    morphology_terms=["脚肿如脱", "身体尪羸", "不可屈伸", "鹤膝", "骨节肿大",
                      "诸肢节疼痛", "焮肿", "拘挛"],
    special_subtypes={
        "hand_foot": {"anchors": ["手", "足", "指", "腕", "踝", "肢节", "四肢"],
                      "qualifiers": ["痛", "肿", "屈伸", "拘挛", "强直", "不仁"],
                      "window": 14},
        "knee": {"anchors": ["膝", "鹤膝", "髀", "胫"],
                 "qualifiers": ["肿", "大", "痛", "不可屈伸"], "window": 12},
    },
    exclusion_terms=["痿", "痿证", "脚气", "丹毒", "流注", "骨痿", "中风偏枯",
                     "痛风石"],
    differential_notes={
        "痿": "痿证以肢体软弱无力为主、多无红肿热痛，与痹证（痛）属不同纲",
        "痿证": "肢体痿弱不用，非以关节疼痛为主",
        "脚气": "古义近脚气病，下肢肿弱麻木，病因不同",
        "丹毒": "急性红肿热痛感染，非类风湿",
        "流注": "深部走窜性脓肿，感染性",
        "中风偏枯": "半身不遂属中风，非痹证",
    },
    pathogenesis_terms=["风寒湿", "风湿", "寒湿", "湿热", "风寒", "肝肾不足",
                        "气血两虚", "气血亏虚", "痰瘀", "痰瘀痹阻", "营卫不和",
                        "风血相搏", "阳气不足", "瘀血"],
    treatment_terms=["祛风散寒", "除湿通络", "温经散寒", "清热除湿", "活血化瘀",
                     "补肝肾", "益气血", "通络止痛", "蠲痹", "散寒止痛",
                     "祛风除湿", "温阳", "养血"],
    extra_herbs=["乌头", "川乌", "附子", "桂枝", "麻黄", "防风", "羌活", "独活",
                 "威灵仙", "秦艽", "桑寄生", "牛膝", "知母", "白芍", "海风藤",
                 "络石藤", "全蝎", "蜈蚣", "乌梢蛇", "白朮", "甘草", "黄芪",
                 "当归", "细辛", "防己", "薏苡仁", "苍朮", "生姜"],
)


# ---------------------------------------------------------------------------
# 温病（古籍对应：温病/风温/春温/暑温/湿温/秋燥/温疫，卫气营血传变）
# 温病学派主体在叶天士/吴鞠通，伤寒金匮仅有「太陽病…為溫病」等零星条文。
# ---------------------------------------------------------------------------

WARM_DISEASE = DiseaseProfile(
    disease_id="warm_disease",
    display_name="温病",
    modern_subtypes=["卫分", "气分", "营分", "血分", "风温", "湿温", "暑温", "秋燥"],
    phenotype_schema={
        "wei": ["发热", "微恶风寒", "头痛", "咳", "口微渴", "脉浮数"],
        "qi": ["壮热", "大汗", "口渴", "心烦", "不恶寒", "脉洪大"],
        "ying": ["身热夜甚", "心烦不寐", "斑疹隐隐", "舌绛", "时有谵语"],
        "xue": ["斑疹", "吐血", "衄血", "便血", "神昏", "舌深绛"],
        "shiwen": ["身热不扬", "胸闷", "脘痞", "苔腻", "身重"],
        "shuwen": ["壮热", "汗多", "烦渴", "面赤", "脉洪"],
    },
    core_terms=["温病", "风温", "春温", "暑温", "湿温", "秋燥", "冬温",
                "温热", "温疫", "温毒", "伏暑", "温邪"],
    morphology_terms=["斑疹", "斑", "疹", "白㾦", "斑疹隐隐", "战汗", "舌绛"],
    special_subtypes={
        "xinbao": {"anchors": ["心包", "神", "心"],
                   "qualifiers": ["昏", "谵语", "逆传", "蒙"], "window": 12},
        "dongxue": {"anchors": ["血", "斑", "络"],
                    "qualifiers": ["动", "吐", "衄", "便", "耗", "出"], "window": 10},
    },
    exclusion_terms=["太阳伤寒", "伤寒表实", "中风", "风寒", "直中", "阴寒",
                     "内伤发热", "虚劳"],
    differential_notes={
        "太阳伤寒": "伤寒恶寒无汗脉浮紧，与温病发热而渴不恶寒相对，属不同辨证体系",
        "伤寒表实": "麻黄汤证恶寒无汗，非温病",
        "风寒": "外感风寒以恶寒为主，温病以发热口渴为主",
        "直中": "寒邪直中三阴，属伤寒范畴",
        "内伤发热": "内伤发热多渐起、无表证，非外感温邪",
        "虚劳": "虚劳发热属内伤，非温病",
    },
    pathogenesis_terms=["温邪", "卫气营血", "邪在卫分", "热入气分", "热入营分",
                        "热入血分", "湿热", "暑热", "燥热", "逆传心包",
                        "热盛动血", "热极生风", "热盛伤津", "卫分", "气分",
                        "营分", "血分"],
    treatment_terms=["辛凉解表", "清气泄热", "清营透热", "凉血散血", "清热解毒",
                     "化湿", "芳香化浊", "滋阴", "养阴生津", "开窍", "息风",
                     "透热转气", "清热生津"],
    extra_herbs=["金银花", "银花", "连翘", "薄荷", "牛蒡子", "桑叶", "菊花",
                 "芦根", "竹叶", "石膏", "知母", "生地黄", "玄参", "水牛角",
                 "牡丹皮", "赤芍", "黄连", "栀子", "板蓝根", "荆芥", "淡豆豉",
                 "桔梗", "甘草", "杏仁", "麦门冬", "石菖蒲", "郁金"],
)


# ---------------------------------------------------------------------------
# 湿疹（古籍对应：湿疮/浸淫疮/旋耳疮/四弯风/奶癣/胎敛疮/血风疮/黄水疮）
# 纯外科，伤寒金匮无，依示例语料；正式研究需导入外科语料。
# ---------------------------------------------------------------------------

ECZEMA = DiseaseProfile(
    disease_id="eczema",
    display_name="湿疹",
    modern_subtypes=["急性", "亚急性", "慢性", "婴儿湿疹", "局限性"],
    phenotype_schema={
        "acute": ["黄水", "浸淫", "糜烂", "流水", "津水", "湿烂", "瘙痒"],
        "chronic": ["干燥", "脱屑", "肥厚", "皲裂", "粗糙", "苔藓"],
        "infant": ["奶癣", "胎敛疮", "头面", "婴儿", "白屑"],
        "site": ["旋耳", "耳", "四弯", "腿弯", "脚弯", "阴囊", "绣球"],
    },
    core_terms=["湿疮", "浸淫疮", "旋耳疮", "四弯风", "奶癣", "胎敛疮",
                "血风疮", "黄水疮", "绣球风", "湿癣", "风湿疡"],
    morphology_terms=["浸淫成片", "黄水", "糜烂", "结痂", "抓痕", "渗出",
                      "津水", "湿烂", "浸淫", "白屑"],
    special_subtypes={
        "ear": {"anchors": ["耳", "旋耳"], "qualifiers": ["疮", "痒", "津水", "黄水"],
                "window": 8},
        "flexure": {"anchors": ["腿弯", "脚弯", "四弯", "肘", "腘"],
                    "qualifiers": ["风", "痒", "津水", "搔破"], "window": 10},
        "infant": {"anchors": ["婴儿", "头面", "头顶", "眉"],
                   "qualifiers": ["奶癣", "癣", "痒", "白屑"], "window": 12},
    },
    exclusion_terms=["白疕", "牛皮癣", "疥疮", "圆癣", "金钱癣", "丹毒",
                     "天疱疮", "麻风"],
    differential_notes={
        "白疕": "银屑病，鳞屑成片、白色，与湿疹之渗出黄水不同",
        "牛皮癣": "顽厚干硬、阵发瘙痒，与湿疹渗出不同",
        "疥疮": "疥螨所致、指缝隧道、夜间剧痒，非湿疹",
        "圆癣": "环形真菌感染（体癣），非湿疹",
        "金钱癣": "真菌感染，非湿疹",
        "丹毒": "急性红肿热痛感染，非湿疹",
        "天疱疮": "大疱性皮病，与湿疹不同",
    },
    pathogenesis_terms=["湿热", "风湿热", "心火脾湿", "脾虚湿蕴", "血虚风燥",
                        "湿热下注", "风热", "胎毒", "湿盛", "血热"],
    treatment_terms=["清热利湿", "祛风除湿", "凉血", "养血润燥", "健脾化湿",
                     "清热解毒", "外洗", "祛湿止痒", "利湿", "燥湿"],
    extra_herbs=["苦参", "白鲜皮", "地肤子", "蛇床子", "黄柏", "苍朮", "萆薢",
                 "土茯苓", "生地黄", "牡丹皮", "当归", "荆芥", "防风", "蝉蜕",
                 "金银花", "龙胆草", "黄芩", "栀子", "薏苡仁", "泽泻", "车前子",
                 "白朮", "甘草"],
)


def get_profile(name: str) -> DiseaseProfile:
    if name in DISEASE_PROFILES:
        return DISEASE_PROFILES[name]
    if T(name) in DISEASE_PROFILES:
        return DISEASE_PROFILES[T(name)]
    raise KeyError(
        f"unknown disease profile: {name}; available: "
        f"{sorted(set(p.disease_id for p in DISEASE_PROFILES.values()))}")


DISEASE_PROFILES: dict[str, DiseaseProfile] = {
    PSORIASIS.disease_id: PSORIASIS,
    "银屑病": PSORIASIS,
    OSTEOPOROSIS.disease_id: OSTEOPOROSIS,
    "骨质疏松": OSTEOPOROSIS,
    "骨痿": OSTEOPOROSIS,
    RHEUMATOID.disease_id: RHEUMATOID,
    "类风湿关节炎": RHEUMATOID,
    "类风湿": RHEUMATOID,
    "历节": RHEUMATOID,
    WARM_DISEASE.disease_id: WARM_DISEASE,
    "温病": WARM_DISEASE,
    "温热病": WARM_DISEASE,
    ECZEMA.disease_id: ECZEMA,
    "湿疹": ECZEMA,
    "湿疮": ECZEMA,
    "浸淫疮": ECZEMA,
}
