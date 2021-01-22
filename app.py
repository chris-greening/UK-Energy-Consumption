import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

from data_processing import preprocess_dataframe, melt_total_dataframe

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

app.layout = html.Div([
    html.Div([
        dcc.Graph(
                id='total-energy-consumption-bar',
                hoverData={'points': [{'customdata': 'South East'}]}
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
        id="bar-plot"),
    ],
    className="dash"
)


@app.callback(
    Output('total-energy-consumption-bar', 'figure'),
    Input('total-energy-consumption-year-slider', 'value')
)
def update_graph(year_value):
    min_y = 0
    max_y = int(dff.groupby(["Year", "Name"]).sum().max())

    year_df = dff[dff["Year"] == year_value]
    long_year_df = melt_total_dataframe(year_df)
    fig = px.bar(
        long_year_df,
        x="Name",
        y="GWh",
        color="Energy type",
        color_discrete_map=energy_source_colors,
        range_y=[min_y, max_y]
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
