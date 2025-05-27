# import pandas as pd
# import plotly.express as px
# from dash import Dash, dcc, html

# # Load data
# df = pd.read_csv(r"C:\Users\User\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD - Technology & Innovation\Ewallet\govwallet_data.csv")

# # Group data: unique accounts per payout_date and role
# summary = df.groupby(['payout_date', 'gms_role_name'])['gms_id'].nunique().reset_index()
# summary.rename(columns={'gms_id': 'unique_accounts'}, inplace=True)

# # Calculate total unique accounts per role across all dates
# total_per_role = df.groupby('gms_role_name')['gms_id'].nunique().reset_index()
# total_per_role.rename(columns={'gms_id': 'total_unique_accounts'}, inplace=True)

# # Initialize Dash app
# app = Dash(__name__)
# app.title = "GovWallet Disbursement Dashboard"

# # Layout
# app.layout = html.Div([
#     html.H1("GovWallet Disbursement Summary", style={'textAlign': 'center'}),

#     html.H2("Bar Chart: Unique Accounts per Role and Payout Date"),
#     dcc.Graph(
#         figure=px.bar(
#             summary,
#             x='payout_date',
#             y='unique_accounts',
#             color='gms_role_name',
#             barmode='group',
#             title="Unique Accounts by Role & Date"
#         )
#     ),

#     html.H2("Total Unique Accounts per Role (All Dates)"),
#     html.Ul([
#         html.Li(f"{row['gms_role_name']}: {row['total_unique_accounts']} unique accounts")
#         for _, row in total_per_role.iterrows()
#     ])
# ])

# if __name__ == '__main__':
#     app.run(debug=True)
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
import requests
from io import StringIO



def create_dash1(server):
    # Load data
    url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EdyAJaCQLpFAp3JTaMCmK_8BkXS81I50q0dg7t5bDrsSEg?download=1"


        # Send HTTP GET request
    response = requests.get(url)
    response.raise_for_status()  # optional, raise error if download fails
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))
  
    # Group data
    summary = df.groupby(['payout_date', 'gms_role_name'])['gms_id'].nunique().reset_index()
    summary.rename(columns={'gms_id': 'unique_accounts'}, inplace=True)

    total_per_role = df.groupby('gms_role_name')['gms_id'].nunique().reset_index()
    total_per_role.rename(columns={'gms_id': 'total_unique_accounts'}, inplace=True)

    # Create Dash app with route
    app = Dash(__name__, server=server, routes_pathname_prefix='/app1/')
    app.title = "GovWallet Disbursement Dashboard"

    # Layout
    app.layout = html.Div([
        html.H1("GovWallet Disbursement Summary", style={'textAlign': 'center'}),

        html.H2("Bar Chart: Unique Accounts per Role and Payout Date"),
        dcc.Graph(
            figure=px.bar(
                summary,
                x='payout_date',
                y='unique_accounts',
                color='gms_role_name',
                barmode='group',
                title="Unique Accounts by Role & Date"
            )
        ),

        html.H2("Total Unique Accounts per Role (All Dates)"),
        html.Ul([
            html.Li(f"{row['gms_role_name']}: {row['total_unique_accounts']} unique accounts")
            for _, row in total_per_role.iterrows()
        ])
    ])

    return app
