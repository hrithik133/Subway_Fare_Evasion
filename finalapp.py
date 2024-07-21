import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dash import Dash, html, dcc, Input, Output
import plotly.graph_objects as go
import numpy as np
import geopandas as gpd

# Data dictionaries for each quarter in 2023
race_data = {
    'Q1': {'AMER IND': 0, 'ASIAN/PAC.ISL': 14, 'BLACK': 566, 'HISPANIC': 288, 'UNKNOWN': 8, 'WHITE': 47},
    'Q2': {'AMER IND': 1, 'ASIAN/PAC.ISL': 17, 'BLACK': 681, 'HISPANIC': 326, 'UNKNOWN': 39, 'WHITE': 72},
    'Q3': {'AMER IND': 1, 'ASIAN/PAC.ISL': 23, 'BLACK': 687, 'HISPANIC': 360, 'UNKNOWN': 2, 'WHITE': 69},
    'Q4': {'AMER IND': 1, 'ASIAN/PAC.ISL': 23, 'BLACK': 785, 'HISPANIC': 365, 'UNKNOWN': 3, 'WHITE': 75}
}

age_data = {
    'Q1': {'10 - 17': 2, '18 - 24': 173, '25 - 40': 491, '41 - 59': 234, '60+': 23},
    'Q2': {'10 - 17': 4, '18 - 24': 173, '25 - 40': 608, '41 - 59': 318, '60+': 33},
    'Q3': {'10 - 17': 3, '18 - 24': 208, '25 - 40': 599, '41 - 59': 309, '60+': 23},
    'Q4': {'10 - 17': 8, '18 - 24': 209, '25 - 40': 664, '41 - 59': 336, '60+': 35}
}

total_data = {
    'Q1': 923,
    'Q2': 1136,
    'Q3': 1142,
    'Q4': 1252
}

gender_data = {
    'Q1': {'MALE': 868, 'FEMALE': 51, 'UNKNOWN': 0},
    'Q2': {'MALE': 1003, 'FEMALE': 53, 'UNKNOWN': 0},
    'Q3': {'MALE': 1068, 'FEMALE': 63, 'UNKNOWN': 0},
    'Q4': {'MALE': 1182, 'FEMALE': 70, 'UNKNOWN': 0}
}

# Data for last quarter of 2022
last_quarter_2022_race = {'AMER IND': 0, 'ASIAN/PAC.ISL': 6, 'BLACK': 388, 'HISPANIC': 171, 'UNKNOWN': 0, 'WHITE': 36}
last_quarter_2022_age = {'10 - 17': 0, '18 - 24': 105, '25 - 40': 298, '41 - 59': 175, '60+': 23}
last_quarter_2022_gender = {'MALE': 573, 'FEMALE': 28, 'UNKNOWN': 0}
last_quarter_2022_total = 601

app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Subway Fare Evasion Dashboard"),
    html.H2("Developed by Hrithik Shukla"),
    html.H3("Source: NYPD Fare Evasion Reports"),
    
    html.Label("Select Quarter:"),
    dcc.Dropdown(
        id='quarter-selector',
        options=[
            {'label': 'Q1', 'value': 'Q1'},
            {'label': 'Q2', 'value': 'Q2'},
            {'label': 'Q3', 'value': 'Q3'},
            {'label': 'Q4', 'value': 'Q4'},
        ],
        value='Q1'
    ),

    html.Label("Select Year:"),
    dcc.Dropdown(
        id='year-selector',
        options=[
            {'label': '2023', 'value': 2023},
        ],
        value=2023
    ),
    
    html.Div(id='total-arrests-container', style={'textAlign': 'center', 'fontSize': 10, 'color': 'black'}),
    html.Div(id='percent-change-container', style={'textAlign': 'center', 'fontSize': 10}),
    
    html.Div([
        dcc.Graph(id='fare-evasion-graph', config={'responsive': True}, style={'width': '100%', 'display': 'inline-block'}),
        dcc.Graph(id='age-evasion-graph', config={'responsive': True}, style={'width': '100%', 'display': 'inline-block'}),
        dcc.Graph(id='gender-evasion-graph', config={'responsive': True}, style={'width': '100%', 'display': 'inline-block'}),
        dcc.Graph(id='top-stations-graph', config={'responsive': True}, style={'width': '100%', 'display': 'inline-block'}),
        dcc.Graph(id='borough-counts-graph', config={'responsive': True}, style={'width': '100%', 'display': 'inline-block'})
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'width': '100%'}),
    html.Style("""
        @media only screen and (max-width: 600px) {
            .dash-graph {
                width: 100% !important;
                display: block !important;
            }
        }
    """)
], style={'padding': '20px'})

