# import pandas as pd

# df = pd.read_csv("commodities/Maharashtra_Wheat_2021_2026_Master_Dataset.csv")

# df["Date"] = pd.to_datetime(df["Date"])
# df = df.sort_values("Date").reset_index(drop=True)

# price_col = "Weighted_Modal_Price"

# # -------------------------------
# # Missing Gap Analysis
# # -------------------------------

# missing = df[price_col].isna()

# gaps = []
# start = None

# for i, m in enumerate(missing):
#     if m and start is None:
#         start = i
#     elif not m and start is not None:
#         gaps.append((start, i - 1))
#         start = None

# if start is not None:
#     gaps.append((start, len(df) - 1))

# print("=" * 60)
# print(f"Total Missing Values : {missing.sum()}")
# print(f"Total Missing Gaps   : {len(gaps)}")
# print("=" * 60)

# for s, e in gaps:
#     print(
#         f"{df.loc[s,'Date'].date()} --> {df.loc[e,'Date'].date()} "
#         f"| Length = {e-s+1}"
#     )







import pandas as pd

df = pd.read_csv("commodities/Maharashtra_Wheat_2021_2026_Master_Dataset.csv")

df["Date"] = pd.to_datetime(df["Date"])

df = df.sort_values("Date")

df = df.set_index("Date")

col = "Weighted_Modal_Price"

# Small gaps
df[col] = df[col].interpolate(
    method="time",
    limit=3,
    limit_direction="both"
)

# Medium gaps
df[col] = df[col].interpolate(
    method="cubicspline",
    limit=7,
    limit_direction="both"
)

# Longer gaps
df[col] = df[col].interpolate(
    method="pchip",
    limit_direction="both"
)

df[col] = df[col].ffill().bfill()

df.reset_index(inplace=True)

df.to_csv(
    "commodities/Maharashtra_Wheat_2021_2026_Filled.csv",
    index=False
)

print("Completed")