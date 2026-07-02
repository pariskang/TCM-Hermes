#!/usr/bin/env bash
# Hermes v5 — full reproduction from a clean checkout.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1) acquire the corpus (68 MB, 中醫笈成 book-20180111)
#    the public archive is a flat tree (書名/*.txt); each book carries its
#    own 分類= metadata, which the catalog uses for classification
python3 -m hermes download --extract \
  || echo "download failed — place archives/trees and run: python3 -m hermes import <path>"

# 2) full autonomous pipeline:
#    catalog → segment → 5-layer review → themes → merge → skills → report
#    (scoped by default to the 傷寒金匱 categories via 分類= metadata)
python3 -m hermes pipeline

# 3) research / lineage / paper artifacts
python3 -m hermes research stats
python3 -m hermes research network
python3 -m hermes research map
python3 -m hermes research mine --topic 胸痹
python3 -m hermes lineage 桂枝湯
python3 -m hermes paper 胸痹

# 4) governance check
python3 -m hermes metrics
python3 -m hermes status
