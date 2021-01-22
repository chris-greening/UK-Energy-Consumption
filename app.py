import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
from plotly.graph_objs import *
import pandas as pd

from data_processing import preprocess_dataframe, melt_dataframe

def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr(
            [
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])

df = pd.read_csv("Subnational_total_final_energy_consumption_statistics.csv")
dff = preprocess_dataframe(df)
energy_source_colors = {
    "Coal": '#525B76',
    "Manufactured": '#F4A259',
    "Petroleum": '#7A89C2',
    "Gas": '#F9B5AC',
    "Electricity": '#EE7674',
    "Bioenergy": '#9DBF9E',
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    children = [
        html.Div(
            children = [
                html.H2(id="header-info"),
                dcc.Graph(
                        id='total-energy-consumption-bar',
                    hoverData={'points': [{'curveNumber': 2, 'pointNumber': 2, 'pointIndex': 2,
                                           'x': 'Greater London', 'y': 36021.306273, 'label': 'Greater London', 'value': 36021.306273}]},
                        style={'height': '60vh'}
                    ),
                dcc.Slider(
                        id='total-energy-consumption-year-slider',
                        min=dff['Year'].min(),
                        max=dff['Year'].max(),
                        value=dff['Year'].max(),
                        marks={str(year): str(year) for year in dff['Year'].unique()},
                        step=None
                    )
            ],
            className="top-plot"
        ),
        html.Div(
            children = [
                html.H2(id="region-info"),
                dcc.Graph(
                    id="region-time-series-bar",
                    style={'height': '30vh'}
                ),
                dcc.Graph(
                    id="region-time-series-scatter",
                    style={'height': '30vh'}
                ),
            ],
            className="top-plot"
        ),
    ],
    id="dash"
)


@app.callback(
    Output('total-energy-consumption-bar', 'figure'),
    Input('total-energy-consumption-year-slider', 'value')
)
def update_graph(year_value):
    min_y = 0
    max_y = int(dff.groupby(["Year", "Name"]).sum().max()['All_Fuels_Total'])
    max_y = max_y + max_y*.05

    year_df = dff[dff["Year"] == year_value]
    long_year_df = melt_dataframe(year_df)
    fig = px.bar(
        long_year_df,
        x="Name",
        y="GWh",
        color="Energy type",
        color_discrete_map=energy_source_colors,
        range_y=[min_y, max_y]
    )
    fig.update_layout({
        'plot_bgcolor': '#F2F8FF',
        'paper_bgcolor': '#F2F8FF'
    })
    return fig

@app.callback(
    Output('header-info', 'children'),
    Input('total-energy-consumption-year-slider', 'value')
)
def update_header(year_value):
    return f"UK Energy Consumption ({year_value})"

@app.callback(
    Output('region-info', 'children'),
    Input('total-energy-consumption-bar', 'hoverData')
)
def update_region_header(hoverData):
    return f"{hoverData['points'][0]['x']} Energy Consumption"

@app.callback(
    Output('region-time-series-bar', 'figure'),
    Input('total-energy-consumption-bar', 'hoverData')
)
def update_region_time_series(hoverData):
    region_df = dff[dff['Name'] == hoverData['points'][0]['x']]
    long_region_df = melt_dataframe(region_df)

    title = f"Energy consumption time series for {hoverData['points'][0]['x']}"
    fig = px.bar(
            long_region_df,
            x="Year",
            y="GWh",
            color="Energy type",
            title=title,
            color_discrete_map=energy_source_colors,
        )
    fig.update_layout({
        'plot_bgcolor': '#F2F8FF',
        'paper_bgcolor': '#F2F8FF'
    })
    return fig


@app.callback(
    Output('region-time-series-scatter', 'figure'),
    Input('total-energy-consumption-bar', 'hoverData')
)
def update_region_time_series(hoverData):
    region_df = dff[dff['Name'] == hoverData['points'][0]['x']]
    long_region_df = melt_dataframe(region_df)

    title = f"Energy consumption time series for {hoverData['points'][0]['x']}"
    fig = px.line(
        long_region_df,
        x="Year",
        y="GWh",
        color="Energy type",
        color_discrete_map=energy_source_colors,
    )
    fig.update_layout({
        'plot_bgcolor': '#F2F8FF',
        'paper_bgcolor': '#F2F8FF'
    })
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
