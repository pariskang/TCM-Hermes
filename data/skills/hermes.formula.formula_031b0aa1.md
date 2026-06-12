# 茯苓甘草湯方證合併規則

- **Skill**: `hermes.formula.formula_031b0aa1`
- **Merged rule**: `MHR_FORMULA_FORMULA_031B0AA1`
- **Release level**: silver
- **Consensus score**: 0.889
- **Supporting initial rules**: 12

## 归纳主张
茯苓甘草湯可歸納為傷寒、小便不利、渴、汗出、心下悸、厥等方證的核心方（支持條文 12 條，跨 11 部書）。

## 原文证据（节选）
> 故悸也。經曰先治其水。後治其厥。宜茯苓甘草湯主之。
> ——《傷寒捷訣》·心動悸（SU_B18FAB5FB_000165，silver）

> 傷寒汗出而渴者，五苓散主之，不渴者，茯苓甘草湯主之。
> ——《傷寒纘論·傷寒緒論》·太陽中篇（SU_B11498305_000111，silver）

> 傷寒汗出而渴者，五苓散主之；不渴者，茯苓甘草湯主之。
> ——《傷寒論(宋本)》·辨太陽病脈證並治中第六（SU_SHL_SONGBEN_000320，silver）

> 傷寒汗出而渴者，五苓散主之；不渴者，茯苓甘草湯主之。
> ——《傷寒論》·辨太陽病脈證並治中（SU_SHL_TIAOWEN_000167，silver）

> 傷寒汗出而渴者，五苓散主之。不渴者，茯苓甘草湯主之。
> ——《註解傷寒論》·辨太陽病脈證並治法第六（SU_SHL_ZHUJIE_000696，silver）

> 傷寒汗出而心下悸，渴者，五苓散主之，不渴者，茯苓甘草湯主之。
> ——《傷寒論注》·五苓散證（SU_SHL_LUNZHU_000354，silver）

> 傷寒汗出，而心下悸，渴者，五苓散主之，不渴者，茯苓甘草湯主之。
> ——《傷寒來蘇集》·五苓散證（SU_SHL_LAISU_000148，silver）

> 7.44傷寒，汗出而渴，小便不利者，五苓散主之；不渴者，茯苓甘草湯主之。
> ——《傷寒雜病論(桂本)》·辨太陽病脈證並治中（SU_SHL_GUIBEN_000526，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B11498305", "book_title": "傷寒纘論·傷寒緒論", "distinct_conditions": ["小便利"], "rule_ids": ["IR_B11498305_000075", "IR_B11498305_000077"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUANZHU", "book_title": "傷寒貫珠集", "distinct_conditions": ["脈浮數"], "rule_ids": ["IR_SHL_GUANZHU_000158"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["小便不利"], "rule_ids": ["IR_SHL_GUIBEN_000503"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "傷寒論輯義", "註解傷寒論"], "composition": ["桂枝", "甘草", "生薑", "茯苓"], "rule_ids": ["IR_BBAACE965_000343", "IR_BC91F4420_000138", "IR_SHL_ZHUJIE_000301"]}
- {"kind": "composition_variant", "books": ["曹氏傷寒金匱發微合刊"], "composition": ["甘草", "茯苓"], "rule_ids": ["IR_CAOSHI_FAWEI_000195"]}
- {"kind": "composition_variant", "books": ["傷寒貫珠集"], "composition": ["桂枝", "桃核", "甘草", "生薑", "茯苓"], "rule_ids": ["IR_SHL_GUANZHU_000160"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
