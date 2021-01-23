import datetime

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
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

markdown_msg = """
[Source](https://www.gov.uk/government/statistics/total-final-energy-consumption-at-regional-and-local-authority-level-2005-to-2018)

[GitHub](https://github.com/chris-greening/UK-Energy-Consumption)

This data represents the total energy consumption at the regional level of the UK between 2005 and 2018.

Use the Year slider to slice a different year of data for the _Total Energy Consumption_ and _Percentage of energy source consumption plots_.
"""

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# server = app.server

app.layout = html.Div(
    children = [
        html.H1("UK Energy Consumption"),
        dcc.Markdown(markdown_msg),
        html.Div(
            children = [
                html.H3(id="header-info"),
                dcc.Graph(
                        id='total-energy-consumption-bar',
                        hoverData={'points': [{'curveNumber': 2, 'pointNumber': 2, 'pointIndex': 2,
                                           'x': 'Greater London', 'y': 36021.306273, 'label': 'Greater London', 'value': 36021.306273}]},
                        style={'height': '30vh'}
                    ),
            ],
            className="top-plot",
            style={"float":"left"}
        ),
        html.Div(
            children = [
                html.H3(id="header-percentage-info"),
                dcc.Graph(
                    id='total-energy-consumption-percent',
                    style={'height': '30vh'}
                ),
            ],
            className="top-plot",
        ),
        dcc.Slider(
            id='total-energy-consumption-year-slider',
            min=dff['Year'].min(),
            max=dff['Year'].max(),
            value=dff['Year'].max(),
            marks={str(year): str(year)
                   for year in dff['Year'].unique()},
            step=None
        ),
        html.H6("Year", style={"text-align": "center"}),
        html.H1(id="region-info"),
        html.Div(
            children=[
                dcc.Markdown(
                    "Hover over a region in the _Total Energy Consumption_ plot above to analyze resource usage as a function of time"),
                html.H3("Total consumption per year"),
                dcc.Graph(
                    id="region-time-series-bar",
                    style={'height': '30vh'}
                ),
            ],
            className="middle-plot",
            style={"float": "left"}
        ),
        html.Div(
            children = [
                html.H3("Energy source consumption per year"),
                dcc.RadioItems(
                    id='yaxis-type-line',
                    options=[{'label': i, 'value': i}
                             for i in ['Linear', 'Log']],
                    value='Linear',
                    labelStyle={'display': 'inline-block'}
                ),
                dcc.Graph(
                    id="region-time-series-scatter",
                    style={'height': '30vh'}
                ),
            ],
            className="middle-plot"
        ),
        html.Div(
            children = [
                html.H3("Cumulative rate of change per energy source"),
                html.Div(
                    dcc.Graph(
                        id="cum-rate-of-change",
                        style={'height': '30vh'}
                    ),
                    # style={"padding": "0% 25%"}
                ),
            ],
            # className="bottom-plot"
        ),
        html.Div(
            children=[
                html.H3("Energy resource usage by the numbers"),
                html.Div(
                    dash_table.DataTable(
                        id="table",
                        data=[],
                        style_cell={'textAlign': 'center'},
                        style_data_conditional=[
                            {
                                'if': {
                                    'column_id': 'Year',
                                },
                                'fontWeight': 'bold',
                                'backgroundColor': '#e8e8e8',
                            },
                        ]
                    ),
                    # style={"padding": "0% 25%"}
                )
            ],
            # className="bottom-plot",
            # style={"float": "left"}
        ),
    ],
    id="dash"
)

@app.callback(
    [Output("table", "data"), Output("table", "columns")],
    Input('total-energy-consumption-bar', 'hoverData')
)
def update_table(hoverData):
    location = hoverData['points'][0]['x']
    region_df = dff[dff["Name"] == location]
    descriptive_columns = ["Year"]

    totals_columns = [
        col for col in region_df.columns if "Total" in col]
    all_columns = descriptive_columns + totals_columns
    all_columns = [col for col in all_columns if col in region_df.columns]
    region_df = region_df[all_columns]
    region_df = region_df.rename(
        columns={col: col.replace("_Total", "") + " (GWh)" for col in region_df.columns if "Year" not in col})
    region_df = region_df.round(2)
    region_df = region_df.rename(columns = {"All_Fuels (GWh)": "Total (GWh)"})
    return region_df.to_dict("records"), [{"name": i, "id": i} for i in region_df.columns]

