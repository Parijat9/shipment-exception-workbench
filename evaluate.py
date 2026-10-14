import argparse
import json
from pathlib import Path
from engine import classify


def evaluate(predict):
    fixtures = json.loads(
        (Path(__file__).parent / "fixtures/evaluation.json").read_text()
    )
    rows = []
    for item in fixtures:
        if item["split"] != "holdout":
            continue
        try:
            pred = predict(item["note"])
            category = pred["category"]
            error = None
        except Exception as exc:
            category = "error"
            error = type(exc).__name__
        rows.append(
            {
                **item,
                "predicted": category,
                "correct": category == item["expected"],
                "error": error,
            }
        )
    answered = [r for r in rows if r["predicted"] not in ("unknown", "error")]
    return {
        "cases": len(rows),
        "accuracy": sum(r["correct"] for r in rows) / len(rows),
        "coverage": len(answered) / len(rows),
        "answered_accuracy": (
            sum(r["correct"] for r in answered) / len(answered) if answered else None
        ),
        "errors": sum(r["error"] is not None for r in rows),
        "results": rows,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    args = p.parse_args()
    predict = classify
    if args.live:
        from ai import classify_live

        predict = lambda note: classify_live(note)[0]
    result = evaluate(predict)
    result["provider"] = "openai" if args.live else "keyword_baseline"
    out = Path("build")
    out.mkdir(exist_ok=True)
    (
        out / ("evaluation-live.json" if args.live else "evaluation-baseline.json")
    ).write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, indent=2))
