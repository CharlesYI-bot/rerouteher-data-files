from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
sys.path.insert(0, str(WORKSPACE / ".work" / "sklearn"))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    top_k_accuracy_score,
)
from sklearn.pipeline import Pipeline  # noqa: E402


MODEL = ROOT / "02_RESUME_MODEL"


def evaluate(pipeline: Pipeline, frame: pd.DataFrame, split: str) -> tuple[dict, pd.DataFrame]:
    texts = frame["text"].fillna("")
    truth = frame["role_id"]
    predicted = pipeline.predict(texts)
    probabilities = pipeline.predict_proba(texts)
    classes = list(pipeline.named_steps["classifier"].classes_)
    top3_indexes = probabilities.argsort(axis=1)[:, -3:][:, ::-1]
    top3 = [[classes[index] for index in indexes] for indexes in top3_indexes]
    report = classification_report(truth, predicted, labels=classes, output_dict=True, zero_division=0)
    metrics = {
        "split": split,
        "n_examples": len(frame),
        "accuracy": float(accuracy_score(truth, predicted)),
        "macro_f1": float(f1_score(truth, predicted, labels=classes, average="macro", zero_division=0)),
        "top3_accuracy": float(top_k_accuracy_score(truth, probabilities, k=3, labels=classes)),
        "per_class": {
            role_id: {
                "precision": float(report[role_id]["precision"]),
                "recall": float(report[role_id]["recall"]),
                "f1": float(report[role_id]["f1-score"]),
                "support": int(report[role_id]["support"]),
            }
            for role_id in classes
        },
    }
    rows = frame[["resume_id", "role_id"]].copy()
    rows.columns = ["resume_id", "true_role_id"]
    rows["predicted_role_id"] = predicted
    rows["predicted_probability"] = probabilities.max(axis=1).round(6)
    rows["top3_role_ids"] = [";".join(values) for values in top3]
    rows["correct"] = rows["true_role_id"].eq(rows["predicted_role_id"])
    return metrics, rows


