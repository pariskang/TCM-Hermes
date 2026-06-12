# 真武湯方證合併規則

- **Skill**: `hermes.formula.zhenwu_tang`
- **Merged rule**: `MHR_FORMULA_ZHENWU_TANG`
- **Release level**: silver
- **Consensus score**: 0.886
- **Supporting initial rules**: 51

## 归纳主张
真武湯可歸納為下利、少陰病、太陽病、小便不利、心下痞、傷寒等方證的核心方（支持條文 51 條，跨 26 部書）。

## 原文证据（节选）
> 或小便利。或下利。嘔者。真武湯主之。
> ——《傷寒論綱目》·咳悸（SU_B3E16D849_003395，silver）

> 或小便利。或下利。嘔者。真武湯主之。
> ——《傷寒論綱目》·嘔吐下利（SU_B3E16D849_003652，silver）

> 或小便利。或下利。嘔者。真武湯主之。
> ——《傷寒論綱目》·小便不利（SU_B3E16D849_003732，silver）

> 或小便利。或下利。或嘔者。真武湯主之。
> ——《張卿子傷寒論》·白通加豬膽汁方第九十六（SU_B1CAC3ADF_002098，silver）

> 或小便利。或下利。或嘔者。真武湯主之。
> ——《中寒論辯證廣注》·白通加豬膽汁湯方（SU_B2EB248E3_000244，silver）

> 頭眩。身動。振振欲擗地者。真武湯主之。
> ——《傷寒論綱目》·振戰栗（SU_B3E16D849_000656，silver）

> 或小便利。或下利。或嘔者。真武湯主之。
> ——《傷寒論綱目》·腹痛（SU_B3E16D849_003492，silver）

> 或小便利。或下利。或嘔者。真武湯主之。
> ——《傷寒論輯義》·辨少陰病脈證並治（SU_BBAACE965_002906，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B11498305", "book_title": "傷寒纘論·傷寒緒論", "distinct_conditions": ["乾嘔", "喘", "心下痞", "短氣"], "rule_ids": ["IR_B11498305_000085", "IR_B11498305_000369", "IR_B11498305_000903"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_MINGLI", "book_title": "傷寒明理論", "distinct_conditions": ["傷寒", "厥", "惡寒", "惡風", "筋惕肉瞤", "脈微弱", "頭痛"], "rule_ids": ["IR_SHL_MINGLI_000129"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_ZHUJIE", "book_title": "註解傷寒論", "distinct_conditions": ["亡陽"], "rule_ids": ["IR_SHL_ZHUJIE_000325", "IR_SHL_ZHUJIE_000326", "IR_SHL_ZHUJIE_000902"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "傷寒論輯義"], "composition": ["生薑", "白朮", "芍藥", "茯苓", "附子"], "rule_ids": ["IR_BBAACE965_001236", "IR_BC91F4420_000499"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["生薑三兩", "白朮二兩", "芍藥三兩", "茯苓三兩", "附子一枚"], "rule_ids": ["IR_SHL_GUIBEN_000527"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["乾薑二兩", "五味子半升", "生薑三兩", "白朮二兩", "芍藥三兩", "茯苓三兩", "附子一枚"], "rule_ids": ["IR_SHL_GUIBEN_001036"]}

## 冲突记录 conflict_set
- 證據中同時出現真武湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
