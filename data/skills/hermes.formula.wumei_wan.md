# 烏梅丸方證合併規則

- **Skill**: `hermes.formula.wumei_wan`
- **Merged rule**: `MHR_FORMULA_WUMEI_WAN`
- **Release level**: silver
- **Consensus score**: 0.9
- **Supporting initial rules**: 23

## 归纳主张
烏梅丸可歸納為蛔厥、傷寒、消渴、厥陰病、厥、吐蚘等方證的核心方（支持條文 23 條，跨 21 部書）。

## 原文证据（节选）
> 蛔厥者。烏梅丸主之。
> ——《傷寒論輯義》·辨厥陰病脈證並治（SU_BBAACE965_003054，silver）

> 蛔厥者。烏梅丸主之。
> ——《金匱玉函經二註》·趺蹶手指臂腫轉筋陰狐疝蛔蟲病脈證第十九（SU_JGYH_ERZHU_001685，silver）

> 蚘厥者，烏梅丸主之。
> ——《金匱要略方論》·趺蹶手指臂腫轉筋陰狐疝蚘蟲病脈證治第十九（SU_JGYL_FANGLUN_000887，silver）

> 蛔厥者。烏梅丸主之。
> ——《金匱玉函要略輯義》·論一首、脈證一條、方五首（SU_JGYL_JIYI_003155，silver）

> 蚘厥者，烏梅丸主之。
> ——《金匱要略方論》·趺蹶手指臂腫轉筋陰狐疝蚘蟲病脈證治第十九（SU_JGYL_TIAOWEN_000885，silver）

> 蚘厥者。（以）烏梅丸主之。
> ——《金匱要略淺註》·跌蹶手指臂腫轉筋狐疝蚘蟲病脈證治第十九（SU_JGYL_QIANZHU_001252，silver）

> 其人當自吐蛔。蛔厥者。烏梅丸主之。
> ——《傷寒溯源集》·厥陰證治第二十一（SU_SHL_SUYUAN_002930，silver）

> 尤聞食臭出。其人自吐尤。尤厥者。烏梅丸主之。
> ——《曹氏傷寒金匱發微合刊》·厥陰篇（SU_CAOSHI_FAWEI_000898，silver）

## 版本差异 variant_set
- {"kind": "condition_variant", "book_id": "BOOK_SHL_LUNZHU", "book_title": "傷寒論注", "distinct_conditions": ["厥陰病"], "rule_ids": ["IR_SHL_LUNZHU_000693"]}
- {"kind": "composition_variant", "books": ["傷寒論輯義"], "composition": ["乾薑", "烏梅", "當歸", "細辛", "黃連"], "rule_ids": ["IR_BBAACE965_001297"]}
- {"kind": "composition_variant", "books": ["傷寒論條辨"], "composition": ["乾薑", "烏梅", "當歸", "細辛", "附子", "黃連"], "rule_ids": ["IR_BC91F4420_000522"]}
- {"kind": "composition_variant", "books": ["傷寒來蘇集", "傷寒貫珠集"], "composition": ["乾薑", "人參", "桂枝", "烏梅", "當歸", "細辛", "苦酒", "蜀椒", "蜜", "附子", "黃柏", "黃連"], "rule_ids": ["IR_SHL_GUANZHU_000689", "IR_SHL_LAISU_000715"]}
- {"kind": "composition_variant", "books": ["傷寒雜病論(桂本)"], "composition": ["乾薑十兩", "人參六兩", "桂枝六兩", "烏梅三百枚", "當歸四兩", "細辛六兩", "蜀椒四兩", "附子六兩", "黃柏六兩", "黃連十六兩"], "rule_ids": ["IR_SHL_GUIBEN_000074", "IR_SHL_GUIBEN_001070"]}
- {"kind": "composition_variant", "books": ["註解傷寒論"], "composition": ["乾薑", "烏梅", "細辛", "黃連"], "rule_ids": ["IR_SHL_ZHUJIE_000954"]}

## 冲突记录 conflict_set
- 證據中同時出現烏梅丸應用與禁忌表述，需按條件區分。

## 安全声明
本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，临床使用须由执业中医师结合患者具体情况判断。
