# 大黃牡丹湯方證合併規則

- **Skill**: `hermes.formula.dahuang_mudan_tang`
- **Merged rule**: `MHR_FORMULA_DAHUANG_MUDAN_TANG`
- **Release level**: silver
- **Consensus score**: 0.906
- **Supporting initial rules**: 5

## 归纳主张
大黃牡丹湯可歸納為腸癰、痞、發熱、惡寒、自汗出、汗出等方證的核心方（支持條文 5 條，跨 5 部書）。

## 原文证据（节选）
> 腸癰者，少腹腫痞，按之即痛如淋，小便自調，時時發熱，自汗出，復惡寒。其脈遲緊者，膿未成，可下之，當有血。脈洪數者，膿已成，不可下也，大黃牡丹湯主之。
> ——《金匱要略方論》·瘡癰腸癰浸淫病脈證并治第十八（SU_JGYL_FANGLUN_000854，silver）

> 腸癰者，少腹腫痞，按之即痛如淋，小便自調，時時發熱，自汗出，復惡寒。其脈遲緊者，膿未成，可下之，當有血。脈洪數者，膿已成，不可下也，大黃牡丹湯主之。
> ——《金匱要略方論》·瘡癰腸癰浸淫病脈證并治第十八（SU_JGYL_TIAOWEN_000852，silver）

> 《金匱》曰：「腸癰者，少腹腫痞，按之即痛如淋，小便自調，時時發熱，自汗出，復惡寒，其脈遲緊者，膿未成，可下之，當有血，脈洪數者，膿已成，不可下也，大黃牡丹湯主之。
> ——《經方實驗錄》·第七九案　腸癰　其三穎師醫案（SU_JF_SHIYANLU_000490，silver）

> 15.17少腹腫痞，按之即痛如淋，小便自調，時時發熱，自汗出，復惡寒，此為腸外有癰也。其脈沉緊者，膿未成也，下之當有血；脈洪數者，膿已成也，可下之，大黃牡丹湯主之。
> ——《傷寒雜病論(桂本)》·辨瘀血吐衄下血瘡癰病脈證並治（SU_SHL_GUIBEN_001328，silver）

> 腸癰之為病，其身甲錯，腹皮急如腫狀，按之濡（此下與後條錯簡，今校正）時時發熱，熱汗出，反惡寒，其脈遲緊者，膿未成，可下之，大黃牡丹湯主之，脈洪數者，膿已成，不可下也（三句舊誤在上，今校正）
> ——《曹氏傷寒金匱發微合刊》·瘡癰，腸癰，浸淫病脈證治第十八（SU_CAOSHI_FAWEI_001981，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_CAOSHI_FAWEI", "book_title": "曹氏傷寒金匱發微合刊", "distinct_conditions": ["汗出"], "rule_ids": ["IR_CAOSHI_FAWEI_001370"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["脈沉緊"], "rule_ids": ["IR_SHL_GUIBEN_001523"]}
- {"kind": "composition_variant", "books": ["曹氏傷寒金匱發微合刊"], "composition": ["大黃"], "rule_ids": ["IR_CAOSHI_FAWEI_001373"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["冬瓜子半升", "大黃四兩", "桃仁五十個", "芒硝三合"], "rule_ids": ["IR_SHL_GUIBEN_001524"]}

## 冲突记录 conflict_set
- 證據中同時出現大黃牡丹湯應用與禁忌表述，需按條件區分。
- 證據中同時出現大黃牡丹湯應用與禁忌表述，需按條件區分。
- 證據中同時出現大黃牡丹湯應用與禁忌表述，需按條件區分。
- 證據中同時出現大黃牡丹湯應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
