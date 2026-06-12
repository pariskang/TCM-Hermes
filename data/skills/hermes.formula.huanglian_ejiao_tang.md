# 黃連阿膠湯方證合併規則

- **Skill**: `hermes.formula.huanglian_ejiao_tang`
- **Merged rule**: `MHR_FORMULA_HUANGLIAN_EJIAO_TANG`
- **Release level**: silver
- **Consensus score**: 0.913
- **Supporting initial rules**: 30

## 归纳主张
黃連阿膠湯可歸納為少陰病、蓄血、瘀血、下利、傷寒、不得臥等方證的核心方（支持條文 30 條，跨 24 部書）。

## 原文证据（节选）
> 得之二三日。心煩。不得臥。黃連阿膠湯主之。
> ——《傷寒論綱目》·不得臥（SU_B3E16D849_003539，silver）

> 得之二三日以上。心中煩。不得臥。黃連阿膠湯主之。
> ——《張卿子傷寒論》·麻黃附子甘草湯方第八十六（SU_B1CAC3ADF_002024，silver）

> 得之二三日以上。心中煩。不得臥。黃連阿膠湯主之。
> ——《傷寒論綱目》·煩躁（SU_B3E16D849_003476，silver）

> 得之二三日以上。心中煩。不得臥。黃連阿膠湯主之。
> ——《傷寒指掌》·少陰本病述古（SU_B5C5ECAC2_000665，silver）

> 得之二三日以上。心中煩。不得臥。黃連阿膠湯主之。
> ——《傷寒論條辨》·辨少陰病脈證並治第七（SU_BC91F4420_001099，silver）

> 得之二三日以上。心中煩。不得臥。黃連阿膠湯主之。
> ——《傷寒醫訣串解》·少陰篇（SU_BF5CDC206_000165，silver）

> 得之二三日以上。心中湎。不得臥。黃連阿膠湯主之。
> ——《曹氏傷寒金匱發微合刊》·少陰篇（SU_CAOSHI_FAWEI_000809，silver）

> 少陰病得之二三日以上，心中煩不得者，黃連阿膠湯主之。
> ——《傷寒總病論》·少陰證（SU_B3E520529_000061，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_JF_SHIYANLU", "book_title": "經方實驗錄", "distinct_conditions": ["角弓反張"], "rule_ids": ["IR_JF_SHIYANLU_000235"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_LAISU", "book_title": "傷寒來蘇集", "distinct_conditions": ["下利", "惡寒", "瘀血", "發熱", "脈數", "脈浮數", "頭痛"], "rule_ids": ["IR_SHL_LAISU_000265", "IR_SHL_LAISU_000681"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_MINGLI", "book_title": "傷寒明理論", "distinct_conditions": ["傷寒", "喜嘔", "虛煩"], "rule_ids": ["IR_SHL_MINGLI_000053"]}
- {"kind": "composition_variant", "books": ["傷寒來蘇集", "傷寒論輯義", "註解傷寒論"], "composition": ["芍藥", "阿膠", "雞子黃", "黃芩", "黃連"], "rule_ids": ["IR_BBAACE965_001190", "IR_SHL_LAISU_000682", "IR_SHL_ZHUJIE_000869"]}
- {"kind": "composition_variant", "books": ["曹氏傷寒金匱發微合刊"], "composition": ["阿膠", "黃連"], "rule_ids": ["IR_CAOSHI_FAWEI_000734"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["芍藥二兩", "阿膠三兩", "雞子黃三枚", "黃芩二兩", "黃連四兩"], "rule_ids": ["IR_SHL_GUIBEN_000173"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
