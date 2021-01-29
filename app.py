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

df = pd.read_csv("Subnational_total_final_energy_consumption_statistics.csv")
dff = preprocess_dataframe(df)
with open("nuts_level_1.geojson") as injson:
    geojson = json.load(injson)
with open("uk.geojson") as injson:
    uk_geojson = json.load(injson)
min_year, max_year = dff['Year'].min(), dff['Year'].max()
year_marks = {str(year): str(year)
              for year in dff['Year'].unique()}

def update_choropleth():
    total_uk_df = dff.groupby("Year").sum().reset_index()
    total_uk_df["Name"] = "United Kingdom"
    print(total_uk_df["All_Fuels_Total"])
    fig = px.choropleth_mapbox(total_uk_df, geojson=uk_geojson, locations="Name", color="All_Fuels_Total", featureidkey="properties.union", animation_frame="Year", color_continuous_scale=plotly.colors.diverging.Temps, range_color=[1000000, 2000000])
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=3.3, mapbox_center={"lat": 54.7, "lon": -3.43})
    fig.update_layout(plotting.CHOROPLETH_COLORS)
    return fig

def uk_total_time_series():
    total_uk_df = dff.groupby("Year").sum().reset_index()
    fig = px.line(
        total_uk_df,
        x="Year",
        y="All_Fuels_Total",
        range_y=[1000000, 2000000],
        color_discrete_sequence=[plotting.REGION_COLORS["United Kingdom"]],
    )
    fig.update_layout(plotting.PLOT_COLORS)
    # fig.update_yaxes(type='linear' if yaxis_type == 'Linear' else 'log')
    fig.update_traces(mode='markers+lines')
    fig.update_xaxes(showspikes=True)
    fig.update_yaxes(showspikes=True)
    fig.update_layout(hovermode="x")

    return fig

def uk_total_per_energy_source():
    min_y = 0
    total_uk_df = dff.groupby("Year").sum().reset_index()
    max_y = int(total_uk_df['All_Fuels_Total'].max())
    max_y = max_y + max_y*.05

    long_year_df = melt_dataframe(total_uk_df)
    fig = px.bar(
        long_year_df,
        x="Year",
        y="GWh",
        color="Energy type",
        color_discrete_map=plotting.ENERGY_SOURCE_COLORS,
        range_y=[min_y, max_y]
    )
    fig.update_xaxes(title_text="")

    fig.update_layout(plotting.PLOT_COLORS)
    fig.update_layout(hovermode="x")

    return fig



markdown_msg = """
Welcome to the interactive UK Energy Consumption dashboard! The purpose of this dashboard is to visualize and explore the UK's total final energy consumption from 2005 to 2018.

As you scroll down the dashboard, the scope will narrow and you'll be able to explore the United Kingdom's energy data in increasingly specific regions.

Sources:

- [Total final energy consumption at regional and local authority level: 2005 to 2018](https://www.gov.uk/government/statistics/total-final-energy-consumption-at-regional-and-local-authority-level-2005-to-2018)
- [UK NUTS Level 1 (2018) boundary data](https://geoportal.statistics.gov.uk/datasets/nuts-level-1-january-2018-super-generalised-clipped-boundaries-in-the-united-kingdom)
- [GitHub](https://github.com/chris-greening/UK-Energy-Consumption)

_Notice of Non-Affiliation and Disclaimer_: We are not affiliated, associated, authorized, endorsed by, or in any way officially connected with the UK government or any of its agencies/departments. The original datasets used by this dashboard are publicly available on the UK's [government website](https://www.gov.uk/) as provided by the [Department for Business, Energy, & Industrial Strategy](https://www.gov.uk/government/organisations/department-for-business-energy-and-industrial-strategy).
"""

