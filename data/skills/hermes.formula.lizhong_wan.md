# 理中丸方證合併規則

- **Skill**: `hermes.formula.lizhong_wan`
- **Merged rule**: `MHR_FORMULA_LIZHONG_WAN`
- **Release level**: silver
- **Consensus score**: 0.92
- **Supporting initial rules**: 11

## 归纳主张
理中丸可歸納為霍亂、下利、嘔吐、頭痛、發熱、身疼痛等方證的核心方（支持條文 11 條，跨 11 部書）。

## 原文证据（节选）
> 多虛寒者。吐利行。必不用水。理中丸主之。
> ——《傷寒論輯義》·辨霍亂病脈證並治（SU_BBAACE965_003308，silver）

> 身疼痛熱多欲飲水者。五苓散主之。寒多不用水者。理中丸主之。
> ——《張卿子傷寒論》·辨霍亂病脈證並治第十三（SU_B1CAC3ADF_002373，silver）

> 《活人書》云：霍亂，嘔吐而利，熱多而不渴，寒多而不飢，理中丸主之。
> ——《劉河間傷寒醫鑑》·論霍亂（SU_B54968951_000024，silver）

> 霍亂頭痛發熱身疼痛熱多欲飲水者。五苓散主之。寒多不用水者。理中丸主之。
> ——《傷寒纘論》·雜篇（SU_B5FF1CA1B_001111，silver）

> 霍亂，頭痛發熱，身疼痛，熱多欲飲水者，五苓散主之，寒多不用水者，理中丸主之。
> ——《傷寒貫珠集》·霍亂十一條（SU_SHL_GUANZHU_000219，silver）

> 霍亂，頭痛，發熱，身疼痛，熱多欲飲水者，五苓散主之。寒多不用水者，理中丸主之。
> ——《傷寒論(宋本)》·辨霍亂病脈證並治第十三（SU_SHL_SONGBEN_000866，silver）

> 霍亂，頭痛，發熱，身疼痛，熱多欲飲水者，五苓散主之。寒多不用水者，理中丸主之。
> ——《傷寒論》·辨霍亂病脈證並治（SU_SHL_TIAOWEN_000713，silver）

> 霍亂，頭痛，發熱，身疼痛，熱多欲飲水者，五苓散主之；寒多不用水者，理中丸主之。
> ——《註解傷寒論》·辨霍亂病脈證並治法第十三（SU_SHL_ZHUJIE_001624，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B54968951", "book_title": "劉河間傷寒醫鑑", "distinct_conditions": ["嘔吐", "渴"], "rule_ids": ["IR_B54968951_000021"]}
- {"kind": "condition_variant", "book_id": "BOOK_BBAACE965", "book_title": "傷寒論輯義", "distinct_conditions": ["吐利"], "rule_ids": ["IR_BBAACE965_001387"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "註解傷寒論"], "composition": ["乾薑", "人參", "甘草", "白朮"], "rule_ids": ["IR_BC91F4420_000584", "IR_SHL_ZHUJIE_001039"]}
- {"kind": "composition_variant", "books": ["傷寒貫珠集"], "composition": ["乾薑", "人參", "甘草", "白朮", "蜜"], "rule_ids": ["IR_SHL_GUANZHU_000361"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["乾薑三兩", "人參三兩", "甘草三兩", "白朮三兩"], "rule_ids": ["IR_SHL_GUIBEN_001236"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
