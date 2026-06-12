# 升麻湯方證合併規則

- **Skill**: `hermes.formula.formula_bf0623b7`
- **Merged rule**: `MHR_FORMULA_FORMULA_BF0623B7`
- **Release level**: silver
- **Consensus score**: 0.896
- **Supporting initial rules**: 2

## 归纳主张
升麻湯可歸納為下利、傷寒、面赤、發熱、脈浮大等方證的核心方（支持條文 2 條，跨 2 部書）。

## 原文证据（节选）
> 頭疼發熱。偎人畏寒者。此傷寒症也。升麻湯主之。
> ——《仲景傷寒補亡論》·小兒傷寒十九條（SU_BB711944D_001911，silver）

> 初得病一二日，便成陽毒，或服藥吐下後，變成陽毒，其病腰背痛，煩悶不安，狂言欲走，或見鬼，或下利，其脈浮大而數，面赤班班如錦紋，咽喉痛，吐下膿血，五日可治，七日不可治，升麻湯主之不可作煮散。
> ——《傷寒總病論》·陽毒證（SU_B3E520529_000104，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B3E520529", "book_title": "傷寒總病論", "distinct_conditions": ["下利", "脈浮大", "面赤"], "rule_ids": ["IR_B3E520529_000213"]}
- {"kind": "condition_variant", "book_id": "BOOK_BB711944D", "book_title": "仲景傷寒補亡論", "distinct_conditions": ["傷寒", "發熱"], "rule_ids": ["IR_BB711944D_001347"]}

## 冲突记录 conflict_set
- 證據中同時出現升麻湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
