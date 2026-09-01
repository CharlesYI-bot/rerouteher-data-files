from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
sys.path.insert(0, str(WORKSPACE / ".work" / "fastembed"))

from fastembed import TextEmbedding  # noqa: E402


REF = ROOT / "01_REFERENCE_TABLES"
MODEL_DIR = ROOT / "02_RESUME_MODEL"
CACHE = ROOT / "00_SOURCE_ARCHIVE" / "EMBEDDING_MODEL_CACHE"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def as_json(vec) -> str:
    return json.dumps([round(float(x), 7) for x in vec], separators=(",", ":"))


def metrics(y_true, y_pred, classes):
    per_class = {}
    f1s = []
    for c in classes:
        tp = sum(y == c and p == c for y, p in zip(y_true, y_pred))
        fp = sum(y != c and p == c for y, p in zip(y_true, y_pred))
        fn = sum(y == c and p != c for y, p in zip(y_true, y_pred))
        support = sum(y == c for y in y_true)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1s.append(f1)
        per_class[c] = {"precision": precision, "recall": recall, "f1": f1, "support": support}
    return {
        "accuracy": sum(y == p for y, p in zip(y_true, y_pred)) / len(y_true),
        "macro_f1": sum(f1s) / len(f1s),
        "per_class": per_class,
    }


def main() -> None:
    embedder = TextEmbedding(model_name=MODEL_NAME, cache_dir=str(CACHE))

    roles_path = REF / "D1_roles.csv"
    roles = pd.read_csv(roles_path)
    role_text = (
        roles["role_title"].fillna("")
        + ". "
        + roles["occupation_description"].fillna("")
        + ". "
        + roles["task_summary"].fillna("")
    ).tolist()
    role_vectors = list(embedder.embed(role_text, batch_size=32))
    roles["embedding_model"] = MODEL_NAME
    roles["role_embedding_384"] = [as_json(v) for v in role_vectors]
    roles.to_csv(roles_path, index=False)

    skills_path = REF / "D6_skill_taxonomy.csv"
    skills = pd.read_csv(skills_path)
    skill_text = (skills["canonical_name"].fillna("") + ". " + skills["definition"].fillna("")).tolist()
    skill_vectors = list(embedder.embed(skill_text, batch_size=64))
    skills["embedding_model"] = MODEL_NAME
    skills["embedding_384"] = [as_json(v) for v in skill_vectors]
    skills.to_csv(skills_path, index=False)

    examples = pd.read_csv(MODEL_DIR / "D9_training_examples_from_jobhop.csv", dtype={"resume_id": str})
    all_vectors = np.asarray(list(embedder.embed(examples["text"].fillna("").tolist(), batch_size=64)))
    train_mask = examples["split"].eq("train").to_numpy()
    classes = sorted(examples.loc[train_mask, "role_id"].unique())
    centroids = {}
    for c in classes:
        mask = train_mask & examples["role_id"].eq(c).to_numpy()
        vector = all_vectors[mask].mean(axis=0)
        norm = np.linalg.norm(vector)
        centroids[c] = vector / norm if norm else vector

    centroid_rows = [
        {"role_id": c, "embedding_model": MODEL_NAME, "centroid_embedding_384": as_json(centroids[c])}
        for c in classes
    ]
    pd.DataFrame(centroid_rows).to_csv(MODEL_DIR / "D9_minilm_role_centroids.csv", index=False)

    result_metrics = {}
    for split in ["val", "test"]:
        indexes = np.flatnonzero(examples["split"].eq(split).to_numpy())
        preds = []
        rows = []
        for idx in indexes:
            vector = all_vectors[idx]
            scores = sorted(
                ((c, float(np.dot(vector, centroids[c]))) for c in classes),
                key=lambda x: x[1],
                reverse=True,
            )
            preds.append(scores[0][0])
            rows.append(
                {
                    "resume_id": examples.iloc[idx]["resume_id"],
                    "true_role_id": examples.iloc[idx]["role_id"],
                    "predicted_role_id": scores[0][0],
                    "cosine_similarity": round(scores[0][1], 6),
                    "top3_role_ids": ";".join(c for c, _ in scores[:3]),
                }
            )
        true = examples.iloc[indexes]["role_id"].tolist()
        result_metrics[split] = metrics(true, preds, classes)
        pd.DataFrame(rows).to_csv(MODEL_DIR / f"D9_{split}_minilm_predictions.csv", index=False)

    metrics_path = MODEL_DIR / "D9_metrics.json"
    report = json.loads(metrics_path.read_text(encoding="utf-8"))
    report["minilm_centroid_benchmark"] = result_metrics
    nb_val = report["validation"]["macro_f1"]
    minilm_val = result_metrics["val"]["macro_f1"]
    if minilm_val > nb_val:
        report["selected_model"] = "minilm_centroid_retrieval"
    report["embedding_model"] = MODEL_NAME
    report["production_recommendation"] = False
    report["production_blocker"] = (
        "Held-out top-1 and macro-F1 are too low for automatic classification. "
        "Use top-3 suggestions with user confirmation and collect labeled raw resume text before retraining."
    )
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "embedding_model": MODEL_NAME,
                "role_vectors": len(role_vectors),
                "skill_vectors": len(skill_vectors),
                "resume_vectors": len(all_vectors),
                "minilm_validation": result_metrics["val"],
                "minilm_test": result_metrics["test"],
                "selected_model": report["selected_model"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
