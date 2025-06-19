from dash_iconify import DashIconify
from dash import dcc, html, Input, Output, callback, State, callback_context, clientside_callback
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import dash

def create_vertical_icon_sidebar():
    return html.Div(
        id="vertical-sidebar",
        children=[
             html.Div([
                html.Img(
                    src="https://resources.fina.org/photo-resources/2024/07/12/e3c65862-2e4a-469a-a358-e6a23545bfa9/7fafa8e5-db48-4647-bfca-3fbf5ccfa45b?height=240",
                    id="sidebar-logo",
                    className="nav-logo"
                ),  html.Div(className="logo-divider")], className="nav-logo-section"),
            # Navigation Icons
            html.Div([
                html.Div([
                    html.Div("MENU", style={
                        "fontSize": "11px",
                        "letterSpacing": "1px",
                        "color": "#9CA3AF",
                        "marginLeft": "18px",
                        "marginBottom": "8px",
                        "fontWeight": "600",
                        "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
                       },className= "menu-label"),
                ]),
                # Home/Dashboard
                html.Div([
                    html.Div([
                    html.Img(
                        src="https://cdn-icons-png.flaticon.com/512/1946/1946488.png",  # home icon
                        style={"width": "17.5px", "height": "17.5px"},
                        className="nav-icon"
                    ),
                        html.Span("Home", className="nav-label")
                    ], className="nav-icon-content")
                ], 
                id="nav-home",
                className="nav-icon-item active",
                **{"data-page": "dashboard"}
                ),
                
                # Dashboard with Dropdown
                html.Div([
                    html.Div([
                        html.Div([
                        html.Img(
                            src="https://cdn-icons-png.flaticon.com/128/16105/16105467.png", 
                            style={"width": "17.5px", "height": "17.5px"},
                            className="nav-icon"
                        ),
                            html.Span("Dashboard", className="nav-label"),
                            DashIconify(
                                icon="material-symbols:expand-more",
                                width=16,
                                height=16,
                                className="nav-dropdown-icon",
                                id="dashboard-arrow"
                            )
                        ], className="nav-icon-content")
                    ], 
                    id="nav-dashboard",
                    className="nav-icon-item",
                    **{"data-page": "dashboard"}
                    ),
                    
                    # Dashboard Dropdown Menu (inline, pushes content down)
                    html.Div([
                        html.A("📊 Manpower Count Dashboard", href="/appNumberOfRoles/", className="dropdown-item"),
                        html.A("💰 Individual Disbursement Dashboard", href="/appMaxAmount/", className="dropdown-item"),
                        html.A("📈 Total Disbursement Dashboard", href="/appTotalAmount/", className="dropdown-item"),
                        html.A("📉 Disbursement Trend", href="/appDisbursementTrend/", className="dropdown-item"),
                        html.A("❌ Rejection Rate", href="/appRejectionRate/", className="dropdown-item"),
                        html.A("🗺️ Location Heatmap", href="/appLocationHeatmap/", className="dropdown-item"),
                        html.A("⚠️ Campaign Clashes", href="/appCampaignClashes/", className="dropdown-item"),
                        html.A("📍 Campaign Clashes Venue", href="/appCampaignClashesVenue/", className="dropdown-item"),
                        html.A("🕐 Shift Clashes", href="/appShiftClashes/", className="dropdown-item"),
                        html.A("📅 Shift Clashes Venue", href="/appShiftClashesVenue/", className="dropdown-item"),
                        html.A("🧍‍♂️ Shift Entries", href= "/appEntries/", className="dropdown-item")
                    ], 
                    id="dashboard-dropdown",
                    className="nav-dropdown-inline",
                    style={"display": "none"}
                    )
                ], className="nav-dashboard-container"),
                
                # Volunteer Finder
                html.Div([
                    html.Div([
                        html.Img(
                            src="https://cdn-icons-png.flaticon.com/512/1077/1077063.png",  # home icon
                            style={"width": "17.5px", "height": "17.5px"},
                            className="nav-icon"
                        ),
                        html.Span("Volunteer Finder", className="nav-label")
                    ], className="nav-icon-content")
                ], 
                id="nav-volunteer",
                className="nav-icon-item",
                **{"data-page": "volunteer"}
                ),
                
            ], className="nav-icons-top"),
            
            # Logout Button at Bottom
            html.Div([
                html.Div([
                    html.Div([
                        html.Img(
                            src="https://cdn-icons-png.flaticon.com/128/1286/1286853.png",  # logout icon
                            style={"width": "17.5px", "height": "17.5px"},
                            className="nav-icon"
                        ),
                        html.Span("Logout", className="nav-label")
                    ], className="nav-icon-content")
                ], 
                id="nav-logout",
                className="nav-icon-item logout-item",
                **{"data-page": "logout"}
                ),
            ], className="nav-icons-bottom"),
        ]
    )

