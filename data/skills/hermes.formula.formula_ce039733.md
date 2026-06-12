# 甘草麻黃湯方證合併規則

- **Skill**: `hermes.formula.formula_ce039733`
- **Merged rule**: `MHR_FORMULA_FORMULA_CE039733`
- **Release level**: silver
- **Consensus score**: 0.92
- **Supporting initial rules**: 3

## 归纳主张
甘草麻黃湯可歸納為小便不利、皮水、歷節、目黃、脈沉、脈沉緊等方證的核心方（支持條文 3 條，跨 2 部書）。

## 原文证据（节选）
> 又云。皮水。一身面目悉腫。甘草麻黃湯主之。
> ——《金匱玉函要略輯義》·論七首、脈證五條、方九首（SU_JGYL_JIYI_002250，silver）

> 14.64裏水，一身面目黃腫，其脈沉，小便不利，甘草麻黃湯主之；
> ——《傷寒雜病論(桂本)》·辨咳嗽水飲黃汗歷節病脈證並治（SU_SHL_GUIBEN_001275，silver）

> 14.73病歷節，疼痛，兩足腫，大小便不利，脈沉緊者，甘草麻黃湯主之；
> ——《傷寒雜病論(桂本)》·辨咳嗽水飲黃汗歷節病脈證並治（SU_SHL_GUIBEN_001290，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_JGYL_JIYI", "book_title": "金匱玉函要略輯義", "distinct_conditions": ["皮水"], "rule_ids": ["IR_JGYL_JIYI_000273"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["小便不利", "歷節", "目黃", "脈沉", "脈沉緊"], "rule_ids": ["IR_SHL_GUIBEN_001452", "IR_SHL_GUIBEN_001471"]}
- {"kind": "composition_variant", "books": ["曹氏傷寒金匱發微合刊"], "composition": ["甘草", "麻黃"], "rule_ids": ["IR_CAOSHI_FAWEI_001219"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["甘草二兩", "麻黃四兩"], "rule_ids": ["IR_SHL_GUIBEN_001453"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
