# 大承氣湯方證合併規則

- **Skill**: `hermes.formula.da_chengqi_tang`
- **Merged rule**: `MHR_FORMULA_DA_CHENGQI_TANG`
- **Release level**: silver
- **Consensus score**: 0.888
- **Supporting initial rules**: 33

## 归纳主张
大承氣湯可歸納為傷寒、陽明病、下利、產後、腹滿、宿食等方證的核心方（支持條文 33 條，跨 17 部書）。

## 原文证据（节选）
> 不食。食則譫語。至夜即愈。宜大承氣湯主之。
> ——《金匱玉函經二註》·婦人產後病脈證治第二十一（SU_JGYH_ERZHU_001774，silver）

> 不食。食則譫語。至夜即愈。宜大承氣湯主之。
> ——《金匱要略心典》·婦人產後病脈證治第二十一（SU_JGYL_XINDIAN_001597，silver）

> 金匱云。下利脈滑者。當有所去。大承氣湯主之。
> ——《曹氏傷寒金匱發微合刊》·陽明篇（SU_CAOSHI_FAWEI_000709，silver）

> 金匱宿食篇云。下利脈滑者。當有所去。大承氣湯主之。
> ——《曹氏傷寒金匱發微合刊》·陽明篇（SU_CAOSHI_FAWEI_000620，silver）

> 病解能食，七八日更發熱者，為胃實，宜大承氣湯主之。
> ——《曹氏傷寒金匱發微合刊》·婦人產後病脈證治第二十一（SU_CAOSHI_FAWEI_002080，silver）

> 病解能食。七八日更發熱者。此為胃實。大承氣湯主之。
> ——《金匱玉函經二註》·婦人產後病脈證治第二十一（SU_JGYH_ERZHU_001760，silver）

> 病解能食，七八日更發熱者，此為胃實，大承氣湯主之。
> ——《金匱要略方論》·婦人產後病脈證治第二十一（SU_JGYL_FANGLUN_000925，silver）

> 病解能食。七八日更發熱者。此為胃實。大承氣湯主之。
> ——《金匱玉函要略輯義》·論一首、證六條、方八首（SU_JGYL_JIYI_003317，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_B0B74DF58", "book_title": "傷寒恆論", "distinct_conditions": ["陰竭"], "rule_ids": ["IR_B0B74DF58_000489"]}
- {"kind": "condition_variant", "book_id": "BOOK_B434348CD", "book_title": "傷寒附翼", "distinct_conditions": ["不得臥", "惡熱", "燥屎", "脈實", "自利"], "rule_ids": ["IR_B434348CD_000072"]}
- {"kind": "condition_variant", "book_id": "BOOK_B9119D083", "book_title": "傷寒大白", "distinct_conditions": ["大便難"], "rule_ids": ["IR_B9119D083_000235", "IR_B9119D083_000240", "IR_B9119D083_000765"]}
- {"kind": "condition_variant", "book_id": "BOOK_CAOSHI_FAWEI", "book_title": "曹氏傷寒金匱發微合刊", "distinct_conditions": ["脈滑"], "rule_ids": ["IR_CAOSHI_FAWEI_000556", "IR_CAOSHI_FAWEI_000648", "IR_CAOSHI_FAWEI_000849", "IR_CAOSHI_FAWEI_001417", "IR_CAOSHI_FAWEI_001422"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["寸口脈浮"], "rule_ids": ["IR_SHL_GUIBEN_000778", "IR_SHL_GUIBEN_000914", "IR_SHL_GUIBEN_001591", "IR_SHL_GUIBEN_001604"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨", "傷寒論輯義", "傷寒貫珠集", "註解傷寒論"], "composition": ["厚朴", "大黃", "枳實", "芒硝"], "rule_ids": ["IR_BBAACE965_000893", "IR_BC91F4420_000358", "IR_SHL_GUANZHU_000400", "IR_SHL_ZHUJIE_000642"]}

## 冲突记录 conflict_set
- 證據中同時出現大承氣湯應用與禁忌表述，需按條件區分。
- 證據中同時出現大承氣湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
