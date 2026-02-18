#!/usr/bin/env bash

set -e  # остановить скрипт при любой ошибке

# -----------------------------------------------------------------------------
# Конфигурация
# -----------------------------------------------------------------------------

THRESHOLDS="config/thresholds.yaml"
TRAIN_REFERENCE="config/train_reference.csv"

# -----------------------------------------------------------------------------
# Запуски
# -----------------------------------------------------------------------------

echo "=== MatterGen validation ==="

mvp \
  --input-dir samples/mattergen_cifs \
  --out-dir outputs/mattergen \
  --train-reference "$TRAIN_REFERENCE" \
  --thresholds "$THRESHOLDS"


echo "=== Con-CDVAE validation ==="

mvp \
  --input-dir samples/concdvae_cifs \
  --out-dir outputs/concdvae \
  --train-reference "$TRAIN_REFERENCE" \
  --thresholds "$THRESHOLDS"


echo "=== CrystalFormer validation ==="

mvp \
  --input-dir samples/crystalformer_cifs \
  --out-dir outputs/crystalformer \
  --train-reference "$TRAIN_REFERENCE" \
  --thresholds "$THRESHOLDS"


echo "=== Все проверки завершены ==="
