# 十棗湯方證合併規則

- **Skill**: `hermes.formula.shizao_tang`
- **Merged rule**: `MHR_FORMULA_SHIZAO_TANG`
- **Release level**: silver
- **Consensus score**: 0.885
- **Supporting initial rules**: 45

## 归纳主张
十棗湯可歸納為太陽中風、下利、心下痞、懸飲、傷寒、結胸等方證的核心方（支持條文 45 條，跨 26 部書）。

## 原文证据（节选）
> 病懸飲者，十棗湯主之。
> ——《金匱要略方論》·痰飲咳嗽病脈證并治第十二（SU_JGYL_FANGLUN_000489，silver）

> 病懸飲者，十棗湯主之。
> ——《金匱要略方論》·痰飲咳嗽病脈證并治第十二（SU_JGYL_TIAOWEN_000487，silver）

> 咳家其脈弦，為有水。十棗湯主之。
> ——《金匱要略方論》·〔附方〕（SU_JGYL_FANGLUN_000534，silver）

> 咳家。其脈弦為有水。十棗湯主之。
> ——《金匱玉函要略輯義》·論一首、脈證二十一條、方十九首（SU_JGYL_JIYI_001926，silver）

> 咳家其脈弦，為有水。十棗湯主之。
> ——《金匱要略方論》·〔附方〕（SU_JGYL_TIAOWEN_000532，silver）

> 咳家其脈弦。為有水。十棗湯主之。
> ——《金匱要略心典》·痰飲咳嗽病脈證治第十二（SU_JGYL_XINDIAN_000885，silver）

> 咳家。其脈弦。為有水。十棗湯主之。
> ——《金匱玉函經二註》·痰飲咳嗽病脈證治第十二（SU_JGYH_ERZHU_001036，silver）

> 蓋）咳家。其脈弦。為有水。十棗湯主之。
> ——《金匱要略淺註》·痰飲咳嗽病脈證治第十二（SU_JGYL_QIANZHU_000712，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_CAOSHI_FAWEI", "book_title": "曹氏傷寒金匱發微合刊", "distinct_conditions": ["脈浮"], "rule_ids": ["IR_CAOSHI_FAWEI_000387", "IR_CAOSHI_FAWEI_001142", "IR_CAOSHI_FAWEI_001165"]}
- {"kind": "condition_variant", "book_id": "BOOK_JF_SHIYANLU", "book_title": "經方實驗錄", "distinct_conditions": ["傷寒"], "rule_ids": ["IR_JF_SHIYANLU_000199", "IR_JF_SHIYANLU_000200"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_SUYUAN", "book_title": "傷寒溯源集", "distinct_conditions": ["痰飲", "結胸"], "rule_ids": ["IR_SHL_SUYUAN_000467", "IR_SHL_SUYUAN_000472"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "傷寒論輯義", "傷寒貫珠集", "傷寒雜病論(桂本)", "註解傷寒論"], "composition": ["大戟", "大棗", "甘遂", "芫花"], "rule_ids": ["IR_BBAACE965_000694", "IR_BC91F4420_000044", "IR_SHL_GUANZHU_000092", "IR_SHL_GUIBEN_000689", "IR_SHL_ZHUJIE_000514"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)", "經方實驗錄"], "composition": ["大棗十枚"], "rule_ids": ["IR_JF_SHIYANLU_000201", "IR_SHL_GUIBEN_001364"]}
- {"kind": "composition_variant", "books": ["傷寒來蘇集"], "composition": ["大戟", "甘遂", "芫花"], "rule_ids": ["IR_SHL_LAISU_000197"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
