from dash import Dash, dcc, html, Input, Output, dash_table, State
import pandas as pd
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme
import requests
from io import StringIO
import urllib.parse
from dash import callback
from urllib.parse import unquote
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from dashPeople import get_data, get_data_raw, df1
from graphs_people import DisbursementDashboardGraphs

graphs_module = DisbursementDashboardGraphs(get_data, get_data_raw)

def register_callbacks(dash_app):
    global app
    app = dash_app    
    @app.callback(
    Output('advanced-filter-container', 'style'),
    Input('toggle-advanced-filters', 'n_clicks'),
    prevent_initial_call=True)
    def toggle_advanced_filters(n_clicks):
        if n_clicks % 2 == 1:
            return {'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '20px', 'gap': '10px'}
        return {'display': 'none'}

    @app.callback(
        Output('identity-table', 'data'),
        [
            Input('identity-filter-btn', 'n_clicks'),
            Input('name-filter-bottom', 'value'),
            Input('gms-id-input', 'value'),
            Input('badge-id-input', 'value'),
            Input('role-input', 'value')
        ]
    )
    def update_identity_table(n_clicks, selected_names, gms_id, badge_id, role):
        local_df = df1.copy()
        local_df['name'] = local_df['name'].str.strip().str.upper()

        people = local_df.drop_duplicates(subset='name')[['name', 'gms_id', 'badge_id', 'gms_role_name']].copy()

        if selected_names:
            people = people[people['name'].isin(selected_names)]

        if gms_id:
            people = people[people['gms_id'].astype(str).str.contains(gms_id.strip(), case=False, na=False)]

        if badge_id:
            people = people[people['badge_id'].astype(str).str.contains(badge_id.strip(), case=False, na=False)]

        if role:
            people = people[people['gms_role_name'].astype(str).str.contains(role.strip(), case=False, na=False)]

        return [
            {
                "link": f"[{row['name'].title()}](/app3/person/{urllib.parse.quote(str(row['name']))})",
                "gms_id": row['gms_id'] if pd.notna(row['gms_id']) else "—",
                "badge_id": row['badge_id'] if pd.notna(row['badge_id']) else "—",
                "gms_role_name": row['gms_role_name'] if pd.notna(row['gms_role_name']) else "—"
            }
            for _, row in people.iterrows()
        ]




def register_person_callbacks(dash_app):
    @dash_app.callback(
        Output('date-filter-container', 'style'),
        Input('toggle-date-filter', 'n_clicks'),
        prevent_initial_call=True
    )
    def toggle_date_filter(n_clicks):
        if n_clicks % 2 == 1:
            return {'display': 'block', 'marginBottom': '10px'}
        return {'display': 'none', 'marginBottom': '10px'}

    @dash_app.callback(
        Output('accordion-container', 'children'),
        [Input('date-sort-order', 'value'),
         Input('date-filter', 'date')],
        [State('url', 'pathname')]
    )
    def update_accordion(sort_order, selected_date, pathname):
        from urllib.parse import unquote
        name = unquote(pathname.split('/')[-1])

        df = get_data()
        df = df[df['name'] == name]

        # Apply date filter ONLY if selected_date is provided AND sort_order is not 'all'
        if selected_date and sort_order != 'all':
            selected_date_obj = pd.to_datetime(selected_date).date()
            df = df[df['payout_date'] == selected_date_obj]

        # If no data after filtering, return empty accordion
        if df.empty:
            return dbc.Accordion([
                dbc.AccordionItem([
                    html.P("No shifts found for the selected criteria.", style={'textAlign': 'center', 'color': '#666'})
                ], title="No Data", className="bg-light")
            ], start_collapsed=False)

        # Group by date first
        grouped = df.groupby('payout_date')
        
        # Convert to list of tuples and sort by date
        date_groups = list(grouped)
        
        if sort_order == 'desc':
            date_groups.sort(key=lambda x: x[0], reverse=True)  # Sort by date descending
        elif sort_order == 'asc':
            date_groups.sort(key=lambda x: x[0], reverse=False)  # Sort by date ascending
        # For 'all', keep the natural groupby order (no additional sorting needed)
        
        accordion_items = []
        for date, group in date_groups:
            total_shifts_date = group.shape[0]
            total_amount = group['amount'].sum()
            
            shift_details = [
                html.Tr([
                    html.Td(shift),
                    html.Td(status),
                    html.Td(f"${amount:.2f}")
                ]) for shift, status, amount in zip(
                    group['registration_location_id'], 
                    group['approval_stage'], 
                    group['amount']
                )
            ]
            
            # Add total row
            shift_details.append(
                html.Tr([
                    html.Td(html.B("Total Amount Earned")),
                    html.Td(),
                    html.Td(html.B(f"${total_amount:.2f}"))
                ], style={"backgroundColor": "#f8f9fa", "borderTop": "2px solid #ccc"})
            )

            accordion_items.append(
                dbc.AccordionItem([
                    html.Br(),
                    html.P(f"Total shifts: {total_shifts_date}", style={'fontWeight': 'bold'}),
                    dbc.Table([
                        html.Thead(html.Tr([
                            html.Th("Shift Name"), 
                            html.Th("Status"), 
                            html.Th("Amount Paid")
                        ])),
                        html.Tbody(shift_details)
                    ], bordered=True)
                ], title=date.strftime("%Y-%m-%d"), className="bg-light")
            )

        return dbc.Accordion(accordion_items, start_collapsed=True)

    @dash_app.callback(
        Output('page-indicator', 'children'),
        [Input('date-sort-order', 'value'),
         Input('date-filter', 'date')],
        [State('url', 'pathname')]
    )
    def update_page_indicator(sort_order, selected_date, pathname):
        from urllib.parse import unquote
        name = unquote(pathname.split('/')[-1])

        df = get_data()
        df = df[df['name'] == name]

        # Apply date filter ONLY if selected_date is provided AND sort_order is not 'all'
        if selected_date and sort_order != 'all':
            selected_date_obj = pd.to_datetime(selected_date).date()
            df = df[df['payout_date'] == selected_date_obj]

        # Count unique dates (pages)
        unique_dates = df['payout_date'].nunique()
        
        if sort_order == 'all':
            return f"Showing all {unique_dates} dates"
        else:
            return f"Page 1 of {unique_dates}"
        
    @app.callback(
    Output('person-graph-container', 'children'),
    [Input('person-graph-selector', 'value')],
    [State('url', 'pathname')]  # Assuming you have url component in your layout
    )
    def update_person_graph(graph_type, pathname):
        if not graph_type or not pathname:
            return html.Div("Please select a graph type.", style={'textAlign': 'center', 'padding': '20px'})
        
        # Extract person name from pathname
        if '/person/' in pathname:
            name = pathname.split('/person/')[-1]
            name = unquote(name)  # URL decode the name
            
            # Filter data for this specific person
            df = get_data()
            person_df = df[df['name'] == name]
            
            if person_df.empty:
                return html.Div("No data available for this person.", style={'textAlign': 'center', 'padding': '20px'})
            
            # Generate graph for this person
            fig = graphs_module.generate_graph(graph_type, person_df, name_filter=[name])
            
            return dcc.Graph(
                figure=fig,
                style={'backgroundColor': 'white', 'borderRadius': '10px', 'padding': '10px'}
            )
        
        return html.Div("Person not found.", style={'textAlign': 'center', 'padding': '20px'})
            
