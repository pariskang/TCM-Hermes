# 桂枝去芍藥湯方證合併規則

- **Skill**: `hermes.formula.guizhi_qu_shaoyao_tang`
- **Merged rule**: `MHR_FORMULA_GUIZHI_QU_SHAOYAO_TANG`
- **Release level**: silver
- **Consensus score**: 0.889
- **Supporting initial rules**: 28

## 归纳主张
桂枝去芍藥湯可歸納為太陽病、傷寒、腹滿、胸滿、惡寒、心下滿等方證的核心方（支持條文 28 條，跨 26 部書）。

## 原文证据（节选）
> 下後脈促胸滿者，桂枝去芍藥湯主之。
> ——《傷寒總病論》·可發汗證（SU_B3E520529_000080，silver）

> 下後。脈促。胸滿者。桂枝去芍藥湯主之。
> ——《傷寒論綱目》·胸脅腹脹滿痛（SU_B3E16D849_000958，silver）

> 太陽病。脈促胸滿者。桂枝去芍藥湯主之。
> ——《傷寒尋源》·桂枝去芍藥加附子湯（SU_B8E444005_000416，silver）

> 下後，脈促，胸滿者，桂枝去芍藥湯主之。
> ——《傷寒總病論》·可發汗證（SU_BC2BA03C0_000194，silver）

> 下之後。脈促。胸滿者。桂枝去芍藥湯主之。
> ——《中寒論辯證廣注》·桂枝加附子湯方（SU_B2EB248E3_000018，silver）

> 下之後。脈促。胸滿者。桂枝去芍藥湯主之。
> ——《傷寒論綱目》·太陽經脈（SU_B3E16D849_000403，silver）

> 太陽病下之後。脈促胸滿者。桂枝去芍藥湯主之。
> ——《傷寒論辯證廣注》·桂枝加葛根湯方（SU_B41512D4B_000438，silver）

> 太陽病下之後。脈促胸滿者。桂枝去芍藥湯主之。
> ——《傷寒指掌》·誤下例（SU_B5C5ECAC2_000852，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B9119D083", "book_title": "傷寒大白", "distinct_conditions": ["惡寒"], "rule_ids": ["IR_B9119D083_000536"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_MINGLI", "book_title": "傷寒明理論", "distinct_conditions": ["傷寒", "心下滿", "腹滿"], "rule_ids": ["IR_SHL_MINGLI_000029"]}
- {"kind": "composition_variant", "books": ["傷寒論輯義"], "composition": ["大棗", "桂枝", "甘草", "生薑", "芍藥"], "rule_ids": ["IR_BBAACE965_000062"]}
- {"kind": "composition_variant", "books": ["傷寒貫珠集"], "composition": ["附子一枚"], "rule_ids": ["IR_SHL_GUANZHU_000282"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["大棗十二枚", "桂枝三兩", "甘草二兩", "生薑三兩"], "rule_ids": ["IR_SHL_GUIBEN_000376"]}
- {"kind": "composition_variant", "books": ["註解傷寒論"], "composition": ["桂枝", "芍藥"], "rule_ids": ["IR_SHL_ZHUJIE_001143"]}

## 冲突记录 conflict_set
- 證據中同時出現桂枝去芍藥湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
