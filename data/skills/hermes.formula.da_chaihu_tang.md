# 大柴胡湯方證合併規則

- **Skill**: `hermes.formula.da_chaihu_tang`
- **Merged rule**: `MHR_FORMULA_DA_CHAIHU_TANG`
- **Release level**: silver
- **Consensus score**: 0.918
- **Supporting initial rules**: 32

## 归纳主张
大柴胡湯可歸納為嘔吐、下利、傷寒、心下痞、痞、腹滿等方證的核心方（支持條文 32 條，跨 24 部書）。

## 原文证据（节选）
> 傳經熱邪，脅滿乾嘔，大柴胡湯主之。
> ——《傷寒大白》·脅滿（SU_B9119D083_001509，silver）

> 心下痞硬。或往來寒熱。大柴胡湯主之。
> ——《傷寒指掌》·下利（述古）（SU_B5C5ECAC2_001120，silver）

> 汗出不解。心中痞硬。嘔吐而下利者。大柴胡湯主之。
> ——《張卿子傷寒論》·桂枝人參湯方第六十四（SU_B1CAC3ADF_001533，silver）

> 汗出不解。心中痞硬。嘔吐而下利者。大柴胡湯主之。
> ——《傷寒論綱目》·發熱（SU_B3E16D849_000565，silver）

> 汗出不解。心下痞硬。嘔吐而下利者。大柴胡湯主之。
> ——《傷寒論綱目》·痞滿（SU_B3E16D849_002969，silver）

> 汗出不解。心下痞硬。嘔吐而下利者。大柴胡湯主之。
> ——《傷寒論辯證廣注》·桂枝人參湯方（SU_B41512D4B_001032，silver）

> 心下痞硬。嘔吐下利。復往來寒熱者。大柴胡湯主之。
> ——《傷寒指掌》·少陽本病述古（SU_B5C5ECAC2_000479，silver）

> 汗出不解。心下痞硬。嘔吐而下利者。大柴胡湯主之。
> ——《傷寒尋源》·發熱（SU_B8E444005_000175，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B18FAB5FB", "book_title": "傷寒捷訣", "distinct_conditions": ["寒熱"], "rule_ids": ["IR_B18FAB5FB_000108"]}
- {"kind": "condition_variant", "book_id": "BOOK_B3E520529", "book_title": "傷寒總病論", "distinct_conditions": ["潮熱"], "rule_ids": ["IR_B3E520529_000141"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_MINGLI", "book_title": "傷寒明理論", "distinct_conditions": ["欲嘔", "腹滿", "自利"], "rule_ids": ["IR_SHL_MINGLI_000088"]}
- {"kind": "composition_variant", "books": ["傷寒論輯義"], "composition": ["半夏", "大棗", "枳實", "柴胡", "生薑", "芍藥", "黃芩"], "rule_ids": ["IR_BBAACE965_000464"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨"], "composition": ["半夏", "大黃", "枳實", "柴胡", "芍藥", "黃芩"], "rule_ids": ["IR_BC91F4420_000088"]}
- {"kind": "composition_variant", "books": ["傷寒貫珠集", "註解傷寒論"], "composition": ["半夏", "大棗", "大黃", "枳實", "柴胡", "生薑", "芍藥", "黃芩"], "rule_ids": ["IR_SHL_GUANZHU_000542", "IR_SHL_ZHUJIE_000370"]}

## 冲突记录 conflict_set
- 證據中同時出現大柴胡湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
