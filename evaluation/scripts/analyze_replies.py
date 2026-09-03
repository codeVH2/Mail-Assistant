"""Study 2: do human raters prefer the local model's replies or the cloud model's?

36 respondents each judged the same 6 blind AI-vs-AI pairs, plus an attention check.
Run from anywhere; add `> ../results/reply_stats.txt` to keep the report.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

RESULTS = Path(__file__).resolve().parents[1] / "results"
CSV = RESULTS / "Answers - Respostas ao formulário 1.csv"
SUMMARY = RESULTS / "reply_summary.csv"

# Transcribed from key_google_forms.txt: which provider was shown as option A.
# Positions were alternated so that a rater who always picks the first option
# splits evenly between providers instead of favouring one.
PROVIDER_A = {1: "local", 2: "local", 3: "cloud", 5: "local", 6: "cloud", 7: "cloud"}

# Scenario 4 shows two hand-written replies where only B answers the email at all,
# so it measures whether the rater was reading, not which provider is better.
ATTENTION, ATTENTION_OK = 4, "B"

# The key file does not record which email each scenario used; inferred from the
# form's order (the 6 emails in sequence, attention check inserted fourth).
EMAIL = {1: "reply_1", 2: "reply_2", 3: "reply_3", 5: "reply_4", 6: "reply_5", 7: "reply_6"}

ALPHA = 0.05


def load() -> pd.DataFrame:
    """Answers as "A"/"B", one row per respondent, columns numbered by scenario.

    Columns are taken by position: every question carries the same header text
    ("Which reply would you send?"), so names cannot identify a scenario.
    """
    raw = pd.read_csv(CSV).dropna(how="all")
    answers = raw.iloc[:, 1:8].apply(lambda col: col.str.strip().str[-1])
    answers.columns = range(1, 8)
    return answers.reset_index(drop=True)


def to_long(answers: pd.DataFrame) -> pd.DataFrame:
    """One row per (respondent, pair). Decodes A/B into a provider exactly once."""
    rows = [
        {
            "respondent": respondent,
            "scenario": scenario,
            "email": EMAIL[scenario],
            "position": choice,
            "chosen": provider_a if choice == "A" else ("cloud" if provider_a == "local" else "local"),
        }
        for scenario, provider_a in PROVIDER_A.items()
        for respondent, choice in answers[scenario].items()
    ]
    return pd.DataFrame(rows)


def binom(k: int, n: int) -> tuple:
    """Two-sided binomial test against chance, with a 95% interval."""
    result = stats.binomtest(k, n, 0.5)
    low, high = result.proportion_ci()
    return k, n, k / n, result.pvalue, low, high


def show(label: str, k: int, n: int, share: float, p: float, low: float, high: float) -> None:
    verdict = "significant" if p < ALPHA else "not significant"
    print(f"  {label}")
    print(f"    {k}/{n} ({share:.1%})   95% CI [{low:.1%}, {high:.1%}]   p={p:.4f}  ({verdict})")


def local_wins(long: pd.DataFrame) -> tuple:
    return binom(int((long["chosen"] == "local").sum()), len(long))


def sign_test(long: pd.DataFrame) -> tuple:
    """One independent unit per rater: does their majority lean local or cloud?

    Ties (3-3) carry no direction and are dropped, which is what makes it a sign test.
    """
    per = long.assign(hit=long["chosen"] == "local").groupby("respondent")["hit"].agg(["sum", "count"])
    leans_local = int((per["sum"] * 2 > per["count"]).sum())
    leans_cloud = int((per["sum"] * 2 < per["count"]).sum())
    return binom(leans_local, leans_local + leans_cloud), len(per) - leans_local - leans_cloud


def main() -> None:
    collected = load()
    passed = collected[ATTENTION] == ATTENTION_OK

    print("=== ATTENTION CHECK ===")
    print(f"  scenario {ATTENTION}: two hand-written replies, only option {ATTENTION_OK} "
          "answers the email")
    print(f"  collected: {len(collected)}   failed: {int((~passed).sum())}   "
          f"analysed: {int(passed.sum())} ({passed.mean():.1%})")
    if not passed.all():
        print(f"  excluded rows (0-indexed): {list(collected.index[~passed])}")
    print()

    # Failing the check means the rater was not reading the replies, so their
    # preferences carry no information about reply quality. The check was built
    # into the form before collection, so this exclusion is planned, not a
    # criterion chosen after seeing the results.
    answers = collected[passed]
    long = to_long(answers)

    print(f"=== INPUT ===\n  {len(answers)} respondents x {len(PROVIDER_A)} pairs = {len(long)} judgments")
    print(f"  scenario -> email:       {EMAIL}")
    print(f"  provider in position A:  {PROVIDER_A}\n")

    print("=== PREFERENCE FOR LOCAL ===")
    show(f"all judgments, treated as independent (n={len(long)}):", *local_wins(long))
    signs, tied = sign_test(long)
    show(f"per respondent, sign test ({tied} ties dropped):", *signs)
    print()

    print("=== POSITION BIAS ===")
    show("option A chosen, regardless of provider:", *binom(int((long["position"] == "A").sum()), len(long)))
    print("    (each provider held position A in 3 of the 6 pairs, so a preference")
    print("     here would be a confound rather than a provider effect)\n")

    table = (
        long.assign(hit=long["chosen"] == "local")
        .groupby(["scenario", "email"], as_index=False)
        .agg(votes=("hit", "size"), local=("hit", "sum"))
    )
    table["cloud"] = table["votes"] - table["local"]
    table["provider_a"] = table["scenario"].map(PROVIDER_A)
    table["local_share"] = (table["local"] / table["votes"]).round(3)
    print("=== PER SCENARIO ===")
    print("  " + table.to_string(index=False).replace("\n", "\n  ") + "\n")

    *_, p, _, _ = local_wins(long)
    print("=== CONCLUSION ===")
    if p < ALPHA:
        favoured = "local" if local_wins(long)[2] > 0.5 else "cloud"
        print(f"  Raters preferred the {favoured} model's replies (p={p:.4f}, n={len(long)}).")
    else:
        print(f"  No statistically significant preference was detected (p={p:.4f}, n={len(long)}).")
        print("  That is an absence of evidence for a difference, not evidence that the two")
        print("  are equivalent: this study is not powered to establish equivalence.")

    table.to_csv(SUMMARY, index=False)
    print(f"\nwrote {SUMMARY.name}")


if __name__ == "__main__":
    main()