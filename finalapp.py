import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dash import Dash, html, dcc, Input, Output
import plotly.graph_objects as go
import numpy as np

#Refer: https://www.nyc.gov/site/nypd/stats/reports-analysis/subway-fare-evasion.page

app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Subway Fare Evasion Dashboard"),
    html.H2("Developed by Hrithik Shukla (March 21, 2024)"),
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
    
    dcc.Graph(id='fare-evasion-graph', style={'width': '33%', 'display': 'inline-block'}),
    dcc.Graph(id='age-evasion-graph', style={'width': '33%', 'display': 'inline-block'}),
    dcc.Graph(id='gender-evasion-graph', style={'width': '33%', 'display': 'inline-block'}),
    dcc.Graph(id='top-stations-graph', style={'width': '50%', 'display': 'inline-block'}),
    dcc.Graph(id='borough-counts-graph', style={'width': '50%', 'display': 'inline-block'})
])
def fetch_and_process_data(quarter, year):
    # URL of the NYPD Fare Evasion webpage
    url = "https://www.nyc.gov/site/nypd/stats/reports-analysis/subway-fare-evasion.page"
    response = requests.get(url, verify=False)

    # Send a GET request to the URL
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the download link for the Excel file for the selected quarter and year
        download_link = None
        for a_tag in soup.find_all("a"):
            if f"Fare Evasion Arrests - {quarter}, {year}" in a_tag.text:
                download_link = a_tag.get("href")
                break

        # If the link was found, create the absolute URL
        if download_link:
            absolute_download_link = urljoin(url, download_link)
        else:
            return {}, {}, {}, {}, {}, {}  # Return empty dicts if data is not found

        # Calculate the previous quarter and year for comparison
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        prev_quarter_index = (quarters.index(quarter) - 1) % len(quarters)
        prev_year = year if prev_quarter_index != 3 else str(int(year) - 1)
        prev_quarter = quarters[prev_quarter_index]

        # Find the download link for the Excel file for the previous quarter
        prev_download_link = None
        for a_tag in soup.find_all("a"):
            if f"Fare Evasion Arrests - {prev_quarter}, {prev_year}" in a_tag.text:
                prev_download_link = a_tag.get("href")
                break

        # If the link was found, create the absolute URL
        if prev_download_link:
            old_download_link = urljoin(url, prev_download_link)
        else:
            return {}, {}, {}, {}, {}, {}  # Return empty dicts if data is not found

        # Define categories
        race = ["AMER IND", "ASIAN/PAC.ISL", "BLACK", "HISPANIC", "UNKNOWN", "WHITE"]
        age_bracket = ["10 - 17", "18 - 24", "25 - 40", "41 - 59", "60+"]
        gender = ["MALE", "FEMALE", "UNKNOWN"]

        # Function to process and return the dictionary
        def process_data(download_link, sheet_name="Citywide", categories=None):
            df = pd.read_excel(download_link, sheet_name=sheet_name)
            data_dict = {r: 0 for r in categories}
            for index, row in df.iterrows():
                if row['Unnamed: 2'] in categories:
                    data_dict[row['Unnamed: 2']] += int(row['Unnamed: 3'])
            return data_dict

        # Process data for the selected and previous quarters for all categories
        race_dict = process_data(absolute_download_link, categories=race)
        prev_race_dict = process_data(old_download_link, categories=race)
        age_dict = process_data(absolute_download_link, categories=age_bracket)
        prev_age_dict = process_data(old_download_link, categories=age_bracket)
        gender_dict = process_data(absolute_download_link, categories=gender)
        prev_gender_dict = process_data(old_download_link, categories=gender)

        return race_dict, prev_race_dict, age_dict, prev_age_dict, gender_dict, prev_gender_dict


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
    
    # Create horizontal bar chart
    fig = go.Figure(go.Bar(
        x=top_10_arrests[::-1],
        y=top_10_stations[::-1],
        orientation='h',
        marker_color='lightcoral'
    ))
    
    # Customize layout
    fig.update_layout(
        title='Top 10 Stations with Most Arrests',
        xaxis=dict(title='Number of Arrests'),
        yaxis=dict(title='Station'),
        margin=dict(l=150, r=20, t=70, b=70),
        height=600
    )
    
    return fig

# Update the existing callback for race-based graph
@app.callback(
    Output('fare-evasion-graph', 'figure'),
    [Input('quarter-selector', 'value'),
     Input('year-selector', 'value')]
)
def update_graph(selected_quarter, selected_year):
    race_dict, prev_race_dict, _, _, _, _ = fetch_and_process_data(selected_quarter, selected_year)
    race_values = list(race_dict.values())
    prev_race_values = list(prev_race_dict.values())
    categories_race = list(race_dict.keys())
    
    # Sort the data in descending order by current quarter values for visualization
    sorted_data = sorted(zip(race_values, prev_race_values, categories_race), reverse=True)
    sorted_race_values, sorted_prev_race_values, sorted_categories_race = zip(*sorted_data)

    # Use Plotly for the graph
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sorted_categories_race, y=sorted_race_values, name='This Quarter', marker_color='lightblue'))
    fig.add_trace(go.Bar(x=sorted_categories_race, y=sorted_prev_race_values, name='Previous Quarter', marker_color='lightcoral'))
    
    # Customize layout
    fig.update_layout(
        title='Arrests by Race',
        xaxis=dict(title='Race'),
        yaxis=dict(title='Number of Arrests'),
        legend=dict(x=0.51, y=0.99, bordercolor="Black", borderwidth=0.5),
        barmode='group'
    )
    
    return fig

