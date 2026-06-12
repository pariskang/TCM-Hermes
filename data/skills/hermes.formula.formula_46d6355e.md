# 芍藥甘草附子湯方證合併規則

- **Skill**: `hermes.formula.formula_46d6355e`
- **Merged rule**: `MHR_FORMULA_FORMULA_46D6355E`
- **Release level**: silver
- **Consensus score**: 0.919
- **Supporting initial rules**: 18

## 归纳主张
芍藥甘草附子湯可歸納為太陽病、風水、痰飲、惡寒、骨節疼痛、渴等方證的核心方（支持條文 18 條，跨 17 部書）。

## 原文证据（节选）
> 病不解。反惡寒者。虛故也。芍藥甘草附子湯主之。
> ——《張卿子傷寒論》·茯苓桂枝白朮甘草湯方第二十八（SU_B1CAC3ADF_001042，silver）

> 病不解。反惡寒者。虛故也。芍藥甘草附子湯主之。
> ——《傷寒論綱目》·惡寒（SU_B3E16D849_000614，silver）

> 發汗病不解，反惡寒者，虛也，芍藥甘草附子湯主之。
> ——《傷寒大白》·惡寒（SU_B9119D083_000051，silver）

> 發汗病不解，反惡寒者，虛故也，芍藥甘草附子湯主之。
> ——《傷寒纘論·傷寒緒論》·太陽下篇（SU_B11498305_000188，silver）

> 發汗病不解。反惡寒者。虛故也。芍藥甘草附子湯主之。
> ——《傷寒纘論》·太陽下編（SU_B5FF1CA1B_000236，silver）

> 發汗病不解。反惡寒者。虛故也。芍藥甘草附子湯主之。
> ——《傷寒尋源》·自汗（SU_B8E444005_000267，silver）

> 發汗病不解。反惡寒者。虛故也。芍藥甘草附子湯主之。
> ——《傷寒論輯義》·辨太陽病脈證並治中（SU_BBAACE965_000745，silver）

> 發汗病不解。反惡寒者。虛故也。芍藥甘草附子湯主之。
> ——《曹氏傷寒金匱發微合刊》·太陽篇（SU_CAOSHI_FAWEI_000220，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_CAOSHI_FAWEI", "book_title": "曹氏傷寒金匱發微合刊", "distinct_conditions": ["渴", "風水", "骨節疼痛"], "rule_ids": ["IR_CAOSHI_FAWEI_000178", "IR_CAOSHI_FAWEI_001201"]}
- {"kind": "condition_variant", "book_id": "BOOK_JF_SHIYANLU", "book_title": "經方實驗錄", "distinct_conditions": ["心下悸", "振振欲擗地", "汗出", "痰飲", "發熱", "身瞤動", "頭眩"], "rule_ids": ["IR_JF_SHIYANLU_000221"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "傷寒論輯義", "傷寒貫珠集", "曹氏傷寒金匱發微合刊", "註解傷寒論"], "composition": ["甘草", "芍藥", "附子"], "rule_ids": ["IR_BBAACE965_000318", "IR_BC91F4420_000142", "IR_CAOSHI_FAWEI_000179", "IR_SHL_GUANZHU_000139", "IR_SHL_ZHUJIE_000283"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["甘草三兩", "芍藥三兩", "附子一枚"], "rule_ids": ["IR_SHL_GUIBEN_000491"]}

## 冲突记录 conflict_set
- 證據中同時出現芍藥甘草附子湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