# Define categories
race = ["AMER IND", "ASIAN/PAC.ISL", "BLACK", "HISPANIC", "UNKNOWN", "WHITE"]
age_bracket = ["10 - 17", "18 - 24", "25 - 40", "41 - 59", "60+"]
gender = ["MALE", "FEMALE", "UNKNOWN"]

def fetch_and_process_data_2(quarter, year):
    # Define dictionaries for each quarter
    data = {
        'Q1': {'STILLWELL AVENUE-CONEY ISLAND': 47, '161 ST.-YANKEE STADIUM': 42, '3 AVENUE-149 STREET': 35, 'BROADWAY-EAST NEW YORK': 35, 'LIVONIA AVENUE': 30, 'ATLANTIC AVENUE': 28, 'BROOK AVENUE': 26, 'KINGSBRIDGE ROAD': 21, '149 ST.-GRAND CONCOURSE': 18, 'ROCKAWAY AVENUE': 18},
        'Q2': {'STILLWELL AVENUE-CONEY ISLAND': 85, '3 AVENUE-149 STREET': 47, '161 ST.-YANKEE STADIUM': 47, 'SIMPSON STREET': 44, 'HUNTS POINT AVENUE': 34, '42 ST.-PORT AUTHORITY BUS TERMINAL': 31, 'FAR ROCKAWAY-MOTT AVE.': 30, '59 ST.-COLUMBUS CIRCLE': 29, 'BROOK AVENUE': 21, 'JAY STREET-BOROUGH HALL': 20},
        'Q3': {'42 ST.-PORT AUTHORITY BUS TERMINAL': 85, 'ATLANTIC AVENUE': 47, 'STILLWELL AVENUE-CONEY ISLAND': 47, '59 ST.-COLUMBUS CIRCLE': 44, '161 ST.-YANKEE STADIUM': 34, 'GUN HILL ROAD': 31, '3 AVENUE-149 STREET': 30, 'SIMPSON STREET': 29, 'MYRTLE AVENUE': 21, 'FLUSHING AVENUE': 20},
        'Q4': {'161 ST.-YANKEE STADIUM': 62, '3 AVENUE-149 STREET': 58, '42 ST.-PORT AUTHORITY BUS TERMINAL': 55, 'SIMPSON STREET': 37, 'ATLANTIC AVENUE': 35, 'STILLWELL AVENUE-CONEY ISLAND': 34, 'NOSTRAND AVENUE': 30, 'RALPH AVENUE': 30, '59 ST.-COLUMBUS CIRCLE': 29, 'GUN HILL ROAD': 24}
    }
    
    # Fetch the dictionary for the selected quarter
    selected_data = data.get(quarter, {})
    
    return selected_data

def fetch_and_process_data_3(quarter, year):
    # Define dictionaries for each quarter
    data = {
        'Q1': {'BRONX': 349, 'BROOKLYN': 406, 'MANHATTAN': 114, 'QUEENS': 54, 'STATEN ISLAND': 0},
        'Q2': {'BRONX': 410, 'BROOKLYN': 452, 'MANHATTAN': 200, 'QUEENS': 74, 'STATEN ISLAND': 0},
        'Q3': {'BRONX': 314, 'BROOKLYN': 464, 'MANHATTAN': 294, 'QUEENS': 70, 'STATEN ISLAND': 0},
        'Q4': {'BRONX': 404, 'BROOKLYN': 472, 'MANHATTAN': 261, 'QUEENS': 92, 'STATEN ISLAND': 23}
    }
    
    # Fetch the dictionary for the selected quarter
    selected_data = data.get(quarter, {})
    
    return selected_data

