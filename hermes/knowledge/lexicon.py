"""Controlled TCM vocabularies for 傷寒/金匱 text mining.

Curated, conservative lexicons.  They power entity extraction, heuristic rule
mining, the adversarial critic's false-support detection and the workbenches.
Terms are traditional-Chinese as found in 中醫笈成 editions.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Diseases / patterns (病名・病證)
# ---------------------------------------------------------------------------

DISEASES = [
    "太陽中風", "太陽傷寒", "太陽病", "陽明病", "少陽病", "太陰病", "少陰病", "厥陰病",
    "傷寒", "中風", "溫病", "風溫", "中暍", "中濕", "霍亂", "陰陽易", "勞復",
    "百合病", "狐惑", "陰陽毒", "瘧病", "瘧母", "中寒",
    "胸痹", "心痛", "短氣病", "腹滿", "寒疝", "宿食",
    "痰飲", "懸飲", "溢飲", "支飲", "留飲", "伏飲", "消渴", "小便不利", "淋病",
    "水氣病", "風水", "皮水", "正水", "石水", "黃汗", "黃疸", "穀疸", "酒疸", "女勞疸",
    "驚悸", "吐衄", "下血", "瘀血", "嘔吐", "噦", "下利", "奔豚", "奔豚氣",
    "瘡癰", "腸癰", "浸淫瘡", "趺蹶", "轉筋", "陰狐疝", "蚘蟲", "蛔厥",
    "血痹", "虛勞", "肺痿", "肺癰", "咳嗽上氣", "肺脹", "奔豚病",
    "歷節", "中風歷節", "痙病", "剛痙", "柔痙", "濕痹", "百合", "臟躁",
    "妊娠", "產後", "熱入血室", "梅核氣", "崩漏", "帶下", "轉胞",
    "結胸", "大結胸", "小結胸", "臟結", "痞", "心下痞", "蓄血", "蓄水", "亡陽", "亡血",
]

# ---------------------------------------------------------------------------
# Symptoms (症狀)
# ---------------------------------------------------------------------------

SYMPTOMS = [
    "發熱", "惡寒", "惡風", "汗出", "自汗出", "無汗", "盜汗", "頭痛", "頭項強痛", "項背強",
    "身疼痛", "體痛", "骨節疼痛", "腰痛", "惡熱", "潮熱", "往來寒熱", "寒熱",
    "口渴", "渴", "消渴", "口苦", "咽乾", "咽痛", "咽中乾", "目眩", "眩冒", "頭眩",
    "鼻鳴", "乾嘔", "嘔吐", "嘔逆", "欲嘔", "喜嘔", "吐利", "噦", "乾噫食臭", "噫氣",
    "下利", "自利", "便膿血", "大便硬", "大便難", "不大便", "燥屎", "腹滿", "腹痛",
    "腹中痛", "少腹滿", "少腹急結", "少腹硬滿", "心下滿", "心下痞", "心下痞硬", "心下急",
    "心下悸", "心動悸", "臍下悸", "心中懊憹", "心煩", "煩躁", "躁煩", "虛煩", "煩驚",
    "胸滿", "胸脅苦滿", "脅下滿", "脅下硬滿", "胸中窒", "胸痛", "脅痛", "心痛徹背",
    "喘", "喘息", "咳", "咳嗽", "上氣", "短氣", "息高", "鼻塞", "噴嚏",
    "小便不利", "小便利", "小便數", "小便難", "小便自利", "遺尿", "尿血",
    "不得眠", "不得臥", "但欲寐", "多眠睡", "嗜臥", "身重", "身癢", "身黃", "目黃",
    "發黃", "手足厥冷", "手足逆冷", "四逆", "厥", "厥冷", "手足溫", "手足煩熱",
    "譫語", "鄭聲", "獨語", "如見鬼狀", "神昏", "不識人", "驚狂", "怵惕",
    "衄", "鼻衄", "吐血", "唾膿血", "咳唾膿血", "面色赤", "面赤", "面色緣緣正赤",
    "口不仁", "口燥", "舌上燥", "舌上苔", "舌上白苔", "口中和", "氣上衝", "氣上衝胸",
    "奄然發狂", "默默不欲飲食", "不欲飲食", "不能食", "能食", "食難用飽", "飢不能食",
    "吐蚘", "下血", "便血", "清膿血", "筋惕肉瞤", "身瞤動", "振振欲擗地", "戰慄",
    "惡寒踡臥", "背惡寒", "骨節痛", "掣痛", "不可屈伸", "身體羸瘦", "形寒",
    "翕翕發熱", "嗇嗇惡寒", "淅淅惡風", "蒸蒸發熱", "手足濈然汗出", "頭汗出",
    "額上汗出", "目瞑", "目赤", "耳聾", "面垢", "遺溺", "口噤", "背反張", "角弓反張",
]

# ---------------------------------------------------------------------------
# Pulses (脈象)
# ---------------------------------------------------------------------------

PULSES = [
    "脈浮緊", "脈浮數", "脈浮緩", "脈浮弱", "脈浮虛", "脈浮滑", "脈浮大", "脈浮遲", "脈浮",
    "脈沉緊", "脈沉遲", "脈沉細", "脈沉微", "脈沉實", "脈沉滑", "脈沉弦", "脈沉", "脈沈",
    "脈遲", "脈數", "脈緩", "脈緊", "脈弦", "脈滑", "脈澀", "脈虛", "脈實",
    "脈微細", "脈微弱", "脈微欲絕", "脈微", "脈細", "脈弱", "脈大", "脈洪大", "脈芤",
    "脈結代", "脈結", "脈代", "脈促", "脈動", "脈伏", "脈絕", "脈不至", "脈靜", "脈急",
    "脈陰陽俱緊", "脈陰陽俱浮", "陽浮而陰弱", "陽微陰弦", "脈虛數", "脈短",
    "寸口脈浮", "寸口脈沉", "寸口脈微", "尺中遲", "尺脈弱", "趺陽脈浮", "趺陽脈緊",
    "趺陽脈微", "少陰脈弱", "脈平", "脈和",
]

# bare pulse qualities used after a 脈 marker
PULSE_QUALITIES = list("浮沉遲數緩緊弦滑澀虛實微細弱大洪芤結代促動伏絕短長") + ["沈"]

# ---------------------------------------------------------------------------
# Pathomechanism (病機)
# ---------------------------------------------------------------------------

PATHOMECHANISMS = [
    "營衛不和", "榮衛不和", "衛強營弱", "營弱衛強", "風寒束表", "寒邪外束",
    "陽明內熱", "裏熱熾盛", "熱結在裏", "熱入血室", "瘀熱在裏", "濕熱內蘊",
    "水飲內停", "水氣凌心", "飲停心下", "痰飲內阻", "陽虛水泛",
    "脾胃虛寒", "中陽不足", "腎陽虛衰", "陰盛陽衰", "陽氣衰微", "亡陽", "陰竭",
    "津液內竭", "胃中乾燥", "胃氣不和", "少陽樞機不利", "肝乘脾", "肝乘肺",
    "上熱下寒", "寒熱錯雜", "表裏同病", "表邪內陷", "邪熱壅肺", "胸陽不振",
]

# ---------------------------------------------------------------------------
# Treatment principles (治法)
# ---------------------------------------------------------------------------

TREATMENT_PRINCIPLES = [
    "解肌發表", "調和營衛", "發汗解表", "辛溫解表", "宣肺平喘", "解表散寒",
    "和解少陽", "和解表裏", "清熱生津", "清裏熱", "瀉熱通便", "攻下實熱", "峻下熱結",
    "潤腸通便", "溫中散寒", "溫中補虛", "回陽救逆", "溫陽利水", "健脾利濕",
    "溫化痰飲", "化痰平喘", "止咳平喘", "溫經散寒", "養血和營", "滋陰降火",
    "清熱利濕", "利濕退黃", "活血化瘀", "破血逐瘀", "緩中補虛", "補中益氣",
    "降逆止嘔", "和胃降逆", "瀉心消痞", "辛開苦降", "寬胸散結", "通陽散結",
    "瀉肺逐飲", "攻逐水飲", "育陰清熱", "安蛔止痛", "固表止汗", "鎮驚安神",
    "可發汗", "當發汗", "宜下之", "當下之", "可下之", "當溫之", "宜溫之", "當吐之",
    "和胃氣", "救裏", "救表", "先溫其裏", "乃攻其表",
]

# verbs that signal an explicit therapeutic instruction in the original text
TREATMENT_VERBS_PATTERN = re.compile(
    r"(當|宜|可|急|先|乃|復)(發汗|汗|下|吐|溫|和|清|利小便|攻|救裏|救表|灸)")

# ---------------------------------------------------------------------------
# Herbs (藥物) — common in 傷寒/金匱 formulas
# ---------------------------------------------------------------------------

HERBS = [
    "桂枝", "芍藥", "白芍", "赤芍", "甘草", "炙甘草", "生薑", "乾薑", "大棗", "麻黃",
    "杏仁", "石膏", "知母", "粳米", "柴胡", "黃芩", "半夏", "人參", "黃連", "黃柏",
    "大黃", "芒硝", "厚朴", "枳實", "梔子", "豆豉", "香豉", "茯苓", "豬苓", "澤瀉",
    "白朮", "蒼朮", "附子", "烏頭", "天雄", "細辛", "五味子", "乾地黃", "生地黃", "熟地黃",
    "當歸", "川芎", "芎藭", "阿膠", "麥門冬", "天門冬", "栝蔞根", "栝蔞實", "瓜蔞",
    "薤白", "白酒", "葛根", "升麻", "前胡", "桔梗", "貝母", "紫菀", "款冬花", "射干",
    "葶藶", "大戟", "甘遂", "芫花", "巴豆", "桃仁", "牡丹皮", "丹皮", "水蛭", "虻蟲",
    "蟅蟲", "蠐螬", "鼠婦", "乾漆", "桃核", "茵陳蒿", "茵陳", "滑石", "猪膏", "亂髮",
    "蜀椒", "吳茱萸", "山茱萸", "薯蕷", "署蕷", "龍骨", "牡蠣", "鉛丹", "代赭石", "代赭",
    "旋覆花", "竹葉", "竹茹", "雞子黃", "雞子白", "蜂蜜", "白蜜", "飴糖", "膠飴",
    "小麥", "大麥", "赤小豆", "薏苡仁", "敗醬", "冬瓜子", "瓜子", "白頭翁", "秦皮",
    "訶梨勒", "烏梅", "蜀漆", "雲母", "防己", "防風", "黃耆", "桑白皮", "白前",
    "椒目", "海藻", "商陸", "葦莖", "石韋", "瞿麥", "蒲灰", "戎鹽", "礬石", "硝石",
    "雄黃", "苦參", "蛇床子", "狼牙", "甘李根白皮", "梓白皮", "連軺", "連翹",
    "土瓜根", "紫參", "澤漆", "鍾乳", "紫石英", "白石英", "赤石脂", "禹餘糧", "太一餘糧",
    "文蛤", "蛤蚧", "百合", "生百合", "天花粉", "王不留行", "蒴藋", "桑東南根",
    "酸棗仁", "梔子仁", "枳殼", "橘皮", "橘紅", "生梓白皮", "苦酒", "清酒", "美酒",
    "童便", "人尿", "猪膽汁", "蜜", "鹽", "粉", "香薷", "藿香", "佩蘭",
]

DOSE_UNITS = ["兩", "斤", "升", "合", "枚", "個", "箇", "把", "尺", "錢", "分", "銖", "斗", "字"]
CN_NUMS = "一二三四五六七八九十百半"

# ---------------------------------------------------------------------------
# Canonical formulas (名方) — pinyin slug, principles, canonical composition
# ---------------------------------------------------------------------------

CANONICAL_FORMULAS: dict[str, dict] = {
    "桂枝湯": {"slug": "guizhi_tang", "principles": ["解肌發表", "調和營衛"],
             "herbs": ["桂枝", "芍藥", "甘草", "生薑", "大棗"]},
    "麻黃湯": {"slug": "mahuang_tang", "principles": ["發汗解表", "宣肺平喘"],
             "herbs": ["麻黃", "桂枝", "杏仁", "甘草"]},
    "葛根湯": {"slug": "gegen_tang", "principles": ["發汗解表", "升津舒筋"],
             "herbs": ["葛根", "麻黃", "桂枝", "芍藥", "甘草", "生薑", "大棗"]},
    "小柴胡湯": {"slug": "xiao_chaihu_tang", "principles": ["和解少陽"],
              "herbs": ["柴胡", "黃芩", "半夏", "人參", "甘草", "生薑", "大棗"]},
    "大柴胡湯": {"slug": "da_chaihu_tang", "principles": ["和解少陽", "瀉熱通便"],
              "herbs": ["柴胡", "黃芩", "半夏", "芍藥", "枳實", "大黃", "生薑", "大棗"]},
    "白虎湯": {"slug": "baihu_tang", "principles": ["清熱生津"],
             "herbs": ["石膏", "知母", "甘草", "粳米"]},
    "白虎加人參湯": {"slug": "baihu_jia_renshen_tang", "principles": ["清熱益氣生津"],
                "herbs": ["石膏", "知母", "甘草", "粳米", "人參"]},
    "大承氣湯": {"slug": "da_chengqi_tang", "principles": ["峻下熱結"],
              "herbs": ["大黃", "厚朴", "枳實", "芒硝"]},
    "小承氣湯": {"slug": "xiao_chengqi_tang", "principles": ["輕下熱結"],
              "herbs": ["大黃", "厚朴", "枳實"]},
    "調胃承氣湯": {"slug": "tiaowei_chengqi_tang", "principles": ["緩下熱結", "和胃氣"],
               "herbs": ["大黃", "甘草", "芒硝"]},
    "桃核承氣湯": {"slug": "taohe_chengqi_tang", "principles": ["破血下瘀"],
               "herbs": ["桃仁", "大黃", "桂枝", "甘草", "芒硝"]},
    "五苓散": {"slug": "wuling_san", "principles": ["溫陽化氣", "利濕行水"],
             "herbs": ["豬苓", "澤瀉", "白朮", "茯苓", "桂枝"]},
    "豬苓湯": {"slug": "zhuling_tang", "principles": ["利水養陰清熱"],
             "herbs": ["豬苓", "茯苓", "澤瀉", "阿膠", "滑石"]},
    "理中丸": {"slug": "lizhong_wan", "principles": ["溫中散寒", "補氣健脾"],
             "herbs": ["人參", "乾薑", "甘草", "白朮"]},
    "四逆湯": {"slug": "sini_tang", "principles": ["回陽救逆"],
             "herbs": ["附子", "乾薑", "甘草"]},
    "通脈四逆湯": {"slug": "tongmai_sini_tang", "principles": ["回陽通脈"],
               "herbs": ["附子", "乾薑", "甘草"]},
    "真武湯": {"slug": "zhenwu_tang", "principles": ["溫陽利水"],
             "herbs": ["茯苓", "芍藥", "白朮", "生薑", "附子"]},
    "苓桂朮甘湯": {"slug": "linggui_zhugan_tang", "principles": ["溫陽化飲", "健脾利濕"],
               "herbs": ["茯苓", "桂枝", "白朮", "甘草"]},
    "小青龍湯": {"slug": "xiao_qinglong_tang", "principles": ["解表散寒", "溫肺化飲"],
              "herbs": ["麻黃", "芍藥", "細辛", "乾薑", "甘草", "桂枝", "五味子", "半夏"]},
    "大青龍湯": {"slug": "da_qinglong_tang", "principles": ["發汗解表", "兼清裏熱"],
              "herbs": ["麻黃", "桂枝", "甘草", "杏仁", "生薑", "大棗", "石膏"]},
    "麻杏甘石湯": {"slug": "maxing_ganshi_tang", "principles": ["清宣肺熱", "止咳平喘"],
               "herbs": ["麻黃", "杏仁", "甘草", "石膏"]},
    "麻黃杏仁甘草石膏湯": {"slug": "maxing_ganshi_tang", "principles": ["清宣肺熱", "止咳平喘"],
                   "herbs": ["麻黃", "杏仁", "甘草", "石膏"]},
    "梔子豉湯": {"slug": "zhizi_chi_tang", "principles": ["清宣鬱熱", "除煩"],
              "herbs": ["梔子", "香豉"]},
    "半夏瀉心湯": {"slug": "banxia_xiexin_tang", "principles": ["辛開苦降", "和胃消痞"],
               "herbs": ["半夏", "黃芩", "乾薑", "人參", "甘草", "黃連", "大棗"]},
    "生薑瀉心湯": {"slug": "shengjiang_xiexin_tang", "principles": ["和胃消痞", "宣散水氣"],
               "herbs": ["生薑", "甘草", "人參", "乾薑", "黃芩", "半夏", "黃連", "大棗"]},
    "甘草瀉心湯": {"slug": "gancao_xiexin_tang", "principles": ["和胃補中", "消痞止利"],
               "herbs": ["甘草", "黃芩", "乾薑", "半夏", "大棗", "黃連", "人參"]},
    "大陷胸湯": {"slug": "da_xianxiong_tang", "principles": ["瀉熱逐水破結"],
              "herbs": ["大黃", "芒硝", "甘遂"]},
    "小陷胸湯": {"slug": "xiao_xianxiong_tang", "principles": ["清熱化痰", "寬胸散結"],
              "herbs": ["黃連", "半夏", "栝蔞實"]},
    "炙甘草湯": {"slug": "zhigancao_tang", "principles": ["益氣滋陰", "通陽復脈"],
              "herbs": ["甘草", "生薑", "人參", "生地黃", "桂枝", "阿膠", "麥門冬", "麻仁", "大棗"]},
    "吳茱萸湯": {"slug": "wuzhuyu_tang", "principles": ["溫中補虛", "降逆止嘔"],
              "herbs": ["吳茱萸", "人參", "生薑", "大棗"]},
    "黃連阿膠湯": {"slug": "huanglian_ejiao_tang", "principles": ["育陰清熱"],
               "herbs": ["黃連", "黃芩", "芍藥", "雞子黃", "阿膠"]},
    "烏梅丸": {"slug": "wumei_wan", "principles": ["安蛔止痛", "寒熱並調"],
             "herbs": ["烏梅", "細辛", "乾薑", "黃連", "當歸", "附子", "蜀椒", "桂枝", "人參", "黃柏"]},
    "白頭翁湯": {"slug": "baitouweng_tang", "principles": ["清熱解毒", "涼血止利"],
              "herbs": ["白頭翁", "黃柏", "黃連", "秦皮"]},
    "茵陳蒿湯": {"slug": "yinchenhao_tang", "principles": ["清熱利濕退黃"],
              "herbs": ["茵陳蒿", "梔子", "大黃"]},
    "桂枝加葛根湯": {"slug": "guizhi_jia_gegen_tang", "principles": ["解肌發表", "升津舒筋"],
                "herbs": ["葛根", "桂枝", "芍藥", "生薑", "甘草", "大棗"]},
    "桂枝加附子湯": {"slug": "guizhi_jia_fuzi_tang", "principles": ["調和營衛", "復陽固表"],
                "herbs": ["桂枝", "芍藥", "甘草", "生薑", "大棗", "附子"]},
    "桂枝加桂湯": {"slug": "guizhi_jia_gui_tang", "principles": ["溫通心陽", "平衝降逆"],
               "herbs": ["桂枝", "芍藥", "生薑", "甘草", "大棗"]},
    "桂枝去芍藥湯": {"slug": "guizhi_qu_shaoyao_tang", "principles": ["解肌祛風", "通陽"],
                "herbs": ["桂枝", "生薑", "甘草", "大棗"]},
    "葛根黃芩黃連湯": {"slug": "gegen_qinlian_tang", "principles": ["解表清裏止利"],
                 "herbs": ["葛根", "甘草", "黃芩", "黃連"]},
    "栝蔞薤白白酒湯": {"slug": "gualou_xiebai_baijiu_tang", "principles": ["通陽散結", "豁痰下氣"],
                 "herbs": ["栝蔞實", "薤白", "白酒"]},
    "栝蔞薤白半夏湯": {"slug": "gualou_xiebai_banxia_tang", "principles": ["通陽散結", "祛痰寬胸"],
                 "herbs": ["栝蔞實", "薤白", "半夏", "白酒"]},
    "腎氣丸": {"slug": "shenqi_wan", "principles": ["溫補腎陽"],
             "herbs": ["乾地黃", "薯蕷", "山茱萸", "澤瀉", "茯苓", "牡丹皮", "桂枝", "附子"]},
    "八味腎氣丸": {"slug": "shenqi_wan", "principles": ["溫補腎陽"],
               "herbs": ["乾地黃", "薯蕷", "山茱萸", "澤瀉", "茯苓", "牡丹皮", "桂枝", "附子"]},
    "當歸芍藥散": {"slug": "danggui_shaoyao_san", "principles": ["養血調肝", "健脾利濕"],
               "herbs": ["當歸", "芍藥", "茯苓", "白朮", "澤瀉", "川芎"]},
    "膠艾湯": {"slug": "jiao_ai_tang", "principles": ["養血止血", "調經安胎"],
             "herbs": ["川芎", "阿膠", "甘草", "艾葉", "當歸", "芍藥", "乾地黃"]},
    "溫經湯": {"slug": "wenjing_tang", "principles": ["溫經散寒", "養血祛瘀"],
             "herbs": ["吳茱萸", "當歸", "川芎", "芍藥", "人參", "桂枝", "阿膠", "牡丹皮",
                       "生薑", "甘草", "半夏", "麥門冬"]},
    "甘麥大棗湯": {"slug": "ganmai_dazao_tang", "principles": ["養心安神", "和中緩急"],
               "herbs": ["甘草", "小麥", "大棗"]},
    "大建中湯": {"slug": "da_jianzhong_tang", "principles": ["溫中補虛", "降逆止痛"],
              "herbs": ["蜀椒", "乾薑", "人參", "膠飴"]},
    "小建中湯": {"slug": "xiao_jianzhong_tang", "principles": ["溫中補虛", "和裏緩急"],
              "herbs": ["桂枝", "甘草", "大棗", "芍藥", "生薑", "膠飴"]},
    "黃耆建中湯": {"slug": "huangqi_jianzhong_tang", "principles": ["溫中補氣", "和裏緩急"],
               "herbs": ["黃耆", "桂枝", "甘草", "大棗", "芍藥", "生薑", "膠飴"]},
    "大黃牡丹湯": {"slug": "dahuang_mudan_tang", "principles": ["瀉熱破瘀", "散結消腫"],
               "herbs": ["大黃", "牡丹皮", "桃仁", "瓜子", "芒硝"]},
    "薏苡附子敗醬散": {"slug": "yiyi_fuzi_baijiang_san", "principles": ["排膿消腫", "振奮陽氣"],
                 "herbs": ["薏苡仁", "附子", "敗醬"]},
    "葶藶大棗瀉肺湯": {"slug": "tingli_dazao_xiefei_tang", "principles": ["瀉肺逐飲"],
                 "herbs": ["葶藶", "大棗"]},
    "十棗湯": {"slug": "shizao_tang", "principles": ["攻逐水飲"],
             "herbs": ["芫花", "甘遂", "大戟", "大棗"]},
    "麥門冬湯": {"slug": "maimendong_tang", "principles": ["滋養肺胃", "降逆下氣"],
              "herbs": ["麥門冬", "半夏", "人參", "甘草", "粳米", "大棗"]},
    "酸棗仁湯": {"slug": "suanzaoren_tang", "principles": ["養血安神", "清熱除煩"],
              "herbs": ["酸棗仁", "甘草", "知母", "茯苓", "川芎"]},
    "大黃蟅蟲丸": {"slug": "dahuang_zhechong_wan", "principles": ["緩中補虛", "祛瘀生新"],
               "herbs": ["大黃", "黃芩", "甘草", "桃仁", "杏仁", "芍藥", "乾地黃", "乾漆",
                         "虻蟲", "水蛭", "蠐螬", "蟅蟲"]},
    "抵當湯": {"slug": "didang_tang", "principles": ["破血逐瘀"],
             "herbs": ["水蛭", "虻蟲", "桃仁", "大黃"]},
    "旋覆代赭湯": {"slug": "xuanfu_daizhe_tang", "principles": ["降逆化痰", "益氣和胃"],
               "herbs": ["旋覆花", "人參", "生薑", "代赭石", "甘草", "半夏", "大棗"]},
    "桂枝甘草湯": {"slug": "guizhi_gancao_tang", "principles": ["溫通心陽"],
               "herbs": ["桂枝", "甘草"]},
    "芍藥甘草湯": {"slug": "shaoyao_gancao_tang", "principles": ["養血柔筋", "緩急止痛"],
               "herbs": ["芍藥", "甘草"]},
    "乾薑附子湯": {"slug": "ganjiang_fuzi_tang", "principles": ["回陽救逆"],
               "herbs": ["乾薑", "附子"]},
    "茯苓四逆湯": {"slug": "fuling_sini_tang", "principles": ["回陽益陰"],
               "herbs": ["茯苓", "人參", "附子", "甘草", "乾薑"]},
    "當歸四逆湯": {"slug": "danggui_sini_tang", "principles": ["溫經散寒", "養血通脈"],
               "herbs": ["當歸", "桂枝", "芍藥", "細辛", "甘草", "通草", "大棗"]},
    "防己黃耆湯": {"slug": "fangji_huangqi_tang", "principles": ["益氣祛風", "健脾利水"],
               "herbs": ["防己", "甘草", "白朮", "黃耆"]},
    "越婢湯": {"slug": "yuebi_tang", "principles": ["發汗利水"],
             "herbs": ["麻黃", "石膏", "生薑", "大棗", "甘草"]},
    "半夏厚朴湯": {"slug": "banxia_houpo_tang", "principles": ["行氣散結", "降逆化痰"],
               "herbs": ["半夏", "厚朴", "茯苓", "生薑", "蘇葉"]},
    "枳實薤白桂枝湯": {"slug": "zhishi_xiebai_guizhi_tang", "principles": ["通陽散結", "祛痰下氣"],
                 "herbs": ["枳實", "厚朴", "薤白", "桂枝", "栝蔞實"]},
    "黃芩湯": {"slug": "huangqin_tang", "principles": ["清熱止利", "和中止痛"],
             "herbs": ["黃芩", "芍藥", "甘草", "大棗"]},
    "桂枝人參湯": {"slug": "guizhi_renshen_tang", "principles": ["溫中解表"],
               "herbs": ["桂枝", "甘草", "白朮", "人參", "乾薑"]},
    "桃花湯": {"slug": "taohua_tang", "principles": ["溫中澀腸止利"],
             "herbs": ["赤石脂", "乾薑", "粳米"]},
    "豬膚湯": {"slug": "zhufu_tang", "principles": ["滋腎潤肺利咽"], "herbs": []},
    "甘草湯": {"slug": "gancao_tang", "principles": ["清熱利咽"], "herbs": ["甘草"]},
    "桔梗湯": {"slug": "jiegeng_tang", "principles": ["宣肺利咽排膿"], "herbs": ["桔梗", "甘草"]},
    "苦酒湯": {"slug": "kujiu_tang", "principles": ["利咽消腫"], "herbs": ["半夏", "雞子白", "苦酒"]},
}

FORMULA_SUFFIXES = "湯散丸飲煎膏丹方"
FORMULA_PATTERN = re.compile(
    rf"[一-鿿]{{1,10}}[{FORMULA_SUFFIXES}]")

# ---------------------------------------------------------------------------
# Conditional / limiting markers the critic checks for (對抗式質疑)
# ---------------------------------------------------------------------------

LIMITING_MARKERS = ["若", "不可", "反", "誤下", "誤汗", "誤治", "慎", "勿", "禁", "未可", "不得"]
OVERGENERALIZATION_MARKERS = ["凡", "皆", "一切", "百病", "諸病", "無不"]

CONTRAINDICATION_PATTERN = re.compile(
    r"(不可|不得|勿|禁|未可|慎不可|切不可)(更行|復|再|妄)?"
    r"(發汗|汗|下|吐|攻|火|灸|刺|溫針|燒針|飲水|與|服)")

MISTREATMENT_PATTERN = re.compile(
    r"(誤|反|若)(發汗|汗|下|吐|攻|火劫|燒針|溫針)|(本不當|不當)(下|汗|吐)")

PROGNOSIS_PATTERN = re.compile(
    r"(必自愈|自愈|欲解|欲愈|必愈|愈|不治|難治|死|必死|可治|易愈|為欲解|解)$")

TRANSMISSION_PATTERN = re.compile(
    r"(傳|轉屬|轉入|內陷|入)(陽明|少陽|太陰|少陰|厥陰|太陽|裏|腑|臟|血室)")

# ---------------------------------------------------------------------------
# Modern-disease mapping (古今病名映射, research workbench)
# ---------------------------------------------------------------------------

DISEASE_MODERN_MAP = [
    {"classical": "白疕", "modern": "银屑病", "certainty": "medium",
     "note": "外科古籍概念，伤寒金匮类罕见，需扩展本草/外科类目"},
    {"classical": "胸痹", "modern": "冠心病/心绞痛相关胸痛", "certainty": "medium",
     "note": "金匮胸痹心痛短气病脉证治"},
    {"classical": "消渴", "modern": "糖尿病及多饮多尿综合征", "certainty": "medium",
     "note": "金匮消渴小便不利淋病脉证并治"},
    {"classical": "歷節", "modern": "类风湿关节炎/痛风性关节炎", "certainty": "medium",
     "note": "金匮中风历节病脉证并治"},
    {"classical": "肺癰", "modern": "肺脓肿", "certainty": "high",
     "note": "咳唾膿血、吐如米粥"},
    {"classical": "腸癰", "modern": "阑尾炎/腹腔脓肿", "certainty": "high",
     "note": "金匮疮痈肠痈浸淫病"},
    {"classical": "黃疸", "modern": "黄疸（肝胆疾病）", "certainty": "high", "note": ""},
    {"classical": "奔豚", "modern": "惊恐发作/自主神经功能紊乱（参考）", "certainty": "low",
     "note": "氣上衝胸"},
    {"classical": "臟躁", "modern": "焦虑/癔症样发作（参考）", "certainty": "low",
     "note": "妇人脏躁，喜悲伤欲哭"},
    {"classical": "痰飲", "modern": "慢性支气管炎/胸腔积液等水液代谢病（参考）",
     "certainty": "low", "note": ""},
    {"classical": "水氣病", "modern": "水肿（心源性/肾源性等）", "certainty": "medium", "note": ""},
    {"classical": "虛勞", "modern": "慢性虚弱性疾病/消耗性疾病", "certainty": "low", "note": ""},
    {"classical": "百合病", "modern": "情感障碍/躯体化障碍（参考）", "certainty": "low", "note": ""},
    {"classical": "狐惑", "modern": "白塞病（参考）", "certainty": "medium",
     "note": "蝕於喉為惑，蝕於陰為狐"},
]

# ---------------------------------------------------------------------------
# Patient-education glossary (通俗解释, 非诊疗建议)
# ---------------------------------------------------------------------------

PATIENT_GLOSSARY = {
    "太陽病": "中医经典《伤寒论》把外感病初起、以怕冷发热头痛为主的阶段称为太阳病，大致相当于感受外邪后的早期表证阶段。",
    "陽明病": "《伤寒论》中外感病发展到以高热、大汗、口渴或便秘为主的阶段，提示热邪入里。",
    "少陽病": "以口苦、咽干、目眩、往来寒热（一阵冷一阵热）为特点的阶段，介于表里之间。",
    "營衛不和": "营和卫是中医对人体防御与营养机能的概念化描述。营卫不和常用来解释怕风、出汗等症状的机理，桂枝汤类方剂常以此立法。",
    "胸痹": "古代对胸闷、胸痛、气短一类病证的统称，《金匮要略》设专篇论述。出现持续胸痛请立即就医。",
    "痰飲": "中医指体内水液代谢失常停聚而成的病理产物，可表现为咳喘、胃部振水声、眩晕等。",
    "桂枝湯": "出自《伤寒论》的经典方，由桂枝、芍药、炙甘草、生姜、大枣组成，古籍用于怕风出汗的外感表虚证。具体是否适合您，必须由执业中医师判断。",
    "六經辨證": "《伤寒论》将外感病过程概括为太阳、阳明、少阳、太阴、少阴、厥阴六个层次，用以指导诊治，是中医重要的辨证框架。",
    "誤治": "古籍中指不恰当的治疗（如不该发汗而发汗），并记载了由此产生的变证与补救方法，体现了古人对医疗安全的重视。",
}

RISK_SIGNALS = [
    {"pattern": "胸痛", "advice": "胸痛持续不缓解可能危及生命"},
    {"pattern": "呼吸困难", "advice": "呼吸困难需要急诊评估"},
    {"pattern": "高热不退", "advice": "持续高热需要就医排查"},
    {"pattern": "意识", "advice": "意识改变属于急症"},
    {"pattern": "昏迷", "advice": "昏迷属于急症"},
    {"pattern": "便血", "advice": "消化道出血需要急诊评估"},
    {"pattern": "呕血", "advice": "消化道出血需要急诊评估"},
    {"pattern": "剧痛", "advice": "急性剧烈疼痛需要急诊评估"},
    {"pattern": "过敏", "advice": "严重过敏反应（喉头水肿、皮疹伴呼吸困难）需立即急救"},
    {"pattern": "抽搐", "advice": "抽搐发作属于急症"},
]


class _Lexicon:
    """Longest-match-first lookup tables."""

    def __init__(self) -> None:
        self.diseases = sorted(set(DISEASES), key=len, reverse=True)
        self.symptoms = sorted(set(SYMPTOMS), key=len, reverse=True)
        self.pulses = sorted(set(PULSES), key=len, reverse=True)
        self.pathomechanisms = sorted(set(PATHOMECHANISMS), key=len, reverse=True)
        self.principles = sorted(set(TREATMENT_PRINCIPLES), key=len, reverse=True)
        self.herbs = sorted(set(HERBS), key=len, reverse=True)
        self.canonical_formulas = CANONICAL_FORMULAS
        self.formula_pattern = FORMULA_PATTERN
        self.limiting_markers = LIMITING_MARKERS
        self.overgeneralization_markers = OVERGENERALIZATION_MARKERS
        self.disease_modern_map = DISEASE_MODERN_MAP
        self.patient_glossary = PATIENT_GLOSSARY
        self.risk_signals = RISK_SIGNALS

    def find_terms(self, text: str, vocab: list[str]) -> list[str]:
        """Longest-match terms found in text, order of first appearance."""
        found: list[tuple[int, str]] = []
        consumed: list[tuple[int, int]] = []
        for term in vocab:
            start = 0
            while True:
                i = text.find(term, start)
                if i < 0:
                    break
                span = (i, i + len(term))
                if not any(a <= span[0] < b or a < span[1] <= b for a, b in consumed):
                    found.append((i, term))
                    consumed.append(span)
                start = i + 1
        found.sort()
        seen, out = set(), []
        for _, t in found:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out

    def find_formulas(self, text: str) -> list[str]:
        """Formula names (X湯/散/丸…), canonical names preferred."""
        hits: list[str] = []
        for name in sorted(self.canonical_formulas, key=len, reverse=True):
            if name in text and name not in hits:
                hits.append(name)
        for m in self.formula_pattern.finditer(text):
            cand = m.group()
            cand = self._trim_formula(cand)
            if cand and cand not in hits and len(cand) >= 3:
                hits.append(cand)
        return hits

    _BAD_FORMULA_PREFIX = re.compile(
        r"^(?:與|宜|服|飲|用|進|可|當|者|則|復|更|急|先|乃|以|及|或|仍|裏|表|其|此|是|得|前|後|余|餘|一|二|三|再|不中|不可|皆|忌|禁)+")

    def _trim_formula(self, cand: str) -> str:
        cand = self._BAD_FORMULA_PREFIX.sub("", cand)
        if cand in self.canonical_formulas:
            return cand
        # derived names (桂枝加葛根湯 / 柴胡加桂枝湯…) must NOT collapse to the
        # base canonical formula — they are distinct prescriptions
        for canon in sorted(self.canonical_formulas, key=len, reverse=True):
            if cand.endswith(canon):
                prefix = cand[:-len(canon)]
                if not prefix or not re.search(r"[一-鿿]", prefix):
                    return canon
                return cand
        return cand

    def formula_slug(self, name: str) -> str:
        info = self.canonical_formulas.get(name)
        if info:
            return info["slug"]
        from ..utils import short_hash
        return f"formula_{short_hash(name, 8).lower()}"

    def formula_principles(self, name: str) -> list[str]:
        info = self.canonical_formulas.get(name)
        return list(info["principles"]) if info else []

    def formula_herbs(self, name: str) -> list[str]:
        info = self.canonical_formulas.get(name)
        return list(info["herbs"]) if info else []


LEXICON = _Lexicon()
