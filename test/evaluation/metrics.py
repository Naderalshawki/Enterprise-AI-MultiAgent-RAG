"""Deterministic retrieval metrics for regression testing."""
from math import log2
from typing import Iterable, Sequence, Set


def recall_at_k(result_ids: Sequence[str], relevant_ids: Set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    return len(set(result_ids[:k]) & relevant_ids) / len(relevant_ids)


def precision_at_k(result_ids: Sequence[str], relevant_ids: Set[str], k: int) -> float:
    top = result_ids[:k]
    return (len(set(top) & relevant_ids) / len(top)) if top else 0.0


def reciprocal_rank(result_ids: Sequence[str], relevant_ids: Set[str]) -> float:
    for index, item in enumerate(result_ids, start=1):
        if item in relevant_ids:
            return 1.0 / index
    return 0.0


def ndcg_at_k(result_ids: Sequence[str], relevant_ids: Set[str], k: int) -> float:
    top = result_ids[:k]
    dcg = sum((1.0 / log2(index + 1)) for index, item in enumerate(top, start=1) if item in relevant_ids)
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / log2(index + 1) for index in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0
