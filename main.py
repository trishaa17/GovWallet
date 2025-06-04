from flask import Flask
from importlib.machinery import SourceFileLoader
from dashManpowerCount import create_dash_number_of_roles
from dashIndivAmount import create_dash_individual_amount
from dashTotalAmount import create_dash_total_amount
from dashDisbursementTrend import create_dash_disbursement_trend
from dashRejected import create_dash_rejection_rate
from dashLocationHeatmap import create_dash_heatmap
from dashCampaignClashes import create_dash_campaign_clashes
from dashShiftClashes import create_dash_shift_clashes
import loadcsv

server = Flask(__name__)

def auto_refresh_cache():
    while True:
        time.sleep(600)  # 10 minutes
        try:
            csv_cache.force_refresh()
            print("CSV cache auto-refreshed")
        except Exception as e:
            print("Failed to auto-refresh CSV cache:", e)

# Start background thread to refresh cache
threading.Thread(target=auto_refresh_cache, daemon=True).start()


appNumberOfRoles = create_dash_number_of_roles(server)
appMaxAmount = create_dash_individual_amount(server)
appTotalAmount = create_dash_total_amount(server)
appDisbursementTrend = create_dash_disbursement_trend(server)
appRejectionRate = create_dash_rejection_rate(server)
appLocationHeatmap = create_dash_heatmap(server)
appCampaignClashes = create_dash_campaign_clashes(server)
appShiftClashes = create_dash_shift_clashes(server)

@server.route('/')
def index():
    return '''
        <h1>Welcome</h1>
        <p><a href="/appNumberOfRoles/">Manpower Count Dashboard</a></p>
        <p><a href="/appMaxAmount/">Individual Disbursement Dashboard</a></p>
        <p><a href="/appTotalAmount/">Total Disbursement Dashboard (by role/campaign)</a></p>
        <p><a href="/appDisbursementTrend/">Overall Disbursement Trend (day/week/month)</a></p>
        <p><a href="/appRejectionRate/">Rejection rate (by role/campaign/date)</a></p>
        <p><a href="/appLocationHeatmap/">Location Disbursement Heatmap</a></p>
        <p><a href="/appCampaignClashes/">Identify Campaign Clashes</a></p>
        <p><a href="/appShiftClashes/">Identify Shift Timing Clashes</a></p>
       
       
    '''

if __name__ == '__main__':
    server.run(debug=True)