def main() -> None:
    data = pd.read_csv(MODEL / "D9_training_examples_from_jobhop.csv", dtype={"resume_id": str})
    train = data[data["split"].eq("train")].copy()
    validation = data[data["split"].eq("val")].copy()
    test = data[data["split"].eq("test")].copy()
    candidates = []
    best: tuple[tuple[float, float], float, Pipeline, dict] | None = None
    for c_value in [0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]:
        pipeline = Pipeline(
            [
                (
                    "vectorizer",
                    TfidfVectorizer(
                        lowercase=True,
                        strip_accents="unicode",
                        ngram_range=(1, 2),
                        min_df=2,
                        max_df=0.9,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        C=c_value,
                        class_weight="balanced",
                        max_iter=4000,
                        solver="lbfgs",
                        random_state=42,
                    ),
                ),
            ]
        )
        pipeline.fit(train["text"].fillna(""), train["role_id"])
        metrics, _ = evaluate(pipeline, validation, "val")
        candidates.append({"C": c_value, **{key: metrics[key] for key in ["accuracy", "macro_f1", "top3_accuracy"]}})
        selection_key = (metrics["macro_f1"], metrics["accuracy"])
        if best is None or selection_key > best[0]:
            best = (selection_key, c_value, pipeline, metrics)
    assert best is not None
    _, best_c, pipeline, validation_metrics = best
    test_metrics, test_predictions = evaluate(pipeline, test, "test")
    _, validation_predictions = evaluate(pipeline, validation, "val")
    validation_predictions.to_csv(MODEL / "D9_val_tfidf_logreg_predictions.csv", index=False)
    test_predictions.to_csv(MODEL / "D9_test_tfidf_logreg_predictions.csv", index=False)

    classes = list(pipeline.named_steps["classifier"].classes_)
    cm = confusion_matrix(test_predictions["true_role_id"], test_predictions["predicted_role_id"], labels=classes)
    pd.DataFrame(cm, index=classes, columns=classes).rename_axis("actual_role_id").reset_index().to_csv(
        MODEL / "D9_tfidf_logreg_confusion_matrix.csv", index=False
    )
    per_class_rows = []
    for split, metrics in [("val", validation_metrics), ("test", test_metrics)]:
        for role_id, values in metrics["per_class"].items():
            per_class_rows.append({"split": split, "role_id": role_id, **values})
    pd.DataFrame(per_class_rows).to_csv(MODEL / "D9_tfidf_logreg_per_class_metrics.csv", index=False)

    vectorizer = pipeline.named_steps["vectorizer"]
    vocabulary = pd.DataFrame(
        {"feature": vectorizer.get_feature_names_out(), "idf": vectorizer.idf_}
    ).sort_values("feature")
    vocabulary.to_csv(MODEL / "D9_tfidf_logreg_feature_vocabulary.csv", index=False)
    joblib.dump(pipeline, MODEL / "D9_tfidf_logreg_pipeline.joblib")

    threshold_rows = []
    for split, predictions in [("val", validation_predictions), ("test", test_predictions)]:
        for threshold in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            accepted = predictions[predictions["predicted_probability"] >= threshold]
            threshold_rows.append(
                {
                    "split": split,
                    "threshold": threshold,
                    "accepted_examples": len(accepted),
                    "coverage": round(len(accepted) / len(predictions), 6),
                    "accepted_accuracy": None if accepted.empty else round(float(accepted["correct"].mean()), 6),
                }
            )
    pd.DataFrame(threshold_rows).to_csv(MODEL / "D9_tfidf_logreg_threshold_calibration.csv", index=False)

    metadata = {
        "model": "TF-IDF (1,2-grams) + balanced logistic regression",
        "task_alignment": "Implements the D9 vectorization and classifier process in the task brief.",
        "input_scope": "Prior standardized ESCO occupation titles plus education; no raw resume text.",
        "selection_metric": "validation macro-F1, tie-broken by validation accuracy",
        "selected_C": best_c,
        "grid_results": candidates,
        "validation": validation_metrics,
        "test": test_metrics,
        "feature_count": len(vocabulary),
        "scikit_learn_version": sklearn.__version__,
        "random_state": 42,
        "production_approved": False,
    }
    (MODEL / "D9_tfidf_logreg_metrics.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    existing_path = MODEL / "D9_metrics.json"
    existing = json.loads(existing_path.read_text(encoding="utf-8"))
    existing["tfidf_balanced_logistic_regression"] = metadata
    validation_scores = {
        "multinomial_naive_bayes": existing["validation"]["macro_f1"],
        "minilm_centroid_retrieval": existing["minilm_centroid_benchmark"]["val"]["macro_f1"],
        "tfidf_balanced_logistic_regression": validation_metrics["macro_f1"],
    }
    selected = max(validation_scores, key=validation_scores.get)
    existing["selected_model"] = selected
    existing["selection_metric"] = "validation macro-F1"
    existing["validation_model_comparison"] = validation_scores
    existing["production_recommendation"] = False
    existing["production_blocker"] = (
        "The approved JobHop file contains structured Belgian/Flemish career histories, not raw Malaysian CV text; "
        "the held-out sample is small and class-imbalanced, and no demographic fairness audit is possible."
    )
    existing_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    comparison = [
        {
            "model": "multinomial_naive_bayes",
            "validation_macro_f1": existing["validation"]["macro_f1"],
            "test_macro_f1": existing["test"]["macro_f1"],
            "validation_accuracy": existing["validation"]["accuracy"],
            "test_accuracy": existing["test"]["accuracy"],
            "selected": selected == "multinomial_naive_bayes",
        },
        {
            "model": "minilm_centroid_retrieval",
            "validation_macro_f1": existing["minilm_centroid_benchmark"]["val"]["macro_f1"],
            "test_macro_f1": existing["minilm_centroid_benchmark"]["test"]["macro_f1"],
            "validation_accuracy": existing["minilm_centroid_benchmark"]["val"]["accuracy"],
            "test_accuracy": existing["minilm_centroid_benchmark"]["test"]["accuracy"],
            "selected": selected == "minilm_centroid_retrieval",
        },
        {
            "model": "tfidf_balanced_logistic_regression",
            "validation_macro_f1": validation_metrics["macro_f1"],
            "test_macro_f1": test_metrics["macro_f1"],
            "validation_accuracy": validation_metrics["accuracy"],
            "test_accuracy": test_metrics["accuracy"],
            "selected": selected == "tfidf_balanced_logistic_regression",
        },
    ]
    pd.DataFrame(comparison).to_csv(MODEL / "D9_model_comparison.csv", index=False)
    print(json.dumps({"selected_model": selected, "selected_C": best_c, "validation": validation_metrics, "test": test_metrics}, indent=2))


if __name__ == "__main__":
    main()