# Add callback for age-based graph
@app.callback(
    Output('age-evasion-graph', 'figure'),
    [Input('quarter-selector', 'value'),
     Input('year-selector', 'value')]
)
def update_age_graph(selected_quarter, selected_year):
    _, _, age_dict, prev_age_dict, _, _ = fetch_and_process_data(selected_quarter, selected_year)  # Assuming the data is fetched similarly for age as well
    age_values = list(age_dict.values())
    prev_age_values = list(prev_age_dict.values())
    categories_age = list(age_dict.keys())
    
    # Use Plotly for the graph
    fig = go.Figure()
    fig.add_trace(go.Bar(x=categories_age, y=age_values, name='This Quarter', marker_color='lightblue'))
    fig.add_trace(go.Bar(x=categories_age, y=prev_age_values, name='Previous Quarter', marker_color='lightcoral'))
    
    # Customize layout
    fig.update_layout(
        title='Arrests by Age Group',
        xaxis=dict(title='Age Bracket'),
        yaxis=dict(title='Number of Arrests'),
        legend=dict(x=0.51, y=0.99, bordercolor="Black", borderwidth=0.5),
        barmode='group'
    )
    
    return fig

# Add callback for gender-based graph
@app.callback(
    Output('gender-evasion-graph', 'figure'),
    [Input('quarter-selector', 'value'),
     Input('year-selector', 'value')]
)
def update_gender_graph(selected_quarter, selected_year):
    _, _, _, _, gender_dict, prev_gender_dict = fetch_and_process_data(selected_quarter, selected_year)  # Assuming the data is fetched similarly for gender as well
    gender_values = list(gender_dict.values())
    prev_gender_values = list(prev_gender_dict.values())
    categories_gender = list(gender_dict.keys())
    
    # Use Plotly for the graph
    fig = go.Figure()
    fig.add_trace(go.Pie(labels=categories_gender, values=gender_values, marker_colors=['lightblue', 'lightcoral']))
    
    # Customize layout
    fig.update_layout(
        title='Arrests by Gender',
        legend=dict(x=0.80, y=0.99, bordercolor="Black", borderwidth=0.5),
    )
    
    # Clear existing annotations
    fig.update_layout(annotations=[])
    
    # Add annotations
    fig.add_annotation(text='This Quarter', x=0.18, y=0.5, font_size=10, showarrow=False)

    return fig

# Callback to update total arrests and percent change
@app.callback(
    [Output('total-arrests-container', 'children'),
     Output('percent-change-container', 'children')],
    [Input('quarter-selector', 'value'),
     Input('year-selector', 'value')]
)
def update_totals(selected_quarter, selected_year):
    race_dict, prev_race_dict, _, _, _, _ = fetch_and_process_data(selected_quarter, selected_year)
    total_arrests = sum(race_dict.values())
    prev_total_arrests = sum(prev_race_dict.values())
    
    # Calculate percent change
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
                html.H2(f"{total_arrests:,}", style={'font-size': '32px', 'color': 'blue'})
            ], style={'width': '50%', 'display': 'inline-block', 'text-align': 'center'}),

            html.Div([
                html.H2("Percent Change", style={'font-size': '24px', 'color': 'black'}),
                html.H2(percent_change_str, style={'font-size': '32px', 'color': percent_change_color})
            ], style={'width': '50%', 'display': 'inline-block', 'text-align': 'center'})
        ], style={'text-align': 'center', 'margin-bottom': '20px'}),
        ''
    )
# Callback to update the borough counts scatter plot
@app.callback(
    Output('borough-counts-graph', 'figure'),
    [Input('quarter-selector', 'value')]
)
def update_borough_counts_graph(selected_quarter):
    # Fetch the data for the selected quarter
    borough_data = fetch_and_process_data_3(selected_quarter, None)
    
    # Extract borough names and corresponding counts
    borough_names = list(borough_data.keys())
    counts = list(borough_data.values())
    
    # Define marker size and color based on counts
    max_marker_size = 40  # Maximum size for markers
    marker_sizes = [min(count * 0.5, max_marker_size) for count in counts]  # Adjust size based on counts, with a maximum size limit
    marker_colors = ['lightcoral' if count > 300 else 'lightblue' for count in counts]  # Red if count > 300, else blue
    
    # Create scatter plot
    fig = go.Figure(go.Scatter(
        x=counts,
        y=borough_names,
        mode='markers',
        marker=dict(color=marker_colors, size=marker_sizes),  # Adjust marker color and size
        name='Borough Counts'
    ))
    
    # Customize layout
    fig.update_layout(
        title='Arrest Counts by Borough',
        xaxis=dict(title='Counts'),
        yaxis=dict(title='Borough'),
        margin=dict(l=150, r=20, t=70, b=70),
        height=len(borough_names) * 90 + 150  # Adjust height based on the number of boroughs
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
