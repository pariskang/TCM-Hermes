# 麥門冬湯方證合併規則

- **Skill**: `hermes.formula.maimendong_tang`
- **Merged rule**: `MHR_FORMULA_MAIMENDONG_TANG`
- **Release level**: silver
- **Consensus score**: 0.92
- **Supporting initial rules**: 8

## 归纳主张
麥門冬湯可歸納為勞復、傷寒、上氣、發熱、咳、脈數等方證的核心方（支持條文 8 條，跨 7 部書）。

## 原文证据（节选）
> 玉函經。病後勞復。發熱者。麥門冬湯主之。
> ——《傷寒論輯義》·辨陰陽易瘥後勞復病脈證並治（SU_BBAACE965_003464，silver）

> 火逆上氣，咽喉不利，上逆下氣，麥門冬湯主之
> ——《曹氏傷寒金匱發微合刊》·肺痿肺癱咳嗽上氣病脈證治第七（SU_CAOSHI_FAWEI_001382，silver）

> 火逆上氣。咽喉不利。止逆下氣。麥門冬湯主之。
> ——《金匱要略心典》·肺痿肺癰咳嗽上氣病脈證治第七（SU_JGYL_XINDIAN_000476，silver）

> 火逆上氣。咽喉不利。止逆下氣者。麥門冬湯主之。
> ——《金匱玉函經二註》·肺痿肺癰咳嗽上氣病脈證治第七（SU_JGYH_ERZHU_000605，silver）

> 大逆上氣。咽喉不利。止逆下氣者。麥門冬湯主之。
> ——《金匱玉函要略輯義》·論三首、脈證四條、方十五首（SU_JGYL_JIYI_001056，silver）

> 14.19咳而上氣，咽喉不利，脈數者，麥門冬湯主之。
> ——《傷寒雜病論(桂本)》·辨咳嗽水飲黃汗歷節病脈證並治（SU_SHL_GUIBEN_001205，silver）

> 玉函經。傷寒瘥後病篇云。病後勞復發熱者。麥門冬湯主之。
> ——《金匱玉函要略輯義》·論三首、脈證四條、方十五首（SU_JGYL_JIYI_001065，silver）

> 大逆((王雪華：宜作〝火逆〞))上氣，咽喉不利，止逆下氣者((王雪華：當無〝者〞字))，麥門冬湯主之。
> ——《金匱要略方論》·肺痿肺癰咳嗽上氣病脈證治第七（SU_JGYL_TIAOWEN_000273，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_JGYL_JIYI", "book_title": "金匱玉函要略輯義", "distinct_conditions": ["傷寒"], "rule_ids": ["IR_JGYL_JIYI_000115", "IR_JGYL_JIYI_000116"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["咳", "脈數"], "rule_ids": ["IR_SHL_GUIBEN_001378"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["人參二兩", "半夏一升", "大棗十二枚", "甘草二兩", "粳米三合", "麥門冬七升"], "rule_ids": ["IR_SHL_GUIBEN_001379"]}
- {"kind": "composition_variant", "books": ["曹氏傷寒金匱發微合刊"], "composition": ["麥門冬"], "rule_ids": ["IR_CAOSHI_FAWEI_001054"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
