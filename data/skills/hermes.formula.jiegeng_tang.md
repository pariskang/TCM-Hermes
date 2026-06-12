# 桔梗湯方證合併規則

- **Skill**: `hermes.formula.jiegeng_tang`
- **Merged rule**: `MHR_FORMULA_JIEGENG_TANG`
- **Release level**: silver
- **Consensus score**: 0.918
- **Supporting initial rules**: 10

## 归纳主张
桔梗湯可歸納為肺癰、瘀血、咳、胸滿、咽乾、渴等方證的核心方（支持條文 10 條，跨 9 部書）。

## 原文证据（节选）
> 久久吐膿。如米粥者。為肺癰。桔梗湯主之。
> ——《傷寒論輯義》·辨少陰病脈證並治（SU_BBAACE965_002832，silver）

> 久久吐膿。如米粥者。為肺癰。桔梗湯主之。
> ——《金匱玉函要略輯義》·論三首、脈證四條、方十五首（SU_JGYL_JIYI_001084，silver）

> 15.3膈間停留瘀血，若吐血色黑者，桔梗湯主之。
> ——《傷寒雜病論(桂本)》·辨瘀血吐衄下血瘡癰病脈證並治（SU_SHL_GUIBEN_001304，silver）

> 時濁唾腥臭。久久吐膿如米粥者。為肺癰。桔梗湯主之。
> ——《金匱玉函經二註》·肺痿肺癰咳嗽上氣病脈證治第七（SU_JGYH_ERZHU_000616，silver）

> 時出濁唾腥臭。久久吐膿如米粥者。為肺癰。桔梗湯主之。
> ——《金匱要略心典》·肺痿肺癰咳嗽上氣病脈證治第七（SU_JGYL_XINDIAN_000487，silver）

> 咳而胸滿，振寒脈數，咽乾不渴，時出濁唾腥臭，久久吐膿如米粥者，為肺癰，桔梗湯主之。
> ——《金匱要略方論》·肺痿肺癰咳嗽上氣病脈證治第七（SU_JGYL_FANGLUN_000283，silver）

> 咳而胸滿，振寒脈數，咽乾不渴，時出濁唾腥臭，久久吐膿如米粥者，為肺癰，桔梗湯主之。
> ——《金匱要略方論》·肺痿肺癰咳嗽上氣病脈證治第七（SU_JGYL_TIAOWEN_000281，silver）

> 14.21咳而胸滿，振寒脈數，咽乾不渴，時出濁唾腥臭，久久吐膿，如米粥者，此為肺癰，桔梗湯主之。
> ——《傷寒雜病論(桂本)》·辨咳嗽水飲黃汗歷節病脈證並治（SU_SHL_GUIBEN_001209，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["吐血", "瘀血"], "rule_ids": ["IR_SHL_GUIBEN_001384", "IR_SHL_GUIBEN_001491"]}
- {"kind": "composition_variant", "books": ["傷寒論(千金翼方)", "傷寒論條辨", "傷寒論輯義", "註解傷寒論"], "composition": ["桔梗", "甘草"], "rule_ids": ["IR_BBAACE965_001216", "IR_BC91F4420_000489", "IR_SHL_QJYF_000228", "IR_SHL_ZHUJIE_000889"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["桔梗一兩", "甘草二兩"], "rule_ids": ["IR_SHL_GUIBEN_001020", "IR_SHL_GUIBEN_001385", "IR_SHL_GUIBEN_001493"]}
- {"kind": "composition_variant", "books": ["曹氏傷寒金匱發微合刊"], "composition": ["桔梗"], "rule_ids": ["IR_CAOSHI_FAWEI_000747"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
