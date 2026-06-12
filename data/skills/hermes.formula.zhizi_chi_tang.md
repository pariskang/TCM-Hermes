# 梔子豉湯方證合併規則

- **Skill**: `hermes.formula.zhizi_chi_tang`
- **Merged rule**: `MHR_FORMULA_ZHIZI_CHI_TANG`
- **Release level**: silver
- **Consensus score**: 0.903
- **Supporting initial rules**: 97

## 归纳主张
梔子豉湯可歸納為陽明病、傷寒、腹滿、結胸、下利、痞等方證的核心方（支持條文 97 條，跨 31 部書）。

## 原文证据（节选）
> 心中懊　。舌上苔者。梔子豉湯主之。
> ——《傷寒論綱目》·陽明經脈（SU_B3E16D849_001973，silver）

> 心中懊　。舌上苔者。梔子豉湯主之。
> ——《傷寒論綱目》·懊（SU_B3E16D849_002366，silver）

> 心中懊　。舌上苔者。梔子豉湯主之。
> ——《傷寒論綱目》·煩躁（SU_B3E16D849_002388，silver）

> 心中懊　。舌上苔者。梔子豉湯主之。
> ——《傷寒論條辨》·辨陽明病脈證並治第四（SU_BC91F4420_000869，silver）

> 若下之。而煩熱。胸中窒者。梔子豉湯主之。
> ——《張卿子傷寒論》·梔子生薑豉湯方第三十五（SU_B1CAC3ADF_001096，silver）

> 若下之。而煩熱。胸中窒者。梔子豉湯主之。
> ——《傷寒論綱目》·發熱（SU_B3E16D849_000575，silver）

> 若下之。而煩熱。胸中窒者。梔子豉湯主之。
> ——《曹氏傷寒金匱發微合刊》·太陽篇（SU_CAOSHI_FAWEI_000262，silver）

> 發汗若下之，而煩熱胸中窒者，梔子豉湯主之。
> ——《傷寒纘論·傷寒緒論》·太陽下篇（SU_B11498305_000166，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B07FA055B", "book_title": "傷寒審證表", "distinct_conditions": ["不大便", "中風", "亡陽", "厥", "吐血", "咽乾", "噦", "四逆"], "rule_ids": ["IR_B07FA055B_000029"]}
- {"kind": "condition_variant", "book_id": "BOOK_B0B74DF58", "book_title": "傷寒恆論", "distinct_conditions": ["痞"], "rule_ids": ["IR_B0B74DF58_000249", "IR_B0B74DF58_000251", "IR_B0B74DF58_000252", "IR_B0B74DF58_000383", "IR_B0B74DF58_000404"]}
- {"kind": "condition_variant", "book_id": "BOOK_B54968951", "book_title": "劉河間傷寒醫鑑", "distinct_conditions": ["脈沉微"], "rule_ids": ["IR_B54968951_000014"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_MINGLI", "book_title": "傷寒明理論", "distinct_conditions": ["喜嘔", "少陰病", "欲嘔"], "rule_ids": ["IR_SHL_MINGLI_000055"]}
- {"kind": "composition_variant", "books": ["傷寒尋源", "傷寒溯源集", "傷寒論(宋本)", "張卿子傷寒論"], "composition": ["甘草二兩"], "rule_ids": ["IR_B1CAC3ADF_000256", "IR_B8E444005_000349", "IR_SHL_SONGBEN_000519", "IR_SHL_SUYUAN_000312"]}
- {"kind": "composition_variant", "books": ["傷寒尋源", "傷寒溯源集", "傷寒論(宋本)", "張卿子傷寒論"], "composition": ["生薑五兩"], "rule_ids": ["IR_B1CAC3ADF_000257", "IR_B8E444005_000350", "IR_SHL_SONGBEN_000520", "IR_SHL_SUYUAN_000313"]}

## 冲突记录 conflict_set
- 證據中同時出現梔子豉湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
