# ML and Dataset Instructions

## Scope

`ml` owns data preparation, training, evaluation, and the canonical runtime model. API service code may load the model but must not contain model copies.

## Map

```text
datasets/  Collection guidance, download tools, and local dataset locations
training/  Feature extraction, synthetic data generation, and training
models/    Canonical model artifact consumed by the API and Docker image
```

## Rules

- Keep raw or personal recordings out of Git. Commit only explicit small fixtures or documented metadata.
- Record dataset license and provenance before adding external samples.
- Training scripts import feature definitions from `apps/api/app/services` so inference and training stay aligned.
- New model files replace or version the canonical artifact deliberately; never scatter copies across the repo.
- Report the dataset, feature dimension, class mapping, metrics, and command used to produce a model.
- Model inference must retain a non-ML fallback in the API.

## Commands

```bash
python3 ml/training/generate_synthetic_training_data.py \
  --output ml/datasets/synthetic_training_data.csv
python3 ml/training/train_model.py
python3 ml/training/batch_extract_features.py \
  --input-dir ml/datasets/audio --output /tmp/parrot-features.csv
```

Data requirements: `../docs/requirements/`.
