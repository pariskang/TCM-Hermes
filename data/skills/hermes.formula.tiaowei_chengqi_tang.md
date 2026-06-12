# 調胃承氣湯方證合併規則

- **Skill**: `hermes.formula.tiaowei_chengqi_tang`
- **Merged rule**: `MHR_FORMULA_TIAOWEI_CHENGQI_TANG`
- **Release level**: silver
- **Consensus score**: 0.91
- **Supporting initial rules**: 47

## 归纳主张
調胃承氣湯可歸納為太陽病、傷寒、下利、陽明病、腹滿、少陰病等方證的核心方（支持條文 47 條，跨 22 部書）。

## 原文证据（节选）
> 發汗不解。蒸蒸發熱者。屬胃也。調胃承氣湯主之。
> ——《傷寒尋源》·發熱（SU_B8E444005_000174，silver）

> 發汗不解。蒸蒸發熱者。屬胃也。調胃承氣湯主之。
> ——《傷寒論輯義》·辨太陽病脈證並治中（SU_BBAACE965_000774，silver）

> 發汗不解。蒸蒸發熱者。屬胃也。調胃承氣湯主之。
> ——《傷寒溯源集》·正陽陽明證治第十二（SU_SHL_SUYUAN_001782，silver）

> 脈當微厥。今反和者。此為內實也。調胃承氣湯主之。
> ——《傷寒論綱目》·譫語鄭聲（SU_B3E16D849_002113，silver）

> 脈當微厥。今反和者。此為內實也。調胃承氣湯主之。
> ——《傷寒論辯證廣注》·調胃承氣湯方（SU_B41512D4B_001372，silver）

> 亦死。不惡寒而下利者。可治。宜用調胃承氣湯主之。
> ——《敖氏傷寒金鏡錄》·第三十一‧黃苔黑中舌（SU_B6C3E769F_000302，silver）

> 脈當微厥。今反和者。此為內實也。調胃承氣湯主之。
> ——《傷寒論輯義》·辨太陽病脈證並治中（SU_BBAACE965_001176，silver）

> 脈當微厥。今反和者。此為內實也。調胃承氣湯主之。
> ——《傷寒論條辨》·辨太陽病脈證並治下編第三（SU_BC91F4420_000733，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B8E444005", "book_title": "傷寒尋源", "distinct_conditions": ["心煩", "陽明病"], "rule_ids": ["IR_B8E444005_000055", "IR_B8E444005_000098", "IR_B8E444005_000129"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_MINGLI", "book_title": "傷寒明理論", "distinct_conditions": ["不大便", "咽乾", "寒熱", "少陰病", "燥屎", "腹滿", "自利"], "rule_ids": ["IR_SHL_MINGLI_000043"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_QJYF", "book_title": "傷寒論(千金翼方)", "distinct_conditions": ["大便難", "潮熱"], "rule_ids": ["IR_SHL_QJYF_000046"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_ZHUJIE", "book_title": "註解傷寒論", "distinct_conditions": ["脈實"], "rule_ids": ["IR_SHL_ZHUJIE_000344", "IR_SHL_ZHUJIE_000375", "IR_SHL_ZHUJIE_000766"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "傷寒論輯義", "註解傷寒論"], "composition": ["大黃", "清酒", "甘草", "芒硝"], "rule_ids": ["IR_BBAACE965_000122", "IR_BC91F4420_000301", "IR_SHL_ZHUJIE_000183"]}
- {"kind": "composition_variant", "books": ["傷寒貫珠集"], "composition": ["大黃", "炙甘草", "芒硝"], "rule_ids": ["IR_SHL_GUANZHU_000103"]}

## 冲突记录 conflict_set
- 證據中同時出現調胃承氣湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
