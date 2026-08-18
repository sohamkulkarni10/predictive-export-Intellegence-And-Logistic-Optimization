import pandas as pd

# Read both CSV files
df6 = pd.read_csv("news_ml_dataset6.csv")
df7 = pd.read_csv("news_ml_dataset7.csv")

# Append (row-wise)
combined_df = pd.concat([df6, df7], ignore_index=True)

# Save the combined dataset
combined_df.to_csv("final_news_dataset", index=False)

print("Dataset 6 Shape:", df6.shape)
print("Dataset 7 Shape:", df7.shape)
print("Combined Shape:", combined_df.shape)

print("\nFirst 5 rows:")
print(combined_df.head())