import pandas as pd
import numpy as np

df = pd.read_csv("Commodity_Prices_Pivot_All_Commodities.csv")

df["Date"] = pd.to_datetime(df["Date"])

commodities = df.columns[1:]

print("="*100)

for col in commodities:

    s = df[col]

    missing = s.isna()

    total_missing = missing.sum()

    percent = total_missing/len(df)*100

    gaps = []

    start = None

    for i in range(len(s)):

        if missing.iloc[i] and start is None:
            start = i

        elif not missing.iloc[i] and start is not None:

            gaps.append(i-start)

            start=None

    if start is not None:
        gaps.append(len(s)-start)

    if len(gaps)==0:

        max_gap=0
        avg_gap=0

    else:

        max_gap=max(gaps)
        avg_gap=np.mean(gaps)

    print(f"""
Commodity : {col}

Total Missing : {total_missing}

Missing % : {percent:.2f}

Missing Blocks : {len(gaps)}

Largest Gap : {max_gap}

Average Gap : {avg_gap:.2f}

{'-'*70}
""")
    




import pandas as pd

# Load dataset
df = pd.read_csv("Commodity_Prices_Pivot_All_Commodities.csv")

df["Date"] = pd.to_datetime(df["Date"])

commodities = df.columns[1:]

LONG_GAP = 15

print("=" * 120)
print(f"LONG MISSING GAPS (>= {LONG_GAP} DAYS)")
print("=" * 120)

for commodity in commodities:

    missing = df[commodity].isna()

    gaps = []

    start = None

    for i in range(len(df)):

        if missing.iloc[i] and start is None:
            start = i

        elif not missing.iloc[i] and start is not None:

            end = i - 1
            length = end - start + 1

            if length >= LONG_GAP:
                gaps.append({
                    "Start Date": df.loc[start, "Date"].date(),
                    "End Date": df.loc[end, "Date"].date(),
                    "Length": length
                })

            start = None

    # Handle gap till last row
    if start is not None:

        end = len(df) - 1
        length = end - start + 1

        if length >= LONG_GAP:
            gaps.append({
                "Start Date": df.loc[start, "Date"].date(),
                "End Date": df.loc[end, "Date"].date(),
                "Length": length
            })

    print("\n" + "=" * 80)
    print(f"{commodity}")
    print("=" * 80)

    if len(gaps) == 0:
        print("No gaps >= 15 days")

    else:
        for g in gaps:
            print(
                f"{g['Start Date']}  -->  {g['End Date']}    "
                f"({g['Length']} days)"
            )

print("\nAnalysis Complete.")