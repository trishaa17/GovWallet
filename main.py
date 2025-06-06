from flask import Flask, jsonify
from dash import Dash, dcc, html, Input, Output
from importlib.machinery import SourceFileLoader
from dashManpowerCount import create_dash_number_of_roles
from dashIndivAmount import create_dash_individual_amount
from dashTotalAmount import create_dash_total_amount
from dashDisbursementTrend import create_dash_disbursement_trend
from dashRejected import create_dash_rejection_rate
from dashLocationHeatmap import create_dash_heatmap
from dashCampaignClashes import create_dash_campaign_clashes
from dashCampaignClashesVenue import create_dash_campaign_clashes_venue
from dashShiftClashes import create_dash_shift_clashes
from dashShiftClashesVenue import create_dash_shift_clashes_venue
from dashPeople import layout_avg, layout_person
from callbacks_people import register_callbacks, register_person_callbacks
import dash_bootstrap_components as dbc
from urllib.parse import unquote
import loadcsv
import threading
import time


server = Flask(__name__)

def auto_refresh_cache():
    while True:
        time.sleep(300)  # 5 minutes
        try:
            loadcsv.force_refresh()
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
appCampaignClashesVenue = create_dash_campaign_clashes_venue(server)
appShiftClashes = create_dash_shift_clashes(server)
appShiftClashesVenue = create_dash_shift_clashes_venue(server)
app3 = Dash(__name__, server=server, url_base_pathname='/app3/', external_stylesheets=[dbc.themes.BOOTSTRAP])
app3.title = "Volunteer"
app3.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])
register_callbacks(app3)
register_person_callbacks(app3)
@app3.callback(Output('page-content', 'children'), Input('url', 'pathname'))

def display_page(pathname):
    if pathname.startswith('/app3/person/'):
        name = pathname.split('/')[-1]
        return layout_person(name)
    return layout_avg()

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
        <p><a href="/appCampaignClashes/">Identify Campaign Clashes (Finance Manager Version)</a></p>
        <p><a href="/appCampaignClashesVenue/">Identify Campaign Clashes (Venue Manager Version)</a></p>
        <p><a href="/appShiftClashes/">Identify Shift Timing Clashes (Finance Manager Version)</a></p>
        <p><a href="/appShiftClashesVenue/">Identify Shift Timing Clashes (Venue Manager Version)</a></p>
        <p><a href="/app3/">Average Shifts</a></p>    
    '''

@server.route('/refresh-cache')
def refresh_cache():
    try:
        loadcsv.force_refresh()
        return jsonify({"status": "success", "message": "Cache refreshed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    server.run(debug=True)
