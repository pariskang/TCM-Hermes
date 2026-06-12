# 甘草乾薑湯方證合併規則

- **Skill**: `hermes.formula.formula_a0ad5583`
- **Merged rule**: `MHR_FORMULA_FORMULA_A0AD5583`
- **Release level**: silver
- **Consensus score**: 0.92
- **Supporting initial rules**: 3

## 归纳主张
甘草乾薑湯可歸納為咳、厥、喘、耳聾、渴、脈沉等方證的核心方（支持條文 3 條，跨 2 部書）。

## 原文证据（节选）
> 腳攣急。服桂枝。得之便厥作。甘草乾薑湯主之。
> ——《傷寒百證歌》·第八十九證‧小便自利歌（SU_BB7301DF2_000264，silver）

> 14.24似咳非咳，唾多涎沫，其人不渴，此為肺冷，甘草乾薑湯主之。
> ——《傷寒雜病論(桂本)》·辨咳嗽水飲黃汗歷節病脈證並治（SU_SHL_GUIBEN_001217，silver）

> 5.51寒病，喘，咳，少氣，不能報息，口唾涎沫，耳聾，嗌乾，此寒邪乘肺也，脈沉而遲者，甘草乾薑湯主之；
> ——《傷寒雜病論(桂本)》·寒病脈證並治第十二（SU_SHL_GUIBEN_000414，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_BB7301DF2", "book_title": "傷寒百證歌", "distinct_conditions": ["厥"], "rule_ids": ["IR_BB7301DF2_000309"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["咳", "喘", "渴", "耳聾", "脈沉"], "rule_ids": ["IR_SHL_GUIBEN_000346", "IR_SHL_GUIBEN_001394"]}
- {"kind": "composition_variant", "books": ["傷寒論辯證廣注"], "composition": ["乾薑", "甘草", "芍藥"], "rule_ids": ["IR_B41512D4B_000114"]}
- {"kind": "composition_variant", "books": ["傷寒論(千金翼方)", "傷寒論條辨", "傷寒論輯義", "傷寒貫珠集", "曹氏傷寒金匱發微合刊", "註解傷寒論"], "composition": ["乾薑", "甘草"], "rule_ids": ["IR_BBAACE965_000117", "IR_BC91F4420_000299", "IR_CAOSHI_FAWEI_000070", "IR_SHL_GUANZHU_000123", "IR_SHL_QJYF_000328"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["乾薑二兩", "甘草四兩"], "rule_ids": ["IR_SHL_GUIBEN_000348", "IR_SHL_GUIBEN_000402", "IR_SHL_GUIBEN_001395"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
