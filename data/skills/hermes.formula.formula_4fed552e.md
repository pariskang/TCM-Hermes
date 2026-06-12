# 理中湯方證合併規則

- **Skill**: `hermes.formula.formula_4fed552e`
- **Merged rule**: `MHR_FORMULA_FORMULA_4FED552E`
- **Release level**: silver
- **Consensus score**: 0.92
- **Supporting initial rules**: 5

## 归纳主张
理中湯可歸納為下利、霍亂、中寒、熱入血室、腹滿、嘔吐等方證的核心方（支持條文 5 條，跨 4 部書）。

## 原文证据（节选）
> 12.4霍亂嘔吐下利，無寒熱，脈濡弱者，理中湯主之。
> ——《傷寒雜病論(桂本)》·辨霍亂吐利病脈證並治（SU_SHL_GUIBEN_001059，silver）

> 太陰中寒症也。外症腹痛吐利手足指冷。六脈沉細。宜理中湯主之。
> ——《傷寒指掌》·診察（SU_B5C5ECAC2_000077，silver）

> 霍亂而頭痛發熱，身體疼痛，熱多欲飲水，五苓散主之；寒多不用水者，理中湯主之。
> ——《傷寒論(千金翼方)》·霍亂病狀第六（SU_SHL_QJYF_000545，silver）

> 為熱入血室。（小柴胡東加當歸生地丹皮）少陰下利膿血。（桃花湯）色紫黑。（理中湯主之）
> ——《傷寒括要》·便膿血（SU_BCCBDEC5F_000188，silver）

> 5.50寒病，腹滿腸鳴，食不化，飧泄，甚則足痿不收，脈遲而濇，此寒邪乘脾也，理中湯主之；
> ——《傷寒雜病論(桂本)》·寒病脈證並治第十二（SU_SHL_GUIBEN_000411，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B5C5ECAC2", "book_title": "傷寒指掌", "distinct_conditions": ["中寒", "吐利", "脈沉細", "腹痛"], "rule_ids": ["IR_B5C5ECAC2_000005"]}
- {"kind": "condition_variant", "book_id": "BOOK_BCCBDEC5F", "book_title": "傷寒括要", "distinct_conditions": ["熱入血室"], "rule_ids": ["IR_BCCBDEC5F_000080"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["嘔吐", "寒熱", "脈遲", "腹滿"], "rule_ids": ["IR_SHL_GUIBEN_000340", "IR_SHL_GUIBEN_001202"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_QJYF", "book_title": "傷寒論(千金翼方)", "distinct_conditions": ["發熱", "頭痛"], "rule_ids": ["IR_SHL_QJYF_000353"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
