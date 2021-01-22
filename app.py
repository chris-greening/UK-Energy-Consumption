import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

from filter_tools import filter_energy_type

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

def return_years_df(df: pd.DataFrame):
    """Return a MultiIndex'd DataFrame based on years"""
    df = df[df["UNIT"] == "GWh"]
    df = df[df["NAME"].str.isupper()]

    # Drop the LAUA column
    df = df.drop(columns=["LAUA"])

    # Reorder the columns
    descriptive_columns = ["YEAR", "NAME", "UNIT"]
    other_columns = [col for col in df.columns if col not in descriptive_columns]
    all_columns = descriptive_columns + other_columns
    df = df[all_columns]

    # Title the columns and region names
    df = df.rename(columns={col: col.title() for col in all_columns})
    df = df.rename(columns={
        "Bioenergy_All": "Bioenergy_Total",
        "Total_Coal": "Coal_Total",
        "Total_Manufactured": "Manufactured_Total",
        "Total_Petroleum": "Petroleum_Total"
    })
    df["Name"] = df["Name"].str.title()

    # Reset the index
    df = df.reset_index(drop=True)

    # Sort by year then name
    df = df.sort_values(["Year", "Name"])

    return df.set_index(["Year", "Name"])

df = pd.read_csv("Subnational_total_final_energy_consumption_statistics.csv")
year_df = return_years_df(df)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.Div(id="return-description-string"),
    html.Div(
        [
            html.Div(id="df-output", className="six columns"),
            dcc.Graph(id='graph-output', className="six columns"),
        ],
        className="row"
    ),
    html.Div([
        dcc.Dropdown(
            id='df-year-value',
            options=[{'label': i, 'value': i}
                     for i in year_df.index.unique(0)],
            value='2005',
            optionHeight=30
        )],
        style={"width": "4%", "margin-top": "15px", "font-size":"20px", "height":"50px"}
    ),
])

@app.callback(
    Output(component_id="df-output", component_property="children"),
    Input(component_id='df-year-value', component_property='value')
)
def return_year_df(year):
    new_df = year_df.loc[int(year)].copy()
    new_df["Region"] = year_df.loc[int(year)].index.values
    descriptive_columns = ["Region", "Unit"]
    energy_columns = [col for col in new_df.columns if "Total" in col]
    all_columns = descriptive_columns + energy_columns
    new_df = new_df[all_columns]
    # new_df["Region"] = year_df.loc[year].Name
    new_df = generate_table(new_df)
    return new_df

@app.callback(
    Output(component_id="graph-output", component_property="figure"),
    Input(component_id='df-year-value', component_property='value')
)
def return_year_graph(year):
    new_df = year_df.loc[int(year)].copy()
    new_df["Region"] = year_df.loc[int(year)].index.values
    descriptive_columns = ["Region", "Unit"]
    energy_columns = [col for col in new_df.columns if "Total" in col]
    all_columns = descriptive_columns + energy_columns
    new_df = new_df[all_columns]
    fig = px.bar(new_df, x="Region", y="All_Fuels_Total", color="Region", title=f"Energy consumption in the UK in {year}")
    return fig

@app.callback(
    Output(component_id="return-description-string", component_property="children"),
    Input(component_id='df-year-value', component_property='value')
)
def return_description(year):
    return html.H3(f"UK Energy Cunsumption ({year})")

if __name__ == '__main__':
    app.run_server(debug=True)
