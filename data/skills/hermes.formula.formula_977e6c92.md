# 桂枝加黃耆湯方證合併規則

- **Skill**: `hermes.formula.formula_977e6c92`
- **Merged rule**: `MHR_FORMULA_FORMULA_977E6C92`
- **Release level**: silver
- **Consensus score**: 0.92
- **Supporting initial rules**: 7

## 归纳主张
桂枝加黃耆湯可歸納為黃汗、小便不利、歷節、汗出、身重、無汗等方證的核心方（支持條文 7 條，跨 5 部書）。

## 原文证据（节选）
> 諸病黃家，但利其小便；假令脈浮，當以汗解之，宜桂枝加黃耆湯主之。
> ——《金匱要略方論》·黃疸病脈證并治第十五（SU_JGYL_FANGLUN_000676，silver）

> 諸病黃家，但利其小便；假令脈浮，當以汗解之，宜桂枝加黃耆湯主之。
> ——《金匱要略方論》·黃疸病脈證并治第十五（SU_JGYL_TIAOWEN_000674，silver）

> 而要皆水氣傷心之所致。可以切指之曰。）此為黃汗。（以）桂枝加黃耆湯主之。
> ——《金匱要略淺註》·水氣病脈證并治第十四（SU_JGYL_QIANZHU_000882，silver）

> 若身重，汗出已輒輕者，久久必身瞤，瞤即胸中痛，又從腰以上必汗出，下無汗，腰髖弛痛，如有物在皮中狀，劇者不能食，身疼重，煩躁，小便不利，此為黃汗，桂枝加黃耆湯主之。
> ——《金匱要略方論》·水氣病脈證并治第十四（SU_JGYL_FANGLUN_000636，silver）

> 若身重，汗出已輒輕者，久久必身瞤，瞤即胸中痛，又從腰以上必汗出，下無汗，腰髖弛痛，如有物在皮中狀，劇者不能食，身疼重，煩躁，小便不利，此為黃汗，桂枝加黃耆湯主之。
> ——《金匱要略方論》·水氣病脈證并治第十四（SU_JGYL_TIAOWEN_000634，silver）

> 若汗出已，反發熱者，久久身必甲錯；若發熱不止者，久久必生惡瘡；若身重，汗出已，轍②輕者，久久身必瞤，瞤即胸痛；又從腰以上汗出，以下無汗，腰髖弛痛，如有物在皮中狀，劇則不能食，身疼重，煩躁，小便不利，此為黃汗，桂枝加黃耆湯主之。
> ——《傷寒雜病論(桂本)》·辨咳嗽水飲黃汗歷節病脈證並治（SU_SHL_GUIBEN_001280，silver）

> 黃汗之病，兩脛自冷，假令發熱，此屬歷節，食已汗出，又身常暮盜汗出者，此營氣氣，若汗出已，反發熱者，久久其身必甲錯，發熱不止者，必生惡瘡，若身重汗出已，輒輕者久久必身潤，潤即胸中痛，又從腰以上汗出，下無汗，腰寬弛痛如有物在皮中，狀劇者，不能食疼重煩燥，小便不利，此為黃汗，桂枝加黃耆湯主之
> ——《曹氏傷寒金匱發微合刊》·水氣病脈證並治第十四（SU_CAOSHI_FAWEI_001729，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_CAOSHI_FAWEI", "book_title": "曹氏傷寒金匱發微合刊", "distinct_conditions": ["歷節", "盜汗"], "rule_ids": ["IR_CAOSHI_FAWEI_001230"]}
- {"kind": "condition_variant", "book_id": "BOOK_SHL_GUIBEN", "book_title": "傷寒雜病論(桂本)", "distinct_conditions": ["胸痛"], "rule_ids": ["IR_SHL_GUIBEN_001462"]}
- {"kind": "composition_variant", "books": ["曹氏傷寒金匱發微合刊"], "composition": ["桂枝", "黃耆"], "rule_ids": ["IR_CAOSHI_FAWEI_001232"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["大棗十五枚", "桂枝三兩", "甘草二兩", "生薑三兩", "芍藥三兩", "黃耆二兩"], "rule_ids": ["IR_SHL_GUIBEN_000894", "IR_SHL_GUIBEN_001463"]}

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