# Updated CSS styles with logout button styling
nav_styles = """
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

#vertical-sidebar {
    position: fixed !important;
    top: 0;
    left: 0;
    bottom: 0;
    width: 45px; 
    background: #F8F9FA;
    display: flex;
    flex-direction: column;
    justify-content: start;
    padding: 0px 0;
    z-index: 9999 !important;
    box-shadow: 2px 0 12px rgba(0,0,0,0.08);
    transition: width 0.3s ease;
    overflow: visible;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.menu-label {
    color: #6B7280;
    font-size: 9px;
    letter-spacing: 1.2px;
    margin-left: 18px;
    margin-top: 0px;
    margin-bottom: 8px;
    font-weight: 600;
    opacity: 0;
    transition: opacity 0.3s ease;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    text-transform: uppercase;
}

#vertical-sidebar:hover .menu-label {
    opacity: 1;
}

#vertical-sidebar:hover {
    width: 280px;
}

.nav-icon {
    color: #6B7280;
    transition: color 0.3s ease;
}

.nav-icon-item.active .nav-icon {
    color: #4F46E5;
}

.nav-icon-item {
    display: flex;
    align-items: center;
    width: calc(100% - 10px);
    height: 40px;
    margin: 2px 5px 2px 5px;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    border-radius: 8px;
}

.nav-icon-content {
    display: flex;
    align-items: center;
    padding-left: 9px;
    width: 100%;
}

.nav-label {
    color: #374151;
    font-weight: 500;
    opacity: 0;
    transition: opacity 0.3s ease, color 0.3s ease;
    white-space: nowrap;
    font-size: 11px;
    margin-left: 12px;
    flex-grow: 1;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    letter-spacing: 0.2px;
}

.nav-dropdown-icon {
    color: #6B7280;
    opacity: 1;
    transition: opacity 0.3s ease, transform 0.3s ease;
    margin-right: 15px;
}

.nav-dropdown-icon.open {
    transform: rotate(180deg);
}

#vertical-sidebar:hover .nav-label {
    opacity: 1;
}

#vertical-sidebar:hover .nav-dropdown-icon {
    opacity: 1;
}

.nav-icon-item:hover {
    background-color: rgba(79, 70, 229, 0.08);
}

.nav-icon-item.active .nav-label {
    color: #4F46E5;
    font-weight: 600;
}

.nav-icon-item.active {
    background-color: #EEF2FF;
    border-radius: 8px;
    height: 40px;
}

.nav-icon-item.active::before {
    display: none;
}

.nav-dashboard-container {
    display: flex;
    flex-direction: column;
    width: 100%;
}

.nav-dropdown-inline {
    background: rgba(255, 255, 255, 0.98);
    border-radius: 8px;
    margin: 4px 8px 8px 8px;
    padding: 4px 0;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);
    border: 1px solid #E5E7EB;
    transition: all 0.3s ease;
    overflow: hidden;
    opacity: 1;
    max-height: 0;
}

.nav-dropdown-inline[style*="block"] {
    opacity: 1;
    max-height: 400px;
}

.dropdown-item {
    display: block;
    padding: 8px 16px;
    color: #374151;
    text-decoration: none;
    font-size: 11px;
    transition: background-color 0.2s ease;
    border-bottom: 1px solid #F3F4F6;
    white-space: nowrap;
    opacity: 0;
    transform: translateX(-10px);
    transition: all 0.2s ease;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-weight: 500;
    letter-spacing: 0.1px;
}

#vertical-sidebar:hover .dropdown-item {
    opacity: 1;
    transform: translateX(0);
}

.dropdown-item:last-child {
    border-bottom: none;
}

.dropdown-item:hover {
    background-color: #F3F4F6;
    color: #4F46E5;
    text-decoration: none;
    font-weight: 600;
}

.nav-icons-top {
    display: flex;
    flex-direction: column;
    padding-top: 0px;
    flex-grow: 1;
}

.nav-icons-bottom {
    display: flex;
    flex-direction: column;
    margin-top: auto;
    padding-bottom: 20px;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.nav-icons-bottom {
    display: flex;
    flex-direction: column;
    margin-top: auto;
    padding-bottom: 20px;
    opacity: 1 !important; /* Always show logout section */
    transition: opacity 0.3s ease;
}

/* Make logout label always visible */
.logout-item .nav-label {
    opacity: 0;
    color: #374151;
    font-weight: 500;
    font-size: 11px;
    margin-left: 12px;
    transition: color 0.3s ease;
}

/* Keep the hover effect for logout */
.logout-item:hover .nav-label {
    color: #EF4444 !important;
    font-weight: 600;
}

/* Show logout button only on hover */
#vertical-sidebar:hover .nav-icons-bottom {
    opacity: 1;
}

/* Special styling for logout button */
.logout-item {
    border-top: 1px solid #E5E7EB;
    margin-top: 8px !important;
    padding-top: 8px;
}

.logout-item:hover {
    background-color: rgba(239, 68, 68, 0.08) !important;
}

.logout-item:hover .nav-icon {
    color: #EF4444 !important;
}

.logout-item:hover .nav-label {
    color: #EF4444 !important;
    font-weight: 600;
}

.logo-divider {
    width: 100%;
    height: 1px;
    background-color: #D1D5DB;
    margin-top: 0px;
    transition: opacity 0.3s ease;
    opacity: 1;
}

#vertical-sidebar:hover .logo-divider {
    opacity: 0;
}

/* Main content margin */
.main-content {
    margin-left: 50px;
    transition: margin-left 0.3s ease;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.nav-logo-section {
    padding-top: 0px;
    padding-bottom: 0px;
    margin-top: 0px;
    margin-bottom: 4px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: start;
    min-height: 10px;
}

.nav-logo {
    width: 45px;
    height: 45px;
    object-fit: contain;
    border-radius: 0px;
    background: #F8F9FA;
    padding: 0px;
    transition: all 0.3s ease;
}

.nav-logo:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}

#vertical-sidebar:hover .nav-logo {
    width: 120px;
    height: 120px;
}

/* Additional typography standardization */
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Ensure consistent text rendering */
.nav-label, .menu-label, .dropdown-item {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
}
"""

