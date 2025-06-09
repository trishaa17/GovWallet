import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import numpy as np


class DisbursementDashboardGraphs:
    def __init__(self, data_function, raw_data_function):
        """
        Initialize the disbursement graphs module
        data_function: function that returns the main dataframe
        """
        self.get_data = data_function
        self.get_data_raw = raw_data_function     

    def get_graph_options(self):
        """Return available graph options for dropdown"""
        return [
            {'label': '📊 Total Disbursement Dashboard (by role/campaign)', 'value': 'total_disbursement_by_role'},
            {'label': '📈 Overall Disbursement Trend (day/week/month)', 'value': 'disbursement_trend'},
            {'label': '❌ Rejection Rate (by role/campaign/date)', 'value': 'rejection_rate'},
            {'label': '🗺️ Location Work Statistics', 'value': 'location_heatmap'}
        ]
    
    def create_graph_dropdown_section(self):
        """Create the dropdown section for graph selection"""
        return html.Div([
            html.Hr(style={'margin': '40px 0 30px 0'}),
            html.H4("💰 Disbursement Analytics", style={
                'textAlign': 'center', 
                'marginBottom': '25px',
                'fontWeight': 'bold',
                'color': '#2c3e50'
            }),
            
            html.Div([
                html.Label("Select Dashboard Type:", style={
                    'fontWeight': 'bold', 
                    'marginBottom': '10px',
                    'display': 'block'
                }),
                dcc.Dropdown(
                    id='graph-type-selector',
                    options=self.get_graph_options(),
                    value='individual_disbursement',
                    style={'marginBottom': '20px'},
                    placeholder="Choose a disbursement analysis..."
                ),
                
                # Additional filters section
                html.Div([
                    html.Div([
                        html.Label("Date Range:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                        dcc.DatePickerRange(
                            id='graph-date-range',
                            start_date=None,  # Will be set dynamically
                            end_date=None,    # Will be set dynamically
                            display_format='YYYY-MM-DD'
                        )
                    ], style={'flex': '1', 'marginRight': '15px'}),
                    
                    html.Div([
                        html.Label("Filter by Name:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id='graph-name-filter',
                            options=[],  # Will be populated dynamically
                            multi=True,
                            placeholder="All volunteers"
                        )
                    ], style={'flex': '1', 'marginRight': '15px'}),
                    
                    html.Div([
                        html.Label("Filter by Role/Campaign:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id='graph-role-filter',
                            options=[],  # Will be populated dynamically
                            multi=True,
                            placeholder="All roles/campaigns"
                        )
                    ], style={'flex': '1'})
                ], style={'display': 'flex', 'marginBottom': '20px'})
            ], style={
                'backgroundColor': '#f8f9fa',
                'padding': '20px',
                'borderRadius': '10px',
                'border': '1px solid #e9ecef'
            }),
            
            # Graph container
            html.Div(id='dynamic-graph-container', style={'marginTop': '20px'})
        ])
    
    def total_disbursement_by_role_chart(self, df, role_filter=None):
        """Create total disbursement by role/campaign chart"""
        if role_filter:
            df = df[df['registration_location_id'].isin(role_filter)]
        
        # Group by role/campaign
        role_disbursement = df.groupby('registration_location_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'name': 'nunique'
        }).round(2)
        
        role_disbursement.columns = ['total_amount', 'avg_amount', 'total_transactions', 'unique_people']
        role_disbursement = role_disbursement.reset_index()
        role_disbursement = role_disbursement.sort_values('total_amount', ascending=True)
        
        # Create subplot
        fig = make_subplots(
            rows=1, cols=1
        )
        # Total disbursement
        fig.add_trace(
            go.Bar(x=role_disbursement['total_amount'], 
                   y=role_disbursement['registration_location_id'],
                   orientation='h', name='Total Amount', marker_color='steelblue'),
            row=1, col=1
        )
        
        fig.update_layout(height=600, title_text="Disbursement Analysis by Role/Campaign", showlegend=False)
        return fig
    
    def disbursement_trend_chart(self, df):
            """Create disbursement trend chart (daily, weekly, monthly) as bar charts with complete date ranges"""
            df['payout_date'] = pd.to_datetime(df['payout_date'])
            
            # Create complete date ranges to show zero values
            min_date = df['payout_date'].min()
            max_date = df['payout_date'].max()
            
            # Daily trend - create complete date range
            all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
            daily_disbursement = df.groupby('payout_date').agg({
                'amount': 'sum',
                'name': 'nunique'
            }).reindex(all_dates, fill_value=0).reset_index()
            daily_disbursement.columns = ['payout_date', 'amount', 'unique_people']
            
            # Weekly trend - create complete week range
            df['week_period'] = df['payout_date'].dt.to_period('W')
            all_weeks = pd.period_range(start=min_date, end=max_date, freq='W')
            weekly_disbursement = df.groupby('week_period').agg({
                'amount': 'sum',
                'name': 'nunique'
            }).reindex(all_weeks, fill_value=0).reset_index()
            weekly_disbursement.columns = ['week_period', 'amount', 'unique_people']
            weekly_disbursement['week'] = weekly_disbursement['week_period'].apply(
                lambda p: f"{p.start_time.strftime('%d %b %Y')} – {p.end_time.strftime('%d %b %Y')}"
            )            
            # Monthly trend - create complete month range
            df['month_period'] = df['payout_date'].dt.to_period('M')
            all_months = pd.period_range(start=min_date, end=max_date, freq='M')
            monthly_disbursement = df.groupby('month_period').agg({
                'amount': 'sum',
                'name': 'nunique'
            }).reindex(all_months, fill_value=0).reset_index()
            monthly_disbursement.columns = ['month_period', 'amount', 'unique_people']
            monthly_disbursement['month'] = monthly_disbursement['month_period'].dt.strftime('%b %Y')
            
            # Create subplot with 3 charts
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('Daily Disbursement Trend', 'Weekly Disbursement Trend', 'Monthly Disbursement Trend'),
                specs=[[{"secondary_y": True}], 
                    [{"secondary_y": True}], 
                    [{"secondary_y": True}]]
            )
            
            # Daily trend - Bar charts
            fig.add_trace(
                go.Bar(x=daily_disbursement['payout_date'], y=daily_disbursement['amount'], 
                    name='Daily Amount ($)', marker_color='steelblue', opacity=0.8),
                row=1, col=1, secondary_y=False
            )
            
            # Weekly trend - Bar charts
            fig.add_trace(
                go.Bar(x=weekly_disbursement['week'], y=weekly_disbursement['amount'], 
                    name='Weekly Amount ($)', marker_color='forestgreen', opacity=0.8),
                row=2, col=1, secondary_y=False
            )
            
            # Monthly trend - Bar charts
            fig.add_trace(
                go.Bar(x=monthly_disbursement['month'], y=monthly_disbursement['amount'], 
                    name='Monthly Amount ($)', marker_color='purple', opacity=0.8),
                row=3, col=1, secondary_y=False
            )
            
            # Update y-axis labels
            fig.update_yaxes(title_text="Amount ($)", secondary_y=False)
            fig.update_yaxes(title_text="Unique People", secondary_y=True)
            
            fig.update_layout(
                height=900, 
                title_text="Overall Disbursement Trends (Complete Timeline)",
                showlegend=True
            )
            return fig
    
    def rejection_rate_chart(self, df=None, role_filter=None, name_filter=None):
        """Create rejection rate analysis chart with rejected entries table"""
        if df is None:
            df = self.get_data_raw()
        
        if 'approval_final_status' not in df.columns:
            return self.create_no_data_figure("Approval status data not available for rejection analysis")
        
        # Apply name filter FIRST (this was missing!)
        if name_filter and len(name_filter) > 0:
            df = df[df['name'].isin(name_filter)].copy()
            print(f"After name filter: {len(df)} records for names: {name_filter}")
        
        # Apply role filter if provided
        role_column = None
        possible_role_columns = ['registration_location_id', 'campaign', 'role', 'location']
        for col in possible_role_columns:
            if col in df.columns:
                role_column = col
                break
        
        if role_filter and role_column:
            df = df[df[role_column].isin(role_filter)].copy()
            print(f"After role filter: {len(df)} records")
        elif role_filter and not role_column:
            print(f"Warning: No role column found. Available columns: {list(df.columns)}")
        
        # Check if we have any data left after filtering
        if df.empty:
            return self.create_no_data_figure("No data available after applying filters")
        
        # Use approval_final_status column
        status_column = 'approval_final_status'
        
        # Calculate rejection rates by role/campaign
        try:
            if role_column:
                status_by_role = df.groupby([role_column, status_column]).size().unstack(fill_value=0)
            else:
                # If no role column, group by a default or create one
                df['default_group'] = 'All Users'
                status_by_role = df.groupby(['default_group', status_column]).size().unstack(fill_value=0)
                role_column = 'default_group'
        except Exception as e:
            return self.create_no_data_figure(f"Error calculating rejection rates: {str(e)}")
        
        # Check what rejection statuses actually exist
        print(f"Available approval statuses: {df[status_column].value_counts()}")
        
        # Look for rejection statuses in the VALUES, not column names
        available_statuses = df[status_column].unique()
        rejected_statuses = [status for status in available_statuses 
                            if str(status).lower() in ['rejected', 'failed', 'failure', 'deny', 'denied', 'invalid']]
        
        print(f"Found rejected statuses: {rejected_statuses}")
        
        # Look for approved statuses in the VALUES
        approved_statuses = [status for status in available_statuses 
                            if str(status).lower() in ['approved', 'accepted', 'success', 'valid', 'confirmed']]
        
        print(f"Found approved statuses: {approved_statuses}")
        
        # Calculate totals
        total_by_role = status_by_role.sum(axis=1)
        
        if rejected_statuses:
            # Get rejected columns that exist in the pivot table
            rejected_columns = [col for col in status_by_role.columns if col in rejected_statuses]
            if rejected_columns:
                rejected_by_role = status_by_role[rejected_columns].sum(axis=1)
                # Get rejected entries for table
                rejected_df = df[df[status_column].isin(rejected_statuses)].copy()
            else:
                rejected_by_role = pd.Series(0, index=total_by_role.index)
                rejected_df = pd.DataFrame()
        else:
            # No rejections found
            rejected_by_role = pd.Series(0, index=total_by_role.index)
            rejected_df = pd.DataFrame()
        
        # Calculate approved entries
        if approved_statuses:
            # Get approved columns that exist in the pivot table
            approved_columns = [col for col in status_by_role.columns if col in approved_statuses]
            if approved_columns:
                approved_by_role = status_by_role[approved_columns].sum(axis=1)
            else:
                approved_by_role = pd.Series(0, index=total_by_role.index)
        else:
            # No approvals found
            approved_by_role = pd.Series(0, index=total_by_role.index)
        
        # Create rejected entries table
        if not rejected_df.empty and len(rejected_df) > 0:
            # Find date column
            date_columns = [col for col in rejected_df.columns 
                        if any(keyword in col.lower() for keyword in ['date', 'created', 'time', 'timestamp'])]
            
            print(f"Potential date columns: {date_columns}")
            
            if date_columns:
                date_col = date_columns[0]
                try:
                    # Create a clean date column
                    rejected_df['display_date'] = pd.to_datetime(rejected_df[date_col], errors='coerce').dt.date
                    # Handle any NaT values
                    rejected_df['display_date'] = rejected_df['display_date'].fillna('Invalid Date')
                except Exception as e:
                    print(f"Date conversion error: {e}")
                    rejected_df['display_date'] = rejected_df[date_col].astype(str)
            else:
                rejected_df['display_date'] = 'No Date Available'
            
            try:
                # Create summary table grouped by date
                rejected_summary = []
                
                for date_val in rejected_df['display_date'].unique():
                    date_subset = rejected_df[rejected_df['display_date'] == date_val]
                    
                    # Get unique campaigns and rejection reasons
                    campaigns = date_subset[role_column].unique() if role_column != 'default_group' else ['All']
                    reasons = date_subset['approval_final_status'].unique()
                    
                    # Get sample names if available
                    if 'name' in date_subset.columns:
                        names = date_subset['name'].dropna().unique()
                        name_display = ', '.join(names[:3]) + ('...' if len(names) > 3 else '')
                    else:
                        name_display = 'N/A'
                    
                    rejected_summary.append({
                        'date': str(date_val),
                        'rejection_count': len(date_subset),
                        'campaigns': ', '.join(map(str, campaigns)),
                        'rejection_reasons': ', '.join(reasons),
                        'names': name_display
                    })
                
                # Convert to DataFrame
                rejected_by_date = pd.DataFrame(rejected_summary)
                
                # Create table trace
                table_trace = go.Table(
                    header=dict(
                        values=['Date', 'Rejection Count', 'Campaigns', 'Rejection Reasons', 'Sample Names'],
                        fill_color='lightblue',
                        align='left',
                        font=dict(size=12, color='black')
                    ),
                    cells=dict(
                        values=[
                            rejected_by_date['date'],
                            rejected_by_date['rejection_count'],
                            rejected_by_date['campaigns'],
                            rejected_by_date['rejection_reasons'],
                            rejected_by_date['names']
                        ],
                        fill_color='white',
                        align='left',
                        font=dict(size=11)
                    )
                )
            except Exception as e:
                print(f"Error creating rejection summary: {e}")
                # Fallback to simple table
                table_trace = go.Table(
                    header=dict(
                        values=['Message'],
                        fill_color='lightblue',
                        align='center',
                        font=dict(size=12, color='black')
                    ),
                    cells=dict(
                        values=[['Error processing rejected entries']],
                        fill_color='lightgray',
                        align='center',
                        font=dict(size=11)
                    )
                )
        else:
            # Create empty table with message if no rejected entries
            table_trace = go.Table(
                header=dict(
                    values=['Message'],
                    fill_color='lightblue',
                    align='center',
                    font=dict(size=12, color='black')
                ),
                cells=dict(
                    values=[['No rejected entries found']],
                    fill_color='lightgray',
                    align='center',
                    font=dict(size=11)
                )
            )
        
        # Create subplot with table
        try:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Approval Status by Role/Campaign', 'Rejected Entries by Date'),
                specs=[[{"type": "bar"}], 
                    [{"type": "table"}]],
                row_heights=[0.6, 0.4]
            )
            
            # Add approved entries bar chart (green)
            fig.add_trace(
                go.Bar(
                    x=list(total_by_role.index), 
                    y=list(approved_by_role.values), 
                    name='Approved',
                    marker_color='green',
                    text=list(approved_by_role.values),
                    texttemplate='%{text}',
                    textposition='outside',
                    offsetgroup=1
                ),
                row=1, col=1
            )
            
            # Add rejected entries bar chart (red)
            fig.add_trace(
                go.Bar(
                    x=list(total_by_role.index), 
                    y=list(rejected_by_role.values), 
                    name='Rejected',
                    marker_color='red',
                    text=list(rejected_by_role.values),
                    texttemplate='%{text}',
                    textposition='outside',
                    offsetgroup=2
                ),
                row=1, col=1
            )
            
            # Add rejected entries table
            fig.add_trace(table_trace, row=2, col=1)
            
            fig.update_layout(
                height=800,
                showlegend=True,
                title_text="Approval/Rejection Analysis Dashboard",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Update axes
            fig.update_yaxes(title_text="Number of Entries", row=1, col=1)
            fig.update_xaxes(title_text=role_column.replace('_', ' ').title(), row=1, col=1)
            
            # Update annotation fonts
            for annotation in fig['layout']['annotations']:
                annotation['font'] = dict(size=16, color='black', family='Arial')
            
            return fig
        
        except Exception as e:
            print(f"Error creating figure: {e}")
            return self.create_no_data_figure(f"Error creating rejection chart: {str(e)}")
        
    def location_dashboard_chart(self, df):
        """Create location work statistics dashboard with cards"""
        
        # Group by location and calculate metrics
        location_metrics = df.groupby('registration_location_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'name': 'nunique',
            'payout_date': 'nunique'
        }).round(2)
        
        location_metrics.columns = ['total_earned', 'avg_per_session', 'total_sessions','days_worked', 'unique_people']
        location_metrics = location_metrics.reset_index()
        
        # Calculate number of rows needed (2 cards per row)
        num_locations = len(location_metrics)
        num_rows = (num_locations + 1) // 2  # Round up division
        
        # Create subplots - 2 columns, multiple rows
        fig = make_subplots(
            rows=num_rows, 
            cols=2,
            subplot_titles=[f"{row['registration_location_id']}" for _, row in location_metrics.iterrows()],
            specs=[[{"type": "indicator"}, {"type": "indicator"}] for _ in range(num_rows)],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # Color scheme for different metrics
        colors = ['#28a745', '#007bff', '#dc3545', '#ffc107', '#6c757d']
        
        for idx, (_, location_data) in enumerate(location_metrics.iterrows()):
            row = (idx // 2) + 1
            col = (idx % 2) + 1
            
            location_name = location_data['registration_location_id']
            
            # Create a multi-metric indicator for each location
            fig.add_trace(
                go.Indicator(
                    mode="number+gauge+delta",
                    value=location_data['total_earned'],
                    domain={'row': row-1, 'column': col-1},
                    title={
                        "text": f"<b>{location_name}</b><br><span style='font-size:0.8em;color:gray'>Total Earned</span>",
                        "font": {"size": 16}
                    },
                    number={
                        'prefix': '$',
                        'font': {'size': 24, 'color': colors[0]}
                    },
                    gauge={
                        'shape': "bullet",
                        'axis': {'range': [None, location_metrics['total_earned'].max()]},
                        'threshold': {
                            'line': {'color': "red", 'width': 2},
                            'thickness': 0.75,
                            'value': location_metrics['total_earned'].mean()
                        },
                        'steps': [
                            {'range': [0, location_metrics['total_earned'].mean()], 'color': "lightgray"},
                            {'range': [location_metrics['total_earned'].mean(), location_metrics['total_earned'].max()], 'color': "gray"}
                        ],
                        'bar': {'color': colors[0]}
                    },
                    delta={
                        'reference': location_metrics['total_earned'].mean(),
                        'relative': True,
                        'position': "bottom"
                    }
                ),
                row=row, col=col
            )
        
        # Alternative simpler approach with custom annotations
        fig_simple = go.Figure()
        
        # Calculate grid positions
        card_width = 0.45
        card_height = 0.25
        x_positions = [0.05, 0.52]  # Left and right positions
        
        for idx, (_, location_data) in enumerate(location_metrics.iterrows()):
            row_idx = idx // 2
            col_idx = idx % 2
            
            x_pos = x_positions[col_idx]
            y_pos = 0.9 - (row_idx * 0.3)  # Stack vertically
            
            location_name = location_data['registration_location_id']
            total_earned = location_data['total_earned']
            days_worked = int(location_data['days_worked'])
            total_sessions = int(location_data['total_sessions'])
            avg_per_day = total_earned / total_sessions if days_worked > 0 else 0

            
            # Create card background
            fig_simple.add_shape(
                type="rect",
                x0=x_pos, y0=y_pos-card_height, x1=x_pos+card_width, y1=y_pos,
                line=dict(color="lightgray", width=1),
                fillcolor="white",
                layer="below"
            )
            
            # Location title
            fig_simple.add_annotation(
                x=x_pos + card_width/2, y=y_pos - 0.03,
                text=f"<b>{location_name}</b>",
                showarrow=False,
                font=dict(size=14, color="black"),
                align="center"
            )
            
            # Total Earned (large, green)
            fig_simple.add_annotation(
                x=x_pos + 0.15, y=y_pos - 0.1,
                text=f"<b style='color:#28a745; font-size:20px'>${total_earned:.2f}</b><br><span style='color:gray; font-size:12px'>Total Earned</span>",
                showarrow=False,
                align="center"
            )
            
            # Days Worked (blue)
            fig_simple.add_annotation(
                x=x_pos + card_width/2, y=y_pos - 0.1,
                text=f"<b style='color:#007bff; font-size:18px'>{total_sessions}</b><br><span style='color:gray; font-size:12px'>Days Worked</span>",
                showarrow=False,
                align="center"
            )
            
            # Avg per Day (red/orange)
            fig_simple.add_annotation(
                x=x_pos + card_width - 0.15, y=y_pos - 0.1,
                text=f"<b style='color:#dc3545; font-size:18px'>${avg_per_day:.2f}</b><br><span style='color:gray; font-size:12px'>Pay Rate</span>",
                showarrow=False,
                align="center"
            )
            
            # Total Sessions (bottom, smaller)
            fig_simple.add_annotation(
                x=x_pos + card_width/2, y=y_pos - 0.2,
                text=f"<span style='color:#6c757d; font-size:14px'>{total_sessions} sessions",
                showarrow=False,
                align="center"
            )
        
        # Configure layout
        fig_simple.update_layout(
            title={
                'text': "Location Work Statistics Dashboard",
                'font': {'size': 20},
                'x': 0.5
            },
            xaxis={'range': [0, 1], 'showgrid': False, 'showticklabels': False, 'zeroline': False},
            yaxis={'range': [0, 1], 'showgrid': False, 'showticklabels': False, 'zeroline': False},
            plot_bgcolor='rgba(248,249,250,0.8)',
            paper_bgcolor='white',
            height=max(400, num_rows * 200),
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False
        )
        
        return fig_simple
    
    def create_no_data_figure(self, message="No data available"):
        """Create a placeholder figure when data is not available"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=400
        )
        return fig
    
    def generate_graph(self, graph_type, df, name_filter=None, role_filter=None):
        """Generate the selected graph type"""
        if graph_type == 'rejection_rate':
            # use raw data, then filter by person
            df = self.get_data_raw()
            if name_filter and len(name_filter) > 0:
                from urllib.parse import unquote
                decoded_names = [unquote(n).strip() for n in name_filter]
                df = df[df['name'].str.strip().isin(decoded_names)]
            return self.rejection_rate_chart(df, role_filter)

        if df is None or df.empty:
            return self.create_no_data_figure("No data available")

        # Apply name filter for other chart types
        if name_filter and len(name_filter) > 0:
            df = df[df['name'].isin(name_filter)]

        graph_functions = {
            'total_disbursement_by_role': self.total_disbursement_by_role_chart,
            'disbursement_trend': self.disbursement_trend_chart,
            'location_heatmap': self.location_dashboard_chart
        }

        if graph_type in graph_functions:
            try:
                if graph_type == 'total_disbursement_by_role':
                    return graph_functions[graph_type](df, role_filter)
                else:
                    return graph_functions[graph_type](df)
            except Exception as e:
                return self.create_no_data_figure(f"Error generating graph: {str(e)}")
        else:
            return self.create_no_data_figure("Invalid graph type selected")

    
    def setup_callbacks(self, app):
        """Setup callbacks for the graphs functionality"""
        
        @app.callback(
            [Output('graph-date-range', 'start_date'),
             Output('graph-date-range', 'end_date'),
             Output('graph-name-filter', 'options'),
             Output('graph-role-filter', 'options')],
            [Input('graph-type-selector', 'value')]
        )
        def update_filter_options(selected_graph):
            df = self.get_data()
            
            # Set date range
            if not df.empty and 'payout_date' in df.columns:
                df['payout_date'] = pd.to_datetime(df['payout_date'])
                start_date = df['payout_date'].min().date()
                end_date = df['payout_date'].max().date()
            else:
                start_date = None
                end_date = None
            
            # Set name options
            name_options = []
            if not df.empty and 'name' in df.columns:
                unique_names = sorted(df['name'].dropna().unique())
                name_options = [{'label': name, 'value': name} for name in unique_names]
            
            # Set role/campaign options
            role_options = []
            if not df.empty and 'registration_location_id' in df.columns:
                unique_roles = sorted(df['registration_location_id'].dropna().unique())
                role_options = [{'label': role, 'value': role} for role in unique_roles]
            
            return start_date, end_date, name_options, role_options
        
        @app.callback(
            Output('dynamic-graph-container', 'children'),
            [Input('graph-type-selector', 'value'),
             Input('graph-date-range', 'start_date'),
             Input('graph-date-range', 'end_date'),
             Input('graph-name-filter', 'value'),
             Input('graph-role-filter', 'value')]
        )
        def update_graph(graph_type, start_date, end_date, name_filter, role_filter):
            if not graph_type:
                return html.Div("Please select a dashboard type.", style={'textAlign': 'center', 'padding': '20px'})
            
            df = self.get_data()
            
            if df.empty:
                return html.Div("No data available.", style={'textAlign': 'center', 'padding': '20px'})
            
            # Apply date filter
            if start_date and end_date and 'payout_date' in df.columns:
                df['payout_date'] = pd.to_datetime(df['payout_date'])
                df = df[(df['payout_date'].dt.date >= pd.to_datetime(start_date).date()) &
                       (df['payout_date'].dt.date <= pd.to_datetime(end_date).date())]
            
            # Generate graph
            fig = self.generate_graph(graph_type, df, name_filter, role_filter)
            
            return dcc.Graph(
                figure=fig,
                style={'backgroundColor': 'white', 'borderRadius': '10px', 'padding': '10px'}
            )