# Callback to update total arrests and percent change
@app.callback(
    [Output('total-arrests-container', 'children'),
     Output('percent-change-container', 'children')],
    [Input('quarter-selector', 'value')]
)
def update_totals(selected_quarter):
    total_arrests = total_data[selected_quarter]
    
    # Calculate percent change
    if selected_quarter == 'Q1':
        prev_total_arrests = last_quarter_2022_total
    else:
        prev_total_arrests = total_data['Q' + str(int(selected_quarter[1]) - 1)]
    
    if prev_total_arrests != 0:
        percent_change = ((total_arrests - prev_total_arrests) / prev_total_arrests) * 100
    else:
        percent_change = 0

    # Format percent change as string
    percent_change_str = f"{percent_change:.1f}%" if percent_change != 0 else "No change"

    # Determine color based on percent change
    percent_change_color = 'green' if percent_change < 0 else 'red'

    return (
        html.Div([
            html.Div([
                html.H2("Total Arrests", style={'font-size': '24px', 'color': 'black'}),
                html.H2(f"{total_arrests:,}", style={'font-size': '32px', 'color': '#CC0000'})
            ], style={'width': '50%', 'display': 'inline-block', 'text-align': 'center'}),

            html.Div([
                html.H2("Percent Change", style={'font-size': '24px', 'color': 'black'}),
                html.H2(percent_change_str, style={'font-size': '32px', 'color': percent_change_color})
            ], style={'width': '50%', 'display': 'inline-block', 'text-align': 'center'})
        ], style={'text-align': 'center', 'margin-bottom': '20px'}),
        ''
    )

# Add callback for race-based graph
@app.callback(
    Output('fare-evasion-graph', 'figure'),
    [Input('quarter-selector', 'value')]
)
def race_graph(selected_quarter):
    # Get data for the selected quarter
    selected_race_values = list(race_data[selected_quarter].values())
    selected_categories_race = list(race_data[selected_quarter].keys())

    # Determine the previous quarter based on the selected quarter
    if selected_quarter == 'Q1':
        previous_quarter = 'Q4'
        previous_year = 2022  
        previous_data = last_quarter_2022_race
    else:
        previous_quarter = 'Q' + str(int(selected_quarter[1]) - 1)
        previous_year = 2023
        previous_data = race_data[previous_quarter]
        
        # If Q1 is selected, add the values from last_quarter_2022_race to the previous year
        if previous_quarter == 'Q4':
            for race_category, value in last_quarter_2022_race.items():
                previous_data[race_category] = value

    # Fetch the data for the previous quarter
    previous_race_values = [previous_data.get(race_category, 0) for race_category in selected_categories_race]

    # Combine data from the selected quarter and the previous quarter
    combined_race_values = selected_race_values + previous_race_values
    combined_categories_race = selected_categories_race + list(previous_data.keys())

    # Sort the data in descending order
    sorted_indices = np.argsort(selected_race_values)[::-1]
    sorted_selected_race_values = [selected_race_values[i] for i in sorted_indices]
    sorted_selected_categories_race = [selected_categories_race[i] for i in sorted_indices]

    sorted_indices_previous = np.argsort(previous_race_values)[::-1]
    sorted_previous_race_values = [previous_race_values[i] for i in sorted_indices_previous]
    sorted_previous_categories_race = [combined_categories_race[i] for i in sorted_indices_previous]

    # Define the width of each bar
    bar_width = 0.50

    # Define the x-coordinates for bars of each quarter
    x_selected = np.arange(len(selected_categories_race))
    x_previous = [x + bar_width for x in x_selected]

    # Use Plotly for the graph
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_selected, y=sorted_selected_race_values, name='Selected Quarter', marker_color='#CC0000', hovertemplate='<b>%{y}</b>'))
    fig.add_trace(go.Bar(x=x_previous, y=sorted_previous_race_values, name='Previous Quarter', marker_color='#FFCCB3', hovertemplate='<b>%{y}</b>'))  # Update trace name

    # Customize layout
    fig.update_layout(
        title='Arrests by Race',
        xaxis=dict(title='Race', tickvals=[x + bar_width / 2 for x in range(len(combined_categories_race))], ticktext=sorted_selected_categories_race),
        yaxis=dict(title='Number of Arrests'),
        legend=dict(x=0.51, y=0.99, bordercolor="Black", borderwidth=0.5),
        barmode='group',
        plot_bgcolor='rgba(255, 255, 255, 1)'
    )

    return fig


