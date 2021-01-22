import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
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

if __name__ == '__main__':
    app.run_server(debug=True)
