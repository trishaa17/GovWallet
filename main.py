from flask import Flask, jsonify
from dash import Dash, dcc, html, Input, Output, callback_context
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
from navigation_menu import create_vertical_icon_sidebar, get_nav_css, register_navigation_callbacks
from dash.dependencies import Input, Output, State

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

def integrate_navigation_into_app(app, app_name):
    """Helper function to integrate navigation into any Dash app"""
    # Set up the index string with navigation CSS
    index_string = f'''
    <!DOCTYPE html>
    <html>
        <head>
            {{%metas%}}
            <title>{{%title%}}</title>
            {{%favicon%}}
            {{%css%}}
            <style>
            {get_nav_css()}
            </style>
        </head>
        <body>
            {{%app_entry%}}
            <footer>
                {{%config%}}
                {{%scripts%}}
                {{%renderer%}}
            </footer>
        </body>
    </html>
    '''
    app.index_string = index_string
    
    # Store the original layout
    original_layout = app.layout
    
    # Create new layout with navigation
    app.layout = html.Div([
        # Add the navigation sidebar
        create_vertical_icon_sidebar(),
        # Main content area with proper margin class
        html.Div(
            original_layout if callable(original_layout) else original_layout,
            className='main-content',  # This class adds the left margin for the sidebar
            style={'padding': '20px'}  # Add some padding for better spacing
        )
    ])
    
    # Register navigation callbacks
    register_navigation_callbacks(app)
    
    return app

# Create individual dashboard apps with integrated navigation
appNumberOfRoles = integrate_navigation_into_app(
    create_dash_number_of_roles(server), 
    "Manpower Count"
)

appMaxAmount = integrate_navigation_into_app(
    create_dash_individual_amount(server), 
    "Individual Amount"
)

appTotalAmount = integrate_navigation_into_app(
    create_dash_total_amount(server), 
    "Total Amount"
)

appDisbursementTrend = integrate_navigation_into_app(
    create_dash_disbursement_trend(server), 
    "Disbursement Trend"
)

appRejectionRate = integrate_navigation_into_app(
    create_dash_rejection_rate(server), 
    "Rejection Rate"
)

appLocationHeatmap = integrate_navigation_into_app(
    create_dash_heatmap(server), 
    "Location Heatmap"
)

appCampaignClashes = integrate_navigation_into_app(
    create_dash_campaign_clashes(server), 
    "Campaign Clashes"
)

appShiftClashes = integrate_navigation_into_app(
    create_dash_shift_clashes(server), 
    "Shift Clashes"
)

appShiftClashesVenue = integrate_navigation_into_app(
    create_dash_shift_clashes_venue(server),
    "Shift Clashes (VM)"
)

appCampaignClashesVenue = integrate_navigation_into_app(
    create_dash_campaign_clashes_venue(server),
    "Campaign Clashes (VM)"
)



# Main app with navigation (app3) - unchanged
app3 = Dash(__name__, server=server, url_base_pathname='/app3/', external_stylesheets=[dbc.themes.BOOTSTRAP])
app3.title = "Volunteer Dashboard"

# CRITICAL: Set up the index string with navigation CSS
index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
        {get_nav_css()}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
