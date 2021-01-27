import datetime
import json

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly
import pandas as pd

from data_processing import preprocess_dataframe, melt_dataframe, construct_regional_geojson, click_location, construct_regional_markdown
import data_processing as dp
import plotting

DEBUG=True

# @app.callback(
#     Output('choropleth', 'figure'),
#     Input('total-energy-consumption-year-slider', 'value')
# )
def update_choropleth():
    fig = px.choropleth_mapbox(dff, geojson=geojson, locations="Name", color="All_Fuels_Total", featureidkey="properties.nuts118nm", animation_frame="Year",
                               range_color=(0, 250000), color_continuous_scale=plotly.colors.diverging.Temps)
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=3.3, mapbox_center={"lat": 54.7, "lon": -3.43})
    fig.update_layout(plotting.PLOT_COLORS)
    return fig

df = pd.read_csv("Subnational_total_final_energy_consumption_statistics.csv")
dff = preprocess_dataframe(df)
with open("nuts_level_1.geojson") as injson:
    geojson = json.load(injson)


markdown_msg = """
[Dataset](https://www.gov.uk/government/statistics/total-final-energy-consumption-at-regional-and-local-authority-level-2005-to-2018)

[UK NUTS Level 1 (2018) GeoJSON](https://geoportal.statistics.gov.uk/datasets/nuts-level-1-january-2018-super-generalised-clipped-boundaries-in-the-united-kingdom)

[GitHub](https://github.com/chris-greening/UK-Energy-Consumption)

This data represents the total energy consumption at the regional level of the UK between 2005 and 2018.

Use the Year slider to slice a different year of data .
"""

external_stylesheets = ['https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

if not DEBUG:
    server = app.server

app.layout = html.Div(children = [
    html.Div(
        html.Div(
            dcc.Loading(
                dcc.Graph(
                    id="choropleth",
                    figure=update_choropleth()
                )
            ),
            # className="col-xl-12",
        ),
        # className="row"
    ),
    html.Div(
        children = [
            html.H1("UK Energy Consumption"),
            dcc.Markdown(markdown_msg),
            html.Div(
                children = [
                    html.Div(
                        children = [
                            html.H3(id="header-info"),
                            dcc.Graph(
                                id='total-energy-consumption-bar',
                                clickData={'points': [{'x': 'London'}]},
                                className="plot"
                            ),
                        ],
                        className="col-xl-6",
                    ),
                    html.Div(
                        children = [
                            html.H3(id="header-percentage-info"),
                            dcc.Graph(
                                id='total-energy-consumption-percent',
                                className="plot"
                            )
                        ],
                        className="col-xl-6",
                    ),
                ],
                className="row"
            ),
            html.Div(
                html.Div(
                    dcc.Slider(
                        id='total-energy-consumption-year-slider',
                        min=dff['Year'].min(),
                        max=dff['Year'].max(),
                        value=dff['Year'].min(),
                        marks={str(year): str(year)
                            for year in dff['Year'].unique()},
                        step=None,
                    ),
                    className="col-xl-12"
                ),
                className="row"
            ),
            html.H6("Year", style={"text-align": "center"}),
            html.H1(id="region-info"),
            dcc.Markdown(id="regional-markdown"),
            dcc.Graph(
                id="region-choropleth"
            ),
            dcc.Markdown(
                "Click a region in the _Total Energy Consumption_ plot above to analyze resource usage as a function of time"),
            html.Div(
                children = [
                    html.Div(
                        children=[
                            html.H3("Total consumption per year"),
                            dcc.Graph(
                                id="region-time-series-bar",
                                className="plot"
                            )
                        ],
                        className="col-xl-6",
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
                                className="plot"
                            ),
                        ],
                        className="col-xl-6"
                    ),
                ],
                className="row"
            ),
            html.Div(
                html.Div(
                    children = [
                        html.H3("Cumulative rate of change per energy source"),
                        dcc.Graph(
                            id="cum-rate-of-change",
                        ),
                    ],
                    className="col-xl-12 plot"
                ),
                className="row"
            ),
            html.Div(
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
                        )
                    ],
                    className="col-xl-12"
                ),
                className="row",
                style={"margin-top": "3%"}
            )
        ],
        id="dash",
        className="container-fluid",
        style={"max-width": "1500px",  "background-color": "#F2F8FF"}
    )
])


