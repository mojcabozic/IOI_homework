import pandas as pd

df = pd.read_csv("penguins.csv")
df.to_json("penguins.json", orient="records", indent=2)

print("Conversion complete!")