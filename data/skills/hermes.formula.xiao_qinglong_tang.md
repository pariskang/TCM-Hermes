# 小青龍湯方證合併規則

- **Skill**: `hermes.formula.xiao_qinglong_tang`
- **Merged rule**: `MHR_FORMULA_XIAO_QINGLONG_TANG`
- **Release level**: silver
- **Consensus score**: 0.916
- **Supporting initial rules**: 77

## 归纳主张
小青龍湯可歸納為傷寒、小便不利、腹滿、痞、心下痞、少陰病等方證的核心方（支持條文 77 條，跨 33 部書）。

## 原文证据（节选）
> 咳逆倚息不得臥。小青龍湯主之。
> ——《金匱玉函經二註》·痰飲咳嗽病脈證治第十二（SU_JGYH_ERZHU_001045，silver）

> 咳逆倚息不得臥，小青龍湯主之。
> ——《金匱要略方論》·〔附方〕（SU_JGYL_FANGLUN_000537，silver）

> 咳逆倚息不得臥，小青龍湯主之。
> ——《金匱要略方論》·〔附方〕（SU_JGYL_TIAOWEN_000535，silver）

> 咳逆倚息不得臥。小青龍湯主之。
> ——《金匱要略心典》·痰飲咳嗽病脈證治第十二（SU_JGYL_XINDIAN_000897，silver）

> 咳逆倚息。不得臥。小青龍湯主之。
> ——《金匱玉函要略輯義》·論一首、脈證二十一條、方十九首（SU_JGYL_JIYI_001940，silver）

> 乾嘔。身熱微喘。或自利者。小青龍湯主之。
> ——《傷寒論綱目》·乾嘔（SU_B3E16D849_002222，silver）

> 又方。心下有水氣。乾嘔者。小青龍湯主之。
> ——《傷寒百證歌》·第六十四證‧乾嘔歌（SU_BB7301DF2_000192，silver）

> 或小便不利。少腹滿。或喘者。小青龍湯主之。
> ——《張卿子傷寒論》·大青龍湯方第二十一（SU_B1CAC3ADF_000921，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B3E520529", "book_title": "傷寒總病論", "distinct_conditions": ["小便難"], "rule_ids": ["IR_B3E520529_000118"]}
- {"kind": "condition_variant", "book_id": "BOOK_JGYH_ERZHU", "book_title": "金匱玉函經二註", "distinct_conditions": ["心下痞"], "rule_ids": ["IR_JGYH_ERZHU_000156", "IR_JGYH_ERZHU_000372"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["脈浮"], "rule_ids": ["IR_SHL_GUIBEN_000437", "IR_SHL_GUIBEN_000440", "IR_SHL_GUIBEN_000685", "IR_SHL_GUIBEN_001381"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_MINGLI", "book_title": "傷寒明理論", "distinct_conditions": ["下利", "少陰病", "腹痛"], "rule_ids": ["IR_SHL_MINGLI_000082"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "傷寒論輯義"], "composition": ["乾薑", "五味子", "半夏", "桂枝", "甘草", "細辛", "芍藥", "麻黃"], "rule_ids": ["IR_BBAACE965_000191", "IR_BC91F4420_000316"]}
- {"kind": "composition_variant", "books": ["傷寒貫珠集"], "composition": ["乾薑", "半夏", "桂枝", "炙甘草", "石膏", "細辛", "芍藥", "麻黃"], "rule_ids": ["IR_SHL_GUANZHU_000086"]}

## 冲突记录 conflict_set
- 證據中同時出現小青龍湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