@app.callback(
    Output('region-choropleth', 'figure'),
    Input('total-energy-consumption-bar', 'clickData')
)
def update_region_choropleth(clickData):
    location = click_location(clickData)
    region_df = dff[dff["Name"] == location]
    region_geojson = construct_regional_geojson(location, geojson)
    max_energy = region_df["All_Fuels_Total"].max()
    fig = px.choropleth_mapbox(region_df, geojson=region_geojson, locations="Name", color="All_Fuels_Total", featureidkey="properties.nuts118nm", animation_frame="Year",
                               range_color=(0, max_energy), color_continuous_scale=plotly.colors.diverging.Temps)
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=3.7, mapbox_center={"lat": region_geojson["features"][0]["properties"]["lat"], "lon": region_geojson["features"][0]["properties"]["long"]})
    fig.update_layout(plotting.PLOT_COLORS)
    return fig

@app.callback(
    [Output("table", "data"), Output("table", "columns")],
     Input('total-energy-consumption-bar', 'clickData')
)
def update_table(clickData):
    location = click_location(clickData)
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

    long_adjusted_sum_df = dp.calculate_energy_proportion_df(year_value, dff)

    fig = px.bar(
        long_adjusted_sum_df,
        x="Name",
        y="%",
        color="Energy type",
        animation_frame="Year",
        range_y=[0, 100],
        color_discrete_map=plotting.ENERGY_SOURCE_COLORS
    )
    fig.update_yaxes(title_text="% Usage")
    fig.update_xaxes(title_text="")
    fig.update_layout(plotting.PLOT_COLORS)
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
        color_discrete_map=plotting.ENERGY_SOURCE_COLORS,
        range_y=[min_y, max_y]
    )
    fig.update_xaxes(title_text="")

    fig.update_layout(plotting.PLOT_COLORS)
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
    Input('total-energy-consumption-bar', 'clickData')
)
def update_region_bar_header(clickData):
    return f"{click_location(clickData)}"

@app.callback(
    Output('regional-markdown', 'children'),
    Input('total-energy-consumption-bar', 'clickData')
)
def update_regional_markdown(clickData):
    location = click_location(clickData)
    return construct_regional_markdown(location)

@app.callback(
    Output('region-time-series-bar', 'figure'),
    Input('total-energy-consumption-bar', 'clickData')
)
def update_region_bar(clickData):
    region_df = dff[dff['Name'] == click_location(clickData)]
    long_region_df = melt_dataframe(region_df)

    fig = px.bar(
            long_region_df,
            x="Year",
            y="GWh",
            color="Energy type",
            color_discrete_map=plotting.ENERGY_SOURCE_COLORS,
        )
    fig.update_layout(plotting.PLOT_COLORS)
    return fig


@app.callback(
    Output('region-time-series-scatter', 'figure'),
    [Input('total-energy-consumption-bar', 'clickData'),
    Input('yaxis-type-line', 'value')],
)
def update_region_line(clickData, yaxis_type):
    location = click_location(clickData)
    region_df = dff[dff['Name'] == location]
    long_region_df = melt_dataframe(region_df)

    title = f"Energy consumption time series for {location}"
    fig = px.line(
        long_region_df,
        x="Year",
        y="GWh",
        color="Energy type",
        color_discrete_map=plotting.ENERGY_SOURCE_COLORS,
    )
    fig.update_layout(plotting.PLOT_COLORS)
    fig.update_yaxes(type='linear' if yaxis_type == 'Linear' else 'log')
    fig.update_traces(mode='markers+lines')
    fig.update_xaxes(showspikes=True)
    fig.update_yaxes(showspikes=True)

    return fig

@app.callback(
    Output('cum-rate-of-change', 'figure'),
    Input('total-energy-consumption-bar', 'clickData')
)
def update_cum_rate_of_change(clickData):
    year_change_df = dp.calculate_rate_of_change_df(clickData, dff)

    fig = px.line(
        year_change_df,
        x="Year",
        y="GWh",
        color="Energy type",
        color_discrete_map=plotting.ENERGY_SOURCE_COLORS,
        range_x=[datetime.date(2006, 1, 1), datetime.date(2018, 1, 1)]
    )
    fig.update_layout(plotting.PLOT_COLORS)
    fig.update_traces(mode='markers+lines')
    fig.update_yaxes(title_text="Cumulative % change")
    fig.update_xaxes(showspikes=True)
    fig.update_yaxes(showspikes=True)

    return fig

if __name__ == '__main__':
    app.run_server(debug=DEBUG)
