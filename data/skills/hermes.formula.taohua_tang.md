# 桃花湯方證合併規則

- **Skill**: `hermes.formula.taohua_tang`
- **Merged rule**: `MHR_FORMULA_TAOHUA_TANG`
- **Release level**: silver
- **Consensus score**: 0.92
- **Supporting initial rules**: 54

## 归纳主张
桃花湯可歸納為下利、少陰病、小便不利、下血、結胸、熱入血室等方證的核心方（支持條文 54 條，跨 31 部書）。

## 原文证据（节选）
> 下利便膿血者。桃花湯主之。
> ——《金匱玉函經二註》·嘔吐噦下利病脈證第十七（SU_JGYH_ERZHU_001597，silver）

> 下利便膿血者、桃花湯主之。
> ——《金匱要略方論》·嘔吐噦下利病脈證治第十七（SU_JGYL_FANGLUN_000820，silver）

> 下利便膿血者。桃花湯主之。
> ——《金匱玉函要略輯義》·論一首、脈證二十七條、方二十三首（SU_JGYL_JIYI_002943，silver）

> 下利便膿血者、桃花湯主之。
> ——《金匱要略方論》·嘔吐噦下利病脈證治第十七（SU_JGYL_TIAOWEN_000818，silver）

> 下利便膿血者。桃花湯主之。
> ——《金匱要略心典》·嘔吐噦下利病脈證治第十七（SU_JGYL_XINDIAN_001409，silver）

> 少陰下利。便膿血者。桃花湯主之。
> ——《傷寒百證歌》·第七十九證‧下膿血歌（SU_BB7301DF2_000237，silver）

> 少陰病，下利膿血者，桃花湯主之。
> ——《傷寒貫珠集》·少陰溫法十五條（SU_SHL_GUANZHU_000428，silver）

> 少陰病，下利便膿血，桃花湯主之。
> ——《傷寒論(千金翼方)》·少陰病狀第二（SU_SHL_QJYF_000284，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_BBA9FB4A6", "book_title": "傷寒六書", "distinct_conditions": ["下血", "不大便", "小便自利", "熱入血室", "瘀血", "結胸", "胸滿", "脈數"], "rule_ids": ["IR_BBA9FB4A6_000152"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "傷寒論輯義", "傷寒貫珠集", "註解傷寒論"], "composition": ["乾薑", "粳米", "赤石脂"], "rule_ids": ["IR_BBAACE965_001204", "IR_BC91F4420_000480", "IR_SHL_GUANZHU_000627", "IR_SHL_ZHUJIE_000877"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["乾薑一兩", "粳米一升", "赤石脂一斤"], "rule_ids": ["IR_SHL_GUIBEN_001007"]}

## 冲突记录 conflict_set
- 證據中同時出現桃花湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
