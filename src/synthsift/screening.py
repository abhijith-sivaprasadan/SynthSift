from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

@dataclass
class ScreeningResult:
    name: str
    scores: np.ndarray
    predictions: np.ndarray
    precision: float
    recall: float
    f1: float
    confusion: list[list[int]]


def _builder(kind: str, train_texts, y, seed: int):
    if kind == "word_tfidf_logreg":
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    elif kind == "char_tfidf_logreg":
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True)
    else:
        raise ValueError(f"unknown model: {kind}")
    X = vec.fit_transform(train_texts)
    clf = LogisticRegression(max_iter=3000, class_weight="balanced", random_state=seed)
    clf.fit(X, y)
    return vec, clf


def repeated_oof_scores(texts, y, model: str, n_splits=5, n_repeats=10, seed=42):
    texts = np.asarray(texts, dtype=object)
    y = np.asarray(y, dtype=int)
    splitter = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)
    score_sum = np.zeros(len(y), dtype=float)
    counts = np.zeros(len(y), dtype=int)
    for fold, (tr, te) in enumerate(splitter.split(texts, y)):
        vec, clf = _builder(model, texts[tr].tolist(), y[tr], seed + fold)
        score_sum[te] += clf.predict_proba(vec.transform(texts[te].tolist()))[:, 1]
        counts[te] += 1
    if not np.all(counts == n_repeats):
        raise RuntimeError("each observation should be held out once per repeat")
    return score_sum / counts


def evaluate_scores(y, scores, threshold=0.5, name="model"):
    y = np.asarray(y, dtype=int)
    scores = np.asarray(scores, dtype=float)
    pred = (scores >= threshold).astype(int)
    return ScreeningResult(
        name=name,
        scores=scores,
        predictions=pred,
        precision=float(precision_score(y, pred, zero_division=0)),
        recall=float(recall_score(y, pred, zero_division=0)),
        f1=float(f1_score(y, pred, zero_division=0)),
        confusion=confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    )


def workload_at_recall(y, scores, target):
    y = np.asarray(y, dtype=int)
    order = np.argsort(-np.asarray(scores, dtype=float))
    positives = int(y.sum())
    needed = int(np.ceil(target * positives - 1e-12))
    found = 0
    for rank, idx in enumerate(order, start=1):
        found += int(y[idx] == 1)
        if found >= needed:
            return {"screen_n": rank, "achieved_recall": found / positives, "workload_reduction": 1 - rank / len(y)}
    return {"screen_n": len(y), "achieved_recall": found / positives if positives else 0.0, "workload_reduction": 0.0}


def bootstrap_ci(y, predictions, metric, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    y = np.asarray(y, dtype=int); p = np.asarray(predictions, dtype=int)
    values=[]
    n=len(y)
    fn={"precision":precision_score,"recall":recall_score,"f1":f1_score}[metric]
    for _ in range(n_boot):
        idx=rng.integers(0,n,n)
        if len(np.unique(y[idx]))<2: continue
        values.append(fn(y[idx],p[idx],zero_division=0))
    if not values: return [None,None]
    return [float(np.quantile(values,.025)),float(np.quantile(values,.975))]
