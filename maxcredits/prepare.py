# prepare_data.py
import pandas as pd
import sqlite3

# Replace with your actual file path
df = pd.read_csv(r"C:\Users\User\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD - Technology & Innovation\Ewallet\govwallet_data.csv")

df['payout_date'] = pd.to_datetime(df['payout_date']).dt.date

# Compute max amount per volunteer per date
agg_df = df.groupby(['name', 'payout_date'], as_index=False)['amount'].max()

# Save to SQLite
conn = sqlite3.connect('wallet_data.db')
agg_df.to_sql('wallet_data', conn, if_exists='replace', index=False)
conn.close()

print("Database created successfully.")