external_stylesheets = ['https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

if not DEBUG:
    server = app.server

app.layout = html.Div(children = [
    html.Div(
        children=[
            html.Div(
                dcc.Graph(
                    id="choropleth",
                    figure=update_choropleth()
                )
            ),
        ]
    ),
    html.Div(
        children = [
            html.H1("United Kingdom Energy Consumption", style={"font-size": "6vh", "text-align": "center"}),
            dcc.Markdown(markdown_msg),
            html.Hr(),
            # html.H1("United Kingdom", style={"font-size": "6vh", "text-align": "center"}),
            html.Div(
                children=[
                    html.Div(
                        html.Div(
                            children = [
                                html.H3("Total energy consumption (GWh)"),
                                dcc.Markdown("Hover over a data point to analyze breakdown by energy source"),
                                dcc.Graph(
                                    id="uk-total-consumption-time-series",
                                    figure=uk_total_time_series(),
                                    hoverData={"points":[{"x": 2005}]}
                                )
                            ],
                            className="plot"
                        ),
                        className="col-xl-8"
                    ),
                    html.Div(
                        html.Div(
                            children=[
                                html.H3(id="total-energy-consumption-bar-header"),
                                dcc.Graph(
                                    id='total-energy-consumption-bar-plot',
                                )
                            ],
                            className="plot"
                        ),
                        className="col-xl-4",
                    ),
                ],
                className="row"
            ),
            html.Div(
                children=[
                    html.Div(
                        html.Div(
                            children=[
                                html.H3(
                                    "Total consumption per energy source in the UK (GWh)"),
                                dcc.RadioItems(
                                    id='total-type-line',
                                    options=[{'label': i, 'value': i}
                                             for i in ['Linear', 'Log']],
                                    value='Linear',
                                    labelStyle={'display': 'inline-block'},
                                ),
                                dcc.Graph(
                                    id="total-energy-usage",
                                    hoverData={"points": [{"x": 2005}]}
                                ),
                            ],
                            className="plot"
                        ),
                        className="col-xl-8 order-xl-12"
                    ),
                    html.Div(
                        html.Div(
                            children=[
                                html.H3(
                                    id="total-energy-consumption-circle-header"),
                                dcc.Graph(
                                    id='total-energy-consumption-percent-circle',
                                )
                            ],
                            className="plot"
                        ),
                        className="col-xl-4 order-xl-1",
                    ),
                ],
                className="row"
            ),
            # html.Div(
            #     children=[
            #         html.H3("Total energy consumption per energy source (GWh)"),
            #         dcc.Graph(
            #             figure=uk_total_per_energy_source()
            #         )
            #     ],
            #     className="plot"
            # ),
        ],
        className="container-fluid dash",
    ),
    html.Div(
        children=[
            html.Div(
                dcc.Graph(
                    id="all-regions-choropleth",
                )
            ),
            dcc.Slider(
                id='choropleth-year-slider',
                min=min_year,
                max=max_year,
                value=min_year,
                marks=year_marks,
                step=None,
            ),
        ]
    ),
    html.Div(
        children=[
            html.H1("NUTS Level 1 Statistical Regions", style={"font-size": "6vh", "text-align": "center"}),
            html.Div(
                children = [
                    html.Div(
                        html.Div(
                            children=[
                                html.H3(id="header-info"),
                                dcc.Graph(
                                    id='total-energy-consumption-bar',
                                ),
                            ],
                            className="plot"
                        ),
                        className="col-xl-6",
                    ),
                    html.Div(
                        html.Div(
                            children = [
                                html.H3(id="header-percentage-info"),
                                dcc.Graph(
                                    id='total-energy-consumption-percent',
                                ),
                            ],
                            className="plot"
                        ),
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
        ],
        className="container-fluid dash",
    ),
    html.Div(
        children = [
            dcc.Graph(
                id="region-choropleth"
            ),
            dcc.Slider(
                id='region-choropleth-year-slider',
                min=dff['Year'].min(),
                max=dff['Year'].max(),
                value=dff['Year'].min(),
                marks={str(year): str(year)
                       for year in dff['Year'].unique()},
                step=None,
            ),
        ]
    ),
    html.H1(id="region-info",
            style={"font-size": "6vh", "text-align": "center"}),
    html.Div(
        children=[
            dcc.Markdown(id="regional-markdown"),
            dcc.Markdown(
                "**Select a different region to visualize that regions data:**"),
            html.Div(
                dcc.Dropdown(
                    id='region-dropdown',
                    options=[{"label": val, "value": val}
                             for val in dff["Name"].unique()],
                    value='Wales'
                ),
                style={"width": "200px", "margin-bottom": "2%"}
            ),
            html.Hr(),
            html.H1("The regional level at a glance"),
            html.Div(
                children = [
                    html.Div(
                        html.Div(
                            children=[
                                html.H3("Total consumption per year"),
                                dcc.Graph(
                                    id="region-time-series-bar",
                                )
                            ],
                            className="plot"
                        ),
                        className="col-xl-6",
                    ),
                    html.Div(
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
                                ),
                            ],
                            className="plot"
                        ),
                        className="col-xl-6"
                    ),
                ],
                className="row"
            ),
            html.Div(
                html.Div(
                    html.Div(
                        children = [
                            html.H3("Cumulative rate of change per energy source"),
                            dcc.Graph(
                                id="cum-rate-of-change",
                            ),
                        ],
                        className="plot"
                    ),
                    className="col-xl-12"
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
            ),
        ],
        className="container-fluid dash",
    )
])


@app.callback(
    Output('all-regions-choropleth', 'figure'),
    Input('choropleth-year-slider', 'value')
)
def update_all_regions_choropleth(year_value):
    year_df = dff[dff["Year"] == year_value]
    fig = px.choropleth_mapbox(year_df, geojson=geojson, locations="Name", color="All_Fuels_Total", featureidkey="properties.nuts118nm",
                               range_color=(0, 250000), color_continuous_scale=plotly.colors.diverging.Temps)
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=3.3, mapbox_center={"lat": 54.7, "lon": -3.43})
    fig.update_layout(plotting.CHOROPLETH_COLORS)
    return fig

@app.callback(
    Output('uk-circle-percentage-info', 'children'),
    Input('total-energy-consumption-year-slider', 'value')
)
def update_circle_header(year_value):
    return f"Aggregate resource usage in the UK ({year_value})"

@app.callback(
    Output("total-energy-consumption-circle", "figure"),
    Input("total-energy-consumption-year-slider", "value")
)
def update_region_circle(year_value):
    year_df = dff[dff["Year"] == year_value]
    fig = px.pie(year_df, values="All_Fuels_Total", names="Name", hole=.5)
    fig.update_layout(plotting.PLOT_COLORS)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

@app.callback(
    Output("total-energy-consumption-bar-plot", "figure"),
    Input("uk-total-consumption-time-series", "hoverData")
)
def total_uk_energy_bar_plot(hoverData):
    year_value = hoverData['points'][0]['x']
    year_df = dff[dff["Year"] == year_value]
    year_df = year_df.groupby("Year").sum()
    long_total_df = melt_dataframe(year_df)
    fig = px.bar(
        long_total_df,
        x="Energy type",
        y="GWh",
        color="Energy type",
        color_discrete_map=plotting.ENERGY_SOURCE_COLORS,
        range_y=[0, 750000]
    )
    fig.update_layout(plotting.PLOT_COLORS)

    return fig

@app.callback(
    Output("total-energy-consumption-bar-header", "children"),
    Input("uk-total-consumption-time-series", "hoverData")
)
def update_consumption_bar_plot(hoverData):
    year_value = hoverData['points'][0]['x']
    return f"Totel energy consumption (GWh) per energy source ({year_value})"

@app.callback(
    Output("total-energy-consumption-circle-header", "children"),
    Input("total-energy-usage", "hoverData")
)
def update_percent_circle_header(hoverData):
    year_value = hoverData['points'][0]['x']
    return f"Totel percentage (%) per energy source ({year_value})"

@app.callback(
    Output("total-energy-consumption-percent-circle", "figure"),
    Input("total-energy-usage", "hoverData")
)
def update_percent_circle(hoverData):
    year_value = hoverData['points'][0]['x']
    year_df = dff[dff["Year"] == year_value]
    energy_df = year_df.groupby("Year").sum()
    melted_energy_df = melt_dataframe(energy_df)
    fig = px.pie(melted_energy_df, values="GWh", names="Energy type", color="Energy type",
                 hole=.5, color_discrete_map=plotting.ENERGY_SOURCE_COLORS)
    fig.update_layout(plotting.PLOT_COLORS)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False)

    return fig