# Add callback for age-based graph
@app.callback(
    Output('age-evasion-graph', 'figure'),
    [Input('quarter-selector', 'value')]
)
def age_graph(selected_quarter):
    # Get data for the selected quarter
    selected_age_values = list(age_data[selected_quarter].values())
    selected_categories_age = list(age_data[selected_quarter].keys())

    # Determine the previous quarter based on the selected quarter
    if selected_quarter == 'Q1':
        previous_quarter = 'Q4'
        previous_year = 2022  
        previous_data = last_quarter_2022_age
    else:
        previous_quarter = 'Q' + str(int(selected_quarter[1]) - 1)
        previous_year = 2023
        previous_data = age_data[previous_quarter]
        
        # If Q1 is selected, add the values from last_quarter_2022_age to the previous year
        if previous_quarter == 'Q4':
            for age_category, value in last_quarter_2022_age.items():
                previous_data[age_category] = value

    # Fetch the data for the previous quarter
    previous_age_values = [previous_data.get(age_category, 0) for age_category in selected_categories_age]

    # Combine data from the selected quarter and the previous quarter
    combined_age_values = selected_age_values + previous_age_values
    combined_categories_age = selected_categories_age + list(previous_data.keys())

    # Define the width of each bar
    bar_width = 0.50

    # Define the x-coordinates for bars of each quarter
    x_selected = np.arange(len(selected_categories_age))
    x_previous = [x + bar_width for x in x_selected]

    # Use Plotly for the graph
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_selected, y=selected_age_values, name='Selected Quarter', marker_color='#CC0000', hovertemplate='<b>%{y}</b>'))
    fig.add_trace(go.Bar(x=x_previous, y=previous_age_values, name='Previous Quarter', marker_color='#FFCCB3', hovertemplate='<b>%{y}</b>'))  # Update trace name

    # Customize layout
    fig.update_layout(
        title='Arrests by Age',
        xaxis=dict(title='Age', tickvals=[x + bar_width / 2 for x in range(len(combined_categories_age))], ticktext=combined_categories_age),
        yaxis=dict(title='Number of Arrests'),
        legend=dict(x=0.51, y=0.99, bordercolor="Black", borderwidth=0.5),
        barmode='group',
        plot_bgcolor='rgba(255, 255, 255, 1)'
    )

    return fig


# Add callback for gender-based graph
@app.callback(
    Output('gender-evasion-graph', 'figure'),
    [Input('quarter-selector', 'value')]
)
def gender_graph(selected_quarter):
    # Get data for the selected quarter
    selected_gender_values = list(gender_data[selected_quarter].values())
    selected_categories_gender = list(gender_data[selected_quarter].keys())

    # Determine the previous quarter based on the selected quarter
    if selected_quarter == 'Q1':
        previous_quarter = 'Q4'
        previous_year = 2022  
        previous_data = last_quarter_2022_gender
    else:
        previous_quarter = 'Q' + str(int(selected_quarter[1]) - 1)
        previous_year = 2023
        previous_data = gender_data[previous_quarter]
        
        # If Q1 is selected, add the values from last_quarter_2022_gender to the previous year
        if previous_quarter == 'Q4':
            for gender_category, value in last_quarter_2022_gender.items():
                previous_data[gender_category] = value

    # Fetch the data for the previous quarter
    previous_gender_values = [previous_data.get(gender_category, 0) for gender_category in selected_categories_gender]

    # Combine data from the selected quarter and the previous quarter
    combined_gender_values = selected_gender_values + previous_gender_values
    combined_categories_gender = selected_categories_gender + list(previous_data.keys())

    # Define the width of each bar
    bar_width = 0.50

    # Define the x-coordinates for bars of each quarter
    x_selected = np.arange(len(selected_categories_gender))
    x_previous = [x + bar_width for x in x_selected]

    # Use Plotly for the graph
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_selected, y=selected_gender_values, name='Selected Quarter', marker_color='#CC0000', hovertemplate='<b>%{y}</b>'))
    fig.add_trace(go.Bar(x=x_previous, y=previous_gender_values, name='Previous Quarter', marker_color='#FFCCB3', hovertemplate='<b>%{y}</b>'))  # Update trace name

    # Customize layout
    fig.update_layout(
        title='Arrests by Gender',
        xaxis=dict(title='Gender', tickvals=[x + bar_width / 2 for x in range(len(combined_categories_gender))], ticktext=combined_categories_gender),
        yaxis=dict(title='Number of Arrests'),
        legend=dict(x=0.51, y=0.99, bordercolor="Black", borderwidth=0.5),
        barmode='group',
        plot_bgcolor='rgba(255, 255, 255, 1)'
    )

    return fig