@app.callback(
    Output('total-energy-consumption-percent', 'figure'),
    Input('total-energy-consumption-year-slider', 'value')
)
def update_graph_percent(year_value):

    year_df = dff[dff["Year"] == year_value]
    total_consumption_df = year_df.groupby("Name").sum()
    highest_region = total_consumption_df[total_consumption_df["All_Fuels_Total"]
                                      == total_consumption_df["All_Fuels_Total"].max()].index
    highest_region_df = year_df[year_df["Name"] == highest_region[0]]
    adjusted_df = year_df.copy()
    adjusted_df.iloc[:, 3:-4] = adjusted_df.iloc[:, 3:-
                                                4].div(adjusted_df["All_Fuels_Total"], axis=0)
    long_adjusted_sum_df = pd.melt(adjusted_df, id_vars=["Year", "Name"], value_vars=[
                                col for col in highest_region_df.columns if "Total" in col])
    long_adjusted_sum_df = long_adjusted_sum_df.rename(
        columns={"variable": "Energy type", "value": "%"})
    long_adjusted_sum_df["Energy type"] = long_adjusted_sum_df["Energy type"].str.replace(
        "_Total", "")
    long_adjusted_sum_df["%"] = long_adjusted_sum_df["%"] * 100

    fig = px.bar(
        long_adjusted_sum_df,
        x="Name",
        y="%",
        color="Energy type",
        animation_frame="Year",
        range_y=[0, 100],
        color_discrete_map=energy_source_colors
    )
    fig.update_yaxes(title_text="% Usage")
    fig.update_xaxes(title_text="")
    fig.update_layout({
        'plot_bgcolor': '#F2F8FF',
        'paper_bgcolor': '#F2F8FF'
    })
    return fig

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
    fig.update_xaxes(title_text="")

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
    return f"Total Energy Consumption ({year_value})"


@app.callback(
    Output('header-percentage-info', 'children'),
    Input('total-energy-consumption-year-slider', 'value')
)
def update__percentage_header(year_value):
    return f"Percentage of energy source consumption ({year_value})"

@app.callback(
    Output('region-info', 'children'),
    Input('total-energy-consumption-bar', 'hoverData')
)
def update_region_bar_header(hoverData):
    return f"{hoverData['points'][0]['x']}"

@app.callback(
    Output('region-time-series-bar', 'figure'),
    Input('total-energy-consumption-bar', 'hoverData')
)
def update_region_bar(hoverData):
    region_df = dff[dff['Name'] == hoverData['points'][0]['x']]
    long_region_df = melt_dataframe(region_df)

    fig = px.bar(
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


@app.callback(
    Output('region-time-series-scatter', 'figure'),
    [Input('total-energy-consumption-bar', 'hoverData'),
     Input('yaxis-type-line', 'value'),
    ]
)
def update_region_line(hoverData, yaxis_type):
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
    fig.update_yaxes(type='linear' if yaxis_type == 'Linear' else 'log')
    fig.update_traces(mode='markers+lines')

    return fig

@app.callback(
    Output('cum-rate-of-change', 'figure'),
    Input('total-energy-consumption-bar', 'hoverData')
)
def update_cum_rate_of_change(hoverData):
    region_df = dff[dff["Name"] == hoverData['points'][0]['x']]
    region_df = region_df.drop(columns=["Name", "Unit"])
    region_df = region_df.set_index("Year")

    year_change_df = region_df.pct_change().cumsum()
    year_change_df *= 100

    year_change_df = melt_dataframe(year_change_df.reset_index())

    year_change_df["Year"] = year_change_df["Year"].apply(
        lambda x: datetime.datetime.strptime(str(x), "%Y"))

    fig = px.line(
        year_change_df,
        x="Year",
        y="GWh",
        color="Energy type",
        color_discrete_map=energy_source_colors,
        range_x=[datetime.date(2006, 1, 1), datetime.date(2018, 1, 1)]
    )
    fig.update_layout({
        'plot_bgcolor': '#F2F8FF',
        'paper_bgcolor': '#F2F8FF'
    })
    fig.update_traces(mode='markers+lines')
    fig.update_yaxes(title_text="Cumulative % change")

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
