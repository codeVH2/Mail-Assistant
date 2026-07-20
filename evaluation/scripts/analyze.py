from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from scipy import stats

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DATASET = Path(__file__).resolve().parents[1] / "dataset" / "eval_set.json"
PROVIDERS = ["local", "cloud"]
GOLD_CATEGORIES = ["work", "personal", "urgent"]


def load_df(path: Path) -> pd.DataFrame:
    """Load a JSON array into a DataFrame, preserving `id` as a string."""
    return pd.DataFrame(json.loads(path.read_text()))


def majority(s: pd.Series):
    """Most frequent value; on ties, the first by value order.
    Returns None if every run in the group failed to parse (all-null)."""
    m = s.mode()
    return m.iloc[0] if not m.empty else None


def _top_count(s: pd.Series) -> int:
    """Size of the most frequent (non-null) prediction; 0 if all failed."""
    vc = s.value_counts()
    return int(vc.iloc[0]) if not vc.empty else 0


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse the N runs per email into one row (indexed by id)."""
    df = df.copy()
    # A failed parse stores None, and the LLM may emit the score as a string
    # ("0.8"). Coerce so one bad run can't flip the column to object dtype and
    # break .mean(): valid numeric strings survive, junk becomes NaN (skipped).
    df["scoreFromAI"] = pd.to_numeric(df["scoreFromAI"], errors="coerce")
    agg = df.groupby("id").agg(
        category_gold=("category_gold", "first"),
        score_gold=("score_gold", "first"),
        pred_category=("categoryFromAI", majority),
        n_runs=("run", "count"),
        top_count=("categoryFromAI", _top_count),
        score_mean=("scoreFromAI", "mean"),
        score_std=("scoreFromAI", "std"),
    )
    agg["stable"] = agg["top_count"] == agg["n_runs"]
    agg["correct"] = agg["pred_category"] == agg["category_gold"]
    agg["score_err"] = (agg["score_mean"] - agg["score_gold"]).abs()
    return agg


def build_summary(aggs: dict[str, pd.DataFrame], dataset: pd.DataFrame) -> pd.DataFrame:
    """One row per email, both providers side by side."""
    summary = dataset[["id", "size", "category", "score_gold"]].copy()
    summary = summary.rename(columns={"category": "category_gold"})
    for p in PROVIDERS:
        a = aggs[p].copy()
        a["agree"] = a["top_count"].astype(str) + "/" + a["n_runs"].astype(str)
        cols = a[["pred_category", "agree", "correct", "score_mean", "score_err"]].round(3)
        cols = cols.add_prefix(f"{p}_")
        summary = summary.merge(cols, left_on="id", right_index=True)
    return summary


def report(provider: str, df: pd.DataFrame, agg: pd.DataFrame, sizes: pd.Series) -> None:
    print(f"=== {provider.upper()} ===")
    per_run = (df["categoryFromAI"] == df["category_gold"]).mean()
    print(f"  category accuracy (majority vote, {len(agg)} emails): {agg['correct'].mean():.1%}")
    print(f"  category accuracy (per run, {len(df)} runs):    {per_run:.1%}")
    print(f"  category stability (all runs agreed):        {agg['stable'].mean():.1%}")
    print(f"  score MAE (mean |pred - gold|):              {agg['score_err'].mean():.3f}")

    # Confusion matrix: gold (rows) vs majority-vote prediction (cols).
    cm = pd.crosstab(agg["category_gold"], agg["pred_category"])
    cm = cm.reindex(index=GOLD_CATEGORIES, fill_value=0)
    print("\n  confusion (gold \\ pred):")
    print("  " + cm.to_string().replace("\n", "\n  "))

    # Size effect: all categories (now balanced 10 small / 10 medium / 10 large each).
    bs = agg.copy()
    bs["size"] = bs.index.map(sizes)
    by_size = (
        bs.groupby("size")
        .agg(n=("correct", "size"), accuracy=("correct", "mean"), score_mae=("score_err", "mean"))
        .reindex(["small", "medium", "large"])
        .dropna(how="all")
    )
    print("\n  by size (all categories):")
    print("  " + by_size.round(3).to_string().replace("\n", "\n  "))
    print()


def compute_paired_tests(aggs: dict[str, pd.DataFrame], alpha: float = 0.05) -> dict:
    """Compute the paired cloud-vs-local tests and return the raw numbers.

    Category: McNemar exact test — a two-sided binomial test over the
    discordant pairs (only emails where the two providers disagree carry
    information; concordant pairs are uninformative by construction).
    Score: Wilcoxon signed-rank over the paired absolute errors |pred - gold|
    (non-parametric paired test; does not assume the errors are normal).

    Separated from `paired_tests` so plots.py can render the same numbers
    without duplicating the statistics.
    """
    local, cloud = aggs["local"], aggs["cloud"]
    ids = local.index.intersection(cloud.index)
    lc, cc = local.loc[ids, "correct"], cloud.loc[ids, "correct"]

    # Discordant pairs only.
    b = int((cc & ~lc).sum())  # cloud correct, local wrong
    c = int((lc & ~cc).sum())  # local correct, cloud wrong
    n_disc = b + c
    # Exact two-sided McNemar = binomial test of b out of (b+c) at p=0.5.
    p_cat = stats.binomtest(b, n_disc, 0.5).pvalue if n_disc else None
    cat_better = ("cloud" if b > c else "local" if c > b else "neither") if n_disc else None

    le, ce = local.loc[ids, "score_err"], cloud.loc[ids, "score_err"]
    # Drop any email whose score_err is NaN for either provider (total parse
    # failure across all runs) so the paired test gets clean, aligned arrays.
    paired = pd.notna(le) & pd.notna(ce)
    le, ce = le[paired], ce[paired]
    local_mae, cloud_mae = le.mean(), ce.mean()
    try:
        w = stats.wilcoxon(le, ce)
        w_stat, p_score = float(w.statistic), float(w.pvalue)
        score_better = "cloud" if cloud_mae < local_mae else "local" if local_mae < cloud_mae else "neither"
    except ValueError:
        w_stat = p_score = score_better = None

    return {
        "alpha": alpha,
        "n_emails": len(ids),
        "b": b,  # cloud correct, local wrong
        "c": c,  # local correct, cloud wrong
        "n_discordant": n_disc,
        "p_cat": p_cat,
        "cat_better": cat_better,
        "local_mae": local_mae,
        "cloud_mae": cloud_mae,
        "w_stat": w_stat,
        "p_score": p_score,
        "score_better": score_better,
    }


def paired_tests(aggs: dict[str, pd.DataFrame], alpha: float = 0.05) -> None:
    r = compute_paired_tests(aggs, alpha)

    print("=== PAIRED TESTS (cloud vs local, same emails) ===")
    print(f"  category — McNemar exact (n={r['n_emails']} emails):")
    print(f"    cloud correct / local wrong (b): {r['b']}")
    print(f"    local correct / cloud wrong (c): {r['c']}")
    print(f"    discordant pairs (b+c):          {r['n_discordant']}")
    if r["p_cat"] is not None:
        sig = "significant" if r["p_cat"] < alpha else "n.s."
        print(f"    p-value: {r['p_cat']:.4f}  ({sig} at α={alpha}; favours {r['cat_better']})")
    else:
        print("    p-value: n/a (no discordant pairs — providers identical on category)")

    print("  score — Wilcoxon signed-rank (paired |pred - gold|):")
    print(f"    local mean |err|: {r['local_mae']:.3f}   cloud mean |err|: {r['cloud_mae']:.3f}")
    if r["p_score"] is not None:
        sig = "significant" if r["p_score"] < alpha else "n.s."
        print(f"    statistic: {r['w_stat']:.1f}   p-value: {r['p_score']:.4f}  "
              f"({sig} at α={alpha}; lower error: {r['score_better']})")
    else:
        print("    Wilcoxon not computable (all paired differences are zero)")
    print()


def main() -> None:
    dataset = load_df(DATASET)
    sizes = dataset.set_index("id")["size"]

    data = {p: load_df(RESULTS_DIR / f"{p}.json") for p in PROVIDERS}
    aggs = {p: aggregate(data[p]) for p in PROVIDERS}

    summary = build_summary(aggs, dataset)
    out = RESULTS_DIR / "summary.csv"
    summary.to_csv(out, index=False)
    print(f"wrote {out.relative_to(RESULTS_DIR.parent)}\n")

    for p in PROVIDERS:
        report(p, data[p], aggs[p], sizes)

    paired_tests(aggs)


if __name__ == "__main__":
    main()