# Function to register navigation callbacks with the app
def register_navigation_callbacks(app):
    # Clientside callback to detect current page and update navigation state
    app.clientside_callback(
        """
        function() {
            const currentPath = window.location.pathname;
            let activeClasses = ['nav-icon-item', 'nav-icon-item', 'nav-icon-item'];
            
            if (currentPath === '/' || currentPath.includes('dashboard') || 
                currentPath.includes('appNumberOfRoles') || 
                currentPath.includes('appMaxAmount') || 
                currentPath.includes('appTotalAmount') || 
                currentPath.includes('appDisbursementTrend') || 
                currentPath.includes('appRejectionRate') || 
                currentPath.includes('appLocationHeatmap') || 
                currentPath.includes('appCampaignClashes') || 
                currentPath.includes('appShiftClashes')) {
                if (currentPath === '/') {
                    activeClasses[0] = 'nav-icon-item active';
                } else {
                    activeClasses[1] = 'nav-icon-item active';
                }
            } else if (currentPath.includes('app3') || currentPath.includes('volunteer')) {
                activeClasses[2] = 'nav-icon-item active';
            } else {
                activeClasses[0] = 'nav-icon-item active';
            }
            
            return activeClasses;
        }
        """,
        [Output('nav-home', 'className'),
         Output('nav-dashboard', 'className'),
         Output('nav-volunteer', 'className')],
        [Input('nav-home', 'id'),
         Input('nav-dashboard', 'id'),
         Input('nav-volunteer', 'id')]
    )
    
    @app.callback(
        [Output('nav-home', 'className', allow_duplicate=True),
         Output('nav-dashboard', 'className', allow_duplicate=True),
         Output('nav-volunteer', 'className', allow_duplicate=True)],
        [Input('nav-home', 'n_clicks'),
         Input('nav-dashboard', 'n_clicks'),
         Input('nav-volunteer', 'n_clicks')],
        prevent_initial_call=True
    )
    def update_active_nav_on_click(*args):
        ctx = callback_context
        if not ctx.triggered:
            return ['nav-icon-item'] * 3
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        classes = ['nav-icon-item'] * 3
        nav_items = ['nav-home', 'nav-dashboard', 'nav-volunteer']
        
        if button_id in nav_items:
            index = nav_items.index(button_id)
            classes[index] = 'nav-icon-item active'
        
        return classes

    @app.callback(
        [Output('dashboard-dropdown', 'style'),
         Output('dashboard-arrow', 'className')],
        Input('nav-dashboard', 'n_clicks'),
        [State('dashboard-dropdown', 'style'),
         State('dashboard-arrow', 'className')],
        prevent_initial_call=True
    )
    def toggle_dashboard_dropdown(n_clicks, current_style, current_arrow_class):
        if n_clicks:
            if current_style.get('display') == 'none':
                return {'display': 'block'}, 'nav-dropdown-icon open'
            else:
                return {'display': 'none'}, 'nav-dropdown-icon'
        return current_style or {'display': 'none'}, current_arrow_class or 'nav-dropdown-icon'

    # Home navigation callback
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks > 0) {
                window.location.href = '/';
                return '';
            }
            return '';
        }
        """,
        Output('nav-home', 'title'),
        Input('nav-home', 'n_clicks'),
        prevent_initial_call=True
    )

    # Volunteer navigation callback
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks > 0) {
                window.location.href = '/app3/';
                return '';
            }
            return '';
        }
        """,
        Output('nav-volunteer', 'title'),
        Input('nav-volunteer', 'n_clicks'),
        prevent_initial_call=True
    )

    # Logout navigation callback
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks > 0) {
                window.location.href = '/logout';
                return '';
            }
            return '';
        }
        """,
        Output('nav-logout', 'title'),
        Input('nav-logout', 'n_clicks'),
        prevent_initial_call=True
    )

# Function to get the CSS - THIS IS IMPORTANT!
def get_nav_css():
    return nav_styles

# Backward compatibility
def create_sidebar_menu():
    return html.Div(
        id="sidebar",
        children=[
            html.Div([
                html.H2("Navigation", className="display-6"),
                html.Hr(),
                html.P("Select a page:", className="lead"),
                dcc.Tabs(
                    id="sidebar-tabs",
                    value="tab-1",
                    children=[
                        dcc.Tab(label="Dashboard", value="tab-1"),
                        dcc.Tab(label="Analytics", value="tab-2"),
                        dcc.Tab(label="Settings", value="tab-3"),
                    ],
                    vertical=True,
                    style={"height": "300px"}
                ),
                html.Hr(),
                html.P("Quick filters:", className="lead"),
                dcc.Dropdown(
                    id="species-dropdown",
                    options=[
                        {"label": "All Species", "value": "all"},
                        {"label": "Setosa", "value": "setosa"},
                        {"label": "Versicolor", "value": "versicolor"},
                        {"label": "Virginica", "value": "virginica"}
                    ],
                    value="all",
                    style={"margin-bottom": "1rem"}
                ),
                dcc.Checklist(
                    id="feature-checklist",
                    options=[
                        {"label": "Show Grid", "value": "grid"},
                        {"label": "Show Legend", "value": "legend"}
                    ],
                    value=["grid", "legend"]
                )
            ])
        ],
        style={
            "position": "fixed",
            "top": 0,
            "left": "-250px",
            "bottom": 0,
            "width": "250px",
            "backgroundColor": "#2c3e50",
            "padding": "20px",
            "transition": "left 0.3s ease-in-out",
            "zIndex": 999,
        }
    )