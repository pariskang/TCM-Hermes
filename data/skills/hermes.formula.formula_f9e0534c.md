# 桂枝去芍藥加附子湯方證合併規則

- **Skill**: `hermes.formula.formula_f9e0534c`
- **Merged rule**: `MHR_FORMULA_FORMULA_F9E0534C`
- **Release level**: silver
- **Consensus score**: 0.92
- **Supporting initial rules**: 3

## 归纳主张
桂枝去芍藥加附子湯可歸納為太陽病、惡寒、胸滿、脈促等方證的核心方（支持條文 3 條，跨 3 部書）。

## 原文证据（节选）
> 若微惡寒者。桂枝去芍藥加附子湯主之。
> ——《傷寒論輯義》·辨太陽病脈證並治上（SU_BBAACE965_000193，silver）

> 6.23太陽病，下之後，其人惡寒者，桂枝去芍藥加附子湯主之。
> ——《傷寒雜病論(桂本)》·辨太陽病脈證並治上（SU_SHL_GUIBEN_000442，silver）

> 脈促胸滿者。桂枝去芍藥湯主之。若微寒者。桂枝去芍藥加附子湯主之。
> ——《曹氏傷寒金匱發微合刊》·太陽篇（SU_CAOSHI_FAWEI_000085，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_CAOSHI_FAWEI", "book_title": "曹氏傷寒金匱發微合刊", "distinct_conditions": ["胸滿", "脈促"], "rule_ids": ["IR_CAOSHI_FAWEI_000043"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["太陽病"], "rule_ids": ["IR_SHL_GUIBEN_000378"]}
- {"kind": "composition_variant", "books": ["傷寒論輯義"], "composition": ["大棗", "桂枝", "甘草", "生薑", "芍藥", "附子"], "rule_ids": ["IR_BBAACE965_000064"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "註解傷寒論"], "composition": ["附子一枚"], "rule_ids": ["IR_BC91F4420_000060", "IR_SHL_ZHUJIE_001144"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["大棗十二枚", "桂枝三兩", "甘草二兩", "生薑三兩", "附子一枚"], "rule_ids": ["IR_SHL_GUIBEN_000379"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
