import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    df = pd.read_csv(r"C:\Users\User\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD - Technology & Innovation\Ewallet\govwallet_data.csv")

    # Count unique gms_id per payout_date and gms_role
    summary = df.groupby(['payout_date', 'gms_role_name'])['gms_id'].nunique().reset_index()
    summary.rename(columns={'gms_id': 'unique_accounts'}, inplace=True)

    # Bar chart
    plt.figure(figsize=(12, 6))
    sns.barplot(data=summary, x='payout_date', y='unique_accounts', hue='gms_role_name')
    plt.title('Number of Unique Accounts per Role and Payout Date')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # Pie charts (one per payout_date)
    for date in summary['payout_date'].unique():
        sub_df = summary[summary['payout_date'] == date]
        plt.figure()
        plt.pie(sub_df['unique_accounts'], labels=sub_df['gms_role_name'], autopct='%1.1f%%')
        plt.title(f'Role Distribution on {date}')
        plt.show()

if __name__ == '__main__':
    main()
