from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # no GUI; just write files

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyze import (
    DATASET,
    GOLD_CATEGORIES,
    PROVIDERS,
    RESULTS_DIR,
    aggregate,
    compute_paired_tests,
    load_df,
)

COLORS = {"local": "#4C72B0", "cloud": "#DD8452"}


def fig_comparison(aggs: dict[str, pd.DataFrame]) -> None:
    labels = ["Accuracy\n(category)", "Stability\n(3/3 runs)"]
    metric_vals = {
        p: [aggs[p]["correct"].mean(), aggs[p]["stable"].mean()] for p in PROVIDERS
    }
    mae = {p: aggs[p]["score_err"].mean() for p in PROVIDERS}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    x = np.arange(len(labels))
    w = 0.35
    for i, p in enumerate(PROVIDERS):
        bars = ax1.bar(x + (i - 0.5) * w, metric_vals[p], w, label=p, color=COLORS[p])
        for b, v in zip(bars, metric_vals[p]):
            ax1.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.0%}", ha="center", va="bottom", fontsize=9)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylim(0, 1.12)
    ax1.set_ylabel("proportion")
    ax1.set_title("Category: accuracy and stability")
    ax1.legend()

    bars = ax2.bar(PROVIDERS, [mae[p] for p in PROVIDERS], width=0.5, color=[COLORS[p] for p in PROVIDERS])
    for b, p in zip(bars, PROVIDERS):
        ax2.text(b.get_x() + b.get_width() / 2, mae[p] + 0.002, f"{mae[p]:.3f}", ha="center", va="bottom", fontsize=9)
    ax2.set_ylabel("MAE (lower = better)")
    ax2.set_title("Relevance score: mean error")
    ax2.set_ylim(0, max(mae.values()) * 1.35)

    n = len(aggs[PROVIDERS[0]])
    fig.suptitle(f"Local vs Cloud — prioritisation (n={n} emails, 3 runs)", fontweight="bold")
    fig.tight_layout()
    out = RESULTS_DIR / "fig_comparison.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)


def fig_confusion(aggs: dict[str, pd.DataFrame]) -> None:
    # Gold has only 3 categories, but the prompt offers 5 — the model can
    # predict newsletter/promotional. Keep those as extra columns (informative
    # errors) instead of dropping them, and share the column axis across both
    # panels so the matrices are directly comparable.
    rows = GOLD_CATEGORIES
    extra = sorted(
        c
        for p in PROVIDERS
        for c in aggs[p]["pred_category"].dropna().unique()
        if c not in GOLD_CATEGORIES
    )
    cols = GOLD_CATEGORIES + extra

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for ax, p in zip(axes, PROVIDERS):
        cm = pd.crosstab(aggs[p]["category_gold"], aggs[p]["pred_category"])
        cm = cm.reindex(index=rows, columns=cols, fill_value=0)
        ax.imshow(cm.values, cmap="Blues", vmin=0)
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels(cols, rotation=45, ha="right")
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels(rows)
        ax.set_xlabel("predicted")
        ax.set_ylabel("actual (gold)")
        ax.set_title(p)
        peak = cm.values.max() or 1
        for i in range(len(rows)):
            for j in range(len(cols)):
                v = cm.values[i, j]
                ax.text(j, i, str(v), ha="center", va="center",
                        color="white" if v > peak / 2 else "black", fontsize=12)
    fig.suptitle("Confusion matrix — diagonal = correct", fontweight="bold")
    fig.tight_layout()
    out = RESULTS_DIR / "fig_confusion.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)


def fig_significance(aggs: dict[str, pd.DataFrame]) -> None:
    """Render the paired significance tests (McNemar on category, Wilcoxon on
    score error) as two annotated bar panels."""
    r = compute_paired_tests(aggs)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # --- McNemar: the discordant pairs are what the test actually weighs. ---
    disc_labels = ["cloud right\nlocal wrong (b)", "local right\ncloud wrong (c)"]
    disc_vals = [r["b"], r["c"]]
    bars = ax1.bar(disc_labels, disc_vals, width=0.6, color=[COLORS["cloud"], COLORS["local"]])
    for b, v in zip(bars, disc_vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.05, str(v), ha="center", va="bottom", fontsize=11)
    ax1.set_ylabel("discordant emails")
    ax1.set_ylim(0, max(disc_vals + [1]) * 1.25)
    if r["p_cat"] is not None:
        sig = "significant" if r["p_cat"] < r["alpha"] else "n.s."
        sub = f"p = {r['p_cat']:.4f} ({sig}, α={r['alpha']}) — favours {r['cat_better']}"
    else:
        sub = "no discordant pairs — providers identical"
    ax1.set_title(f"McNemar exact — category\n{sub}", fontsize=10)

    # --- Wilcoxon: paired mean absolute score error (lower = better). ---
    mae_vals = [r["local_mae"], r["cloud_mae"]]
    bars = ax2.bar(PROVIDERS, mae_vals, width=0.5, color=[COLORS[p] for p in PROVIDERS])
    for b, v in zip(bars, mae_vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.002, f"{v:.3f}", ha="center", va="bottom", fontsize=11)
    ax2.set_ylabel("mean |pred − gold| (lower = better)")
    ax2.set_ylim(0, max(mae_vals) * 1.35)
    if r["p_score"] is not None:
        sig = "significant" if r["p_score"] < r["alpha"] else "n.s."
        sub = f"W = {r['w_stat']:.1f}, p = {r['p_score']:.4f} ({sig}, α={r['alpha']}) — lower: {r['score_better']}"
    else:
        sub = "all paired differences zero — not computable"
    ax2.set_title(f"Wilcoxon signed-rank — score\n{sub}", fontsize=10)

    fig.suptitle(f"Paired significance: cloud vs local (n={r['n_emails']} emails)", fontweight="bold")
    fig.tight_layout()
    out = RESULTS_DIR / "fig_significance.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main() -> None:
    aggs = {p: aggregate(load_df(RESULTS_DIR / f"{p}.json")) for p in PROVIDERS}
    fig_comparison(aggs)
    fig_confusion(aggs)
    fig_significance(aggs)
    print("wrote fig_comparison.png, fig_confusion.png and fig_significance.png to results/")


if __name__ == "__main__":
    main()