@app.callback(
    Output('total-energy-usage', 'figure'),
    Input('total-type-line', 'value'),
)
def total_uk_energy_time_series(yaxis_type):
    year_df = dff.groupby("Year").sum()
    long_total_df = melt_dataframe(year_df.reset_index())
    fig = px.line(
        long_total_df,
        x="Year",
        y="GWh",
        color="Energy type",
        color_discrete_map=plotting.ENERGY_SOURCE_COLORS,
        log_y=True,
    )
    fig.update_layout(plotting.PLOT_COLORS)
    # fig.update_yaxes(type='linear' if yaxis_type == 'Linear' else 'log')
    fig.update_traces(mode='markers+lines')
    fig.update_xaxes(showspikes=True)
    fig.update_yaxes(showspikes=True)
    fig.update_yaxes(type='linear' if yaxis_type == 'Linear' else 'log')

    return fig

@app.callback(
    Output('region-choropleth', 'figure'),
    [Input('region-dropdown', 'value'),
     Input("region-choropleth-year-slider", "value")]
)
def update_region_choropleth(location, year_value):
    region_df = dff[dff["Name"] == location]
    year_df = region_df[region_df["Year"] == year_value]
    region_geojson = construct_regional_geojson(location, geojson)
    max_energy = region_df["All_Fuels_Total"].max()
    fig = px.choropleth_mapbox(year_df, geojson=region_geojson, locations="Name", color="All_Fuels_Total", featureidkey="properties.nuts118nm",
                               range_color=(0, max_energy), color_continuous_scale=plotly.colors.diverging.Temps)
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=3.7, mapbox_center={"lat": region_geojson["features"][0]["properties"]["lat"], "lon": region_geojson["features"][0]["properties"]["long"]})
    fig.update_layout(plotting.CHOROPLETH_COLORS)
    return fig

@app.callback(
    [Output("table", "data"), Output("table", "columns")],
     Input('region-dropdown', 'value')
)
def update_table(location):
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
    return f"Total energy consumption per region ({year_value})"

@app.callback(
    Output('header-percentage-info', 'children'),
    Input('total-energy-consumption-year-slider', 'value')
)
def update_percentage_header(year_value):
    return f"Percentage of energy consumption per region ({year_value})"

@app.callback(
    Output('region-info', 'children'),
    Input('region-dropdown', 'value')
)
def update_region_bar_header(location):
    return f"{location}"

@app.callback(
    Output('regional-markdown', 'children'),
    Input('region-dropdown', 'value')
)
def update_regional_markdown(location):
    return construct_regional_markdown(location)

@app.callback(
    Output('region-time-series-bar', 'figure'),
    Input('region-dropdown', 'value')
)
def update_region_bar(location):
    region_df = dff[dff['Name'] == location]
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
    [Input('region-dropdown', 'value'),
    Input('yaxis-type-line', 'value')],
)
def update_region_line(location, yaxis_type):
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
    Input('region-dropdown', 'value')
)
def update_cum_rate_of_change(location):
    year_change_df = dp.calculate_rate_of_change_df(location, dff)

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