'''
app3.index_string = index_string

# Set up layout with navigation sidebar
app3.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # Add the navigation sidebar
    create_vertical_icon_sidebar(),
    # Main content area with proper margin class
    html.Div(
        id='page-content',
        className='main-content',  # This class adds the left margin for the sidebar
        children=[]
    )
])

# Register navigation callbacks
register_navigation_callbacks(app3)

# Register existing callbacks
register_callbacks(app3)
register_person_callbacks(app3)

@app3.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/app3/' or pathname == '/app3':
        # Default volunteer dashboard page
        return layout_avg()
    elif pathname.startswith('/app3/person/'):
        name = pathname.split('/')[-1]
        return layout_person(name)
    elif pathname == '/':
        # Redirect to home when at root of app3
        return html.Script("window.location.href = '/';")
    else:
        # Default to average layout
        return layout_avg()

@server.route('/')
def index():
    return f'''
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body {{
                    background: url("https://images.unsplash.com/photo-1454117096348-e4abbeba002c?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
                    background-size: cover;
                    background-repeat: no-repeat;
                    background-position: center center;
                    background-attachment: fixed;
                    color: black;
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                }}
                .container {{
                    text-align: center;
                    padding-top: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .logo {{
                    margin-bottom: 30px;
                    opacity: 0;
                    animation: fadeIn 1s ease-in forwards;
                }}
                .typewriter {{
                    font-size: 48px;
                    font-weight: bold;
                    margin: 30px 0;
                    color: #2c3e50;
                }}
                .typewriter-text {{
                    border-right: 3px solid #2c3e50;
                    padding-right: 5px;
                    animation: blink 1s infinite;
                }}
                .dashboard-section {{
                    margin: 40px 0;
                    opacity: 0;
                    animation: slideUp 1s ease-out 2s forwards;
                }}
                select {{
                    padding: 15px;
                    font-size: 16px;
                    width: 500px;
                    max-width: 90%;
                    border: 2px solid #34495e;
                    border-radius: 8px;
                    background-color: rgba(255,255,255,0.95);
                    color: black;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                select:hover {{
                    border-color: #3498db;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
                a.button {{
                    display: inline-block;
                    padding: 15px 30px;
                    background-color: white;
                    color: black;
                    text-decoration: none;
                    border-radius: 8px;
                    font-family: 'Poppins', sans-serif;
                    font-size: 16px;
                    transition: all 0.3s ease;
                    margin-top: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    border: 2px solid black;
                }}
                a.button:hover {{
                    background-color: black;
                    transform: translateY(-2px);
                    box-shadow: 0 6px 12px rgba(0,0,0,0.2);
                }}
                .subtitle {{
                    font-size: 18px;
                    color: #34495e;
                    margin-bottom: 30px;
                    opacity: 0;
                    animation: fadeIn 1s ease-in 1.5s forwards;
                }}
            .search-wrapper {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px; /* space between dropdown and button */
                margin-top: 20px;
                margin-bottom: 100px; /* Add space below to encourage dropdown to open downward */
            }}

            .search-wrapper select {{
                padding: 15px;
                font-size: 16px;
                border-radius: 30px;
                border: none;
                width: 500px;
                max-width: 90%;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                font-family: 'Poppins', sans-serif;
            }}

            .circular-icon {{
                width: 48px;
                height: 48px;
                border-radius: 50%;
                border: none;
                background-color: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.15);
                padding: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
            }}

            .circular-icon:hover {{
                transform: scale(1.05);
                box-shadow: 0 6px 12px rgba(0,0,0,0.2);
            }}

            .circular-icon img {{
                width: 75%;
                height: 75%;
                object-fit: contain;
            }}
                @keyframes fadeIn {{
                    from {{ opacity: 0; }}
                    to {{ opacity: 1; }}
                }}
                @keyframes slideUp {{
                    from {{ 
                        opacity: 0; 
                        transform: translateY(30px); 
                    }}
                    to {{ 
                        opacity: 1; 
                        transform: translateY(0); 
                    }}
                }}
                @keyframes blink {{
                    0%, 50% {{ border-color: #2c3e50; }}
                    51%, 100% {{ border-color: transparent; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <img src="https://resources.fina.org/photo-resources/2024/07/12/e3c65862-2e4a-469a-a358-e6a23545bfa9/7fafa8e5-db48-4647-bfca-3fbf5ccfa45b?height=240" alt="World Aquatics Logo">
                </div>
                
                <h1 style="text-align: center; font-family: 'Poppins', sans-serif; font-size: 40px;">
                    <span id="typewriter" class="typewriter-text"></span>
                </h1>
                <div class="search-wrapper">
                    <select onchange="if(this.value) window.location.href=this.value">
                        <option value="">Select a Dashboard</option>
                        <option value="/appNumberOfRoles/">📊 Manpower Count Dashboard</option>
                        <option value="/appMaxAmount/">💰 Individual Disbursement Dashboard</option>
                        <option value="/appTotalAmount/">📈 Total Disbursement Dashboard</option>
                        <option value="/appDisbursementTrend/">📉 Disbursement Trend</option>
                        <option value="/appRejectionRate/">❌ Rejection Rate</option>
                        <option value="/appLocationHeatmap/">🗺️ Location Heatmap</option>
                        <option value="/appCampaignClashes/">⚠️ Campaign Clashes</option>
                        <option value="/appCampaignClashesVenue/"> Campaign Clashes Venue</option>
                        <option value="/appShiftClashes/">🕐 Shift Clashes</option>
                        <option value="/appShiftClashesVenue/"> Shift Clashes Venue</option>
                    </select>
                    <button class="circular-icon" onclick="window.location.href='/app3/'"> 
                        <img src="https://static-00.iconduck.com/assets.00/profile-icon-512x512-w0uaq4yr.png" alt="Profile"> 
                    </button>
                </div>
            </div>
            <script>
                const line1 = "World Aquatics Dashboard";
                const line2 = "Select a report to get started.";
                const el = document.getElementById("typewriter");
                let i = 0;
                function typeLine1() {{
                    if (i < line1.length) {{
                        el.textContent += line1.charAt(i);
                        i++;
                        setTimeout(typeLine1, 100);
                    }} 
                    else {{
                        setTimeout(() => {{
                            eraseLine(typeLine2);
                        }}, 1000);
                    }}   
                }}

                function eraseLine(callback) {{
                    const current = el.textContent;
                    if (current.length > 0) {{
                        el.textContent = current.slice(0, -1);
                        setTimeout(() => eraseLine(callback), 50);
                    }} else {{
                        callback();
                    }}
                }}

                function typeLine2() {{
                    let j = 0;
                    function type() {{
                        if (j < line2.length) {{
                            el.textContent += line2.charAt(j);
                            j++;
                            setTimeout(type, 100);
                        }}
                    }}
                    type();
                }}

                setTimeout(typeLine1, 500);
            </script>
        </body>
        </html>'''

@server.route('/refresh-cache')
def refresh_cache():
    try:
        loadcsv.force_refresh()
        return jsonify({"status": "success", "message": "Cache refreshed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    server.run(debug=True)