# Callback to update the top stations graph
@app.callback(
    Output('top-stations-graph', 'figure'),
    [Input('quarter-selector', 'value')]
)
def update_top_stations_graph(selected_quarter):
    # Fetch the data for the selected quarter
    station_data = fetch_and_process_data_2(selected_quarter, None)
    
    # Extract station names and corresponding arrests
    station_names = list(station_data.keys())
    arrests = list(station_data.values())
    
    # Take top 10 stations based on arrests
    top_10_stations = station_names[:10]
    top_10_arrests = arrests[:10]
    
    # Create horizontal bar chart with a continuous color scale
    fig = go.Figure(go.Bar(
        x=top_10_arrests[::-1],
        y=top_10_stations[::-1],
        orientation='h',
        marker=dict(
            color=top_10_arrests[::-1],  # Map color to arrest counts
            colorscale='OrRd',
            )
        )
    )
    
    # Customize layout
    fig.update_layout(
        title='Top 10 Stations with Most Arrests',
        xaxis=dict(title='Number of Arrests'),
        yaxis=dict(title='Station'),
        margin=dict(l=150, r=20, t=70, b=70),
        height=500,
        plot_bgcolor='rgba(255, 255, 255, 1)'
    )
    
    return fig

# Callback to update the borough counts scatter plot
@app.callback(
    Output('borough-counts-graph', 'figure'),
    [Input('quarter-selector', 'value')]
)
def update_borough_counts_graph(selected_quarter):
    # Fetch the data for the selected quarter
    borough_data = fetch_and_process_data_3(selected_quarter, None)
    
    # Load the shapefile (update the path as necessary)
    shapefile_path = 'geo_export_b98d7ad7-d31a-4319-b877-72f88ebddf59.shp'
    gdf = gpd.read_file(shapefile_path)

    # Ensure the GeoDataFrame is in the right projection (latitude and longitude)
    gdf = gdf.to_crs(epsg=4326)

    # Convert the arrest counts dictionary to a DataFrame
    counts_df = pd.DataFrame(list(borough_data.items()), columns=['boro_name', 'arrest_counts'])

    # Make sure the borough names match between gdf and counts_df (case-sensitive)
    gdf['boro_name'] = gdf['boro_name'].str.upper()

    # Merge the GeoDataFrame with the arrest counts DataFrame
    merged_gdf = gdf.merge(counts_df, on='boro_name')

    # Plotting
    fig = go.Figure(go.Choroplethmapbox(
        geojson=merged_gdf.__geo_interface__,
        locations=merged_gdf.index,
        z=merged_gdf['arrest_counts'],
        colorscale='OrRd',
        zmin=0,
        zmax=max(merged_gdf['arrest_counts']),
        marker_opacity=0.6,
        marker_line_width=0,
        hoverinfo='text+z',
        text=merged_gdf['boro_name'] + '<br>' + 'Arrests: ' + merged_gdf['arrest_counts'].astype(str)
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=9,
        mapbox_center={"lat": 40.7128, "lon": -74.0060},
        margin={"r":30,"t":40,"l":30,"b":70},
        title='Arrest Counts by Borough',  # Title for the choropleth map
        height=480
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
