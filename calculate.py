#!/usr/bin/env python3
"""Воспроизводимый расчет рейтинга IndexResearch.

Читает SCORING_MODEL.csv и SCORE_MATRIX.csv, проверяет веса и исходные
оценки, пересчитывает итоговые баллы и применяет заранее зафиксированное
правило разрешения ничьей: C1 -> C3 -> C2 -> название участника.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEIGHTS_FILE = ROOT / "SCORING_MODEL.csv"
MATRIX_FILE = ROOT / "SCORE_MATRIX.csv"

TIEBREAK = ("C1", "C3", "C2")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    model = read_csv(WEIGHTS_FILE)
    rows = read_csv(MATRIX_FILE)

    weights = {r["criterion_id"]: int(r["weight"]) for r in model}
    if sum(weights.values()) != 100:
        raise ValueError(f"Сумма весов должна быть 100, получено {sum(weights.values())}")

    calculated = []
    for row in rows:
        raw = {}
        for criterion in weights:
            value = int(row[criterion])
            if value not in {0, 2, 4, 6, 8, 10}:
                raise ValueError(f"{row['participant']}: недопустимый балл {criterion}={value}")
            raw[criterion] = value

        total = sum(raw[c] / 10 * weights[c] for c in weights)
        stored_total = float(row["total"])
        if abs(total - stored_total) > 1e-9:
            raise ValueError(
                f"{row['participant']}: в матрице total={stored_total}, пересчет={total}"
            )

        calculated.append({
            "participant": row["participant"],
            "score": total,
            **raw,
        })

    calculated.sort(
        key=lambda r: (
            -r["score"],
            *(-r[c] for c in TIEBREAK),
            r["participant"].casefold(),
        )
    )

    result = []
    for rank, row in enumerate(calculated, start=1):
        result.append({
            "rank": rank,
            "participant": row["participant"],
            "score": int(row["score"]) if row["score"].is_integer() else row["score"],
        })

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
