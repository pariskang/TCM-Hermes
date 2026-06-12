# 桂枝湯方證合併規則

- **Skill**: `hermes.formula.guizhi_tang`
- **Merged rule**: `MHR_FORMULA_GUIZHI_TANG`
- **Release level**: silver
- **Consensus score**: 0.896
- **Supporting initial rules**: 83

## 归纳主张
桂枝湯可歸納為太陽病、太陽中風、傷寒、中風、妊娠、發熱等方證的核心方（支持條文 83 條，跨 26 部書）。

## 原文证据（节选）
> 脈浮虛者，桂枝湯主之。
> ——《傷寒直格》·諸可下證（SU_BC3C734B7_000312，silver）

> 發熱。汗出。惡風者。桂枝湯主之。
> ——《傷寒論條辨》·辨太陽病脈證並治上編第一（SU_BC91F4420_000067，silver）

> 翕翕發熱。鼻鳴乾嘔者。桂枝湯主之。
> ——《張卿子傷寒論》·辨太陽病脈證並治法上第五（SU_B1CAC3ADF_000762，silver）

> 翕翕發熱。鼻鳴乾嘔者。桂枝湯主之。
> ——《傷寒論綱目》·自汗（SU_B3E16D849_001481，silver）

> 太陽病頭痛發熱汗出惡風者。桂枝湯主之。
> ——《傷寒論辯證廣注》·桂枝湯方（SU_B41512D4B_000403，silver）

> 復煩。脈浮數者。可更發汗。宜桂枝湯主之。
> ——《傷寒論條辨》·辨太陽病脈證並治中篇第二（SU_BC91F4420_000328，silver）

> 太陽病。頭痛發熱。汗出惡風者。桂枝湯主之。
> ——《張卿子傷寒論》·桂枝湯方第一（SU_B1CAC3ADF_000779，silver）

> 太陽病。頭痛發熱。汗出惡風者。桂枝湯主之。
> ——《傷寒論綱目》·表症（SU_B3E16D849_000161，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_BC3C734B7", "book_title": "傷寒直格", "distinct_conditions": ["脈浮虛"], "rule_ids": ["IR_BC3C734B7_000048"]}
- {"kind": "condition_variant", "book_id": "BOOK_JF_SHIYANLU", "book_title": "經方實驗錄", "distinct_conditions": ["渴", "鼻塞"], "rule_ids": ["IR_JF_SHIYANLU_000001", "IR_JF_SHIYANLU_000003", "IR_JF_SHIYANLU_000012"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_LUNZHU", "book_title": "傷寒論注", "distinct_conditions": ["脈浮大", "脈浮緊", "脈緊"], "rule_ids": ["IR_SHL_LUNZHU_000024", "IR_SHL_LUNZHU_000026", "IR_SHL_LUNZHU_000029", "IR_SHL_LUNZHU_000033", "IR_SHL_LUNZHU_000163"]}
- {"kind": "composition_variant", "books": ["傷寒尋源", "傷寒溯源集", "傷寒論(宋本)", "張卿子傷寒論"], "composition": ["厚朴二兩", "杏仁五十個"], "rule_ids": ["IR_B1CAC3ADF_000108", "IR_B8E444005_000288", "IR_SHL_SONGBEN_000511", "IR_SHL_SUYUAN_000142"]}
- {"kind": "composition_variant", "books": ["中寒論辯證廣注", "傷寒尋源", "傷寒懸解", "傷寒溯源集", "傷寒論(宋本)", "張卿子傷寒論"], "composition": ["附子一枚"], "rule_ids": ["IR_B1CAC3ADF_000111", "IR_B1CAC3ADF_000118", "IR_B2EB248E3_000004", "IR_B2EB248E3_000008", "IR_B8E444005_000271"]}
- {"kind": "composition_variant", "books": ["中寒論辯證廣注", "傷寒尋源", "傷寒溯源集", "傷寒論(宋本)", "傷寒論類方", "張卿子傷寒論"], "composition": ["桂枝", "芍藥"], "rule_ids": ["IR_B1CAC3ADF_000117", "IR_B2EB248E3_000007", "IR_B8E444005_000281", "IR_SHL_LEIFANG_000005", "IR_SHL_LEIFANG_000021"]}

## 冲突记录 conflict_set
- 證據中同時出現桂枝湯應用與禁忌表述，需按條件區分。
- 證據中同時出現桂枝湯應用與禁忌表述，需按條件區分。
- 證據中同時出現桂枝湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
