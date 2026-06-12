# 承氣湯方證合併規則

- **Skill**: `hermes.formula.formula_b20941d0`
- **Merged rule**: `MHR_FORMULA_FORMULA_B20941D0`
- **Release level**: silver
- **Consensus score**: 0.918
- **Supporting initial rules**: 11

## 归纳主张
承氣湯可歸納為陽明病、腹滿、下利、小便不利、傷寒、燥屎等方證的核心方（支持條文 11 條，跨 5 部書）。

## 原文证据（节选）
> 脈弦者生。澀者死。承氣湯主之。
> ——《傷寒論綱目》·循衣摸床（SU_B3E16D849_002470，silver）

> 傷寒吐後，腹滿者，承氣湯主之。
> ——《傷寒論(千金翼方)》·太陽病用承氣湯法第五（SU_SHL_QJYF_000056，silver）

> 胃中燥。大便必堅。堅者譫語。承氣湯主之。
> ——《傷寒百證歌》·第五十七證‧譫語歌（SU_BB7301DF2_000173，silver）

> 後溏者。不可下之。有燥屎者。宜承氣湯主之。
> ——《傷寒百證歌》·第五十九證‧懊歌（SU_BB7301DF2_000178，silver）

> 時有微熱。怫鬱不得眠者。有燥屎也。承氣湯主之。
> ——《傷寒九十論》·懊怫鬱證（八十五）（SU_B9DD8A693_000269，silver）

> 時有微熱。怫鬱不得臥。有燥屎故也。承氣湯主之。
> ——《傷寒百證歌》·第六十證‧怫鬱歌（SU_BB7301DF2_000179，silver）

> 或因下利或胃實。（仲景云。下利而譫語為有燥屎。承氣湯主之。
> ——《傷寒百證歌》·第五十七證‧譫語歌（SU_BB7301DF2_000173，silver）

> 小便不利，時有微熱，大便乍難，怫鬱不得臥，此燥屎裡實也，承氣湯主之。
> ——《傷寒六書》·怫鬱（SU_BBA9FB4A6_001025，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B3E16D849", "book_title": "傷寒論綱目", "distinct_conditions": ["脈弦"], "rule_ids": ["IR_B3E16D849_001220"]}
- {"kind": "condition_variant", "book_id": "BOOK_B9DD8A693", "book_title": "傷寒九十論", "distinct_conditions": ["不得眠"], "rule_ids": ["IR_B9DD8A693_000077"]}
- {"kind": "condition_variant", "book_id": "BOOK_BB7301DF2", "book_title": "傷寒百證歌", "distinct_conditions": ["下利"], "rule_ids": ["IR_BB7301DF2_000191", "IR_BB7301DF2_000192", "IR_BB7301DF2_000207", "IR_BB7301DF2_000209"]}
- {"kind": "condition_variant", "book_id": "BOOK_BBA9FB4A6", "book_title": "傷寒六書", "distinct_conditions": ["小便不利"], "rule_ids": ["IR_BBA9FB4A6_000439"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_QJYF", "book_title": "傷寒論(千金翼方)", "distinct_conditions": ["不能食", "傷寒", "喘", "惡寒", "汗出", "潮熱", "短氣", "能食"], "rule_ids": ["IR_SHL_QJYF_000048", "IR_SHL_QJYF_000133", "IR_SHL_QJYF_000144", "IR_SHL_QJYF_000149"]}

## 冲突记录 conflict_set
- 證據中同時出現承氣湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
