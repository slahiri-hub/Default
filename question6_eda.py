import pandas as pd
import numpy as np

# ── a. Load the dataset ──────────────────────────────────────────────────────
df = pd.read_csv("/root/.claude/uploads/294acc6b-24c6-5ed7-b8a7-e485718ffe0b/d927900b-diabetes.csv")

print("=" * 60)
print("a. pd.read_csv  →  dataset loaded")
print("=" * 60)

# ── b. .head() ───────────────────────────────────────────────────────────────
print("\nb. df.head()  (first 5 rows)")
print("-" * 60)
print(df.head())

# ── c. .shape ────────────────────────────────────────────────────────────────
print("\nc. df.shape")
print("-" * 60)
print(f"  Rows: {df.shape[0]},  Columns: {df.shape[1]}")
print(f"  Column names: {list(df.columns)}")

# ── d. .describe() ───────────────────────────────────────────────────────────
print("\nd. df.describe()  (summary statistics)")
print("-" * 60)
print(df.describe())

# ── e. value_counts() ────────────────────────────────────────────────────────
print("\ne. df['Outcome'].value_counts()")
print("-" * 60)
print(df['Outcome'].value_counts())
print("\n   0 = No Diabetes,  1 = Diabetes")

# ── f. .groupby('Outcome').mean() ────────────────────────────────────────────
print("\nf. df.groupby('Outcome').mean()")
print("-" * 60)
print(df.groupby('Outcome').mean())

# ── g. .drop(columns='Outcome', axis=1) ──────────────────────────────────────
print("\ng. df.drop(columns='Outcome', axis=1)  →  features only")
print("-" * 60)
X = df.drop(columns='Outcome')  # axis=1 is redundant when using columns= in newer pandas
print(X.head())
print(f"  New shape (no Outcome column): {X.shape}")

# ── h. Glucose > 160 ─────────────────────────────────────────────────────────
print("\nh. Samples where Glucose > 160")
print("-" * 60)
high_glucose = df[df['Glucose'] > 160]
print(high_glucose)
print(f"\n  Total samples with Glucose > 160: {len(high_glucose)}")
