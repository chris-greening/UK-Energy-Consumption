import datetime

import pandas as pd

from regional_information import regional_information

def preprocess_dataframe(df: "pandas.DataFrame") -> "pandas.DataFrame":
    dff = df[df["UNIT"] == "GWh"]
    dff = dff[dff["NAME"].str.isupper()]
    dff = dff.drop(columns=["LAUA"])

    # Reorder the columns
    descriptive_columns = ["YEAR", "NAME", "UNIT"]
    other_columns = [col for col in dff.columns if col not in descriptive_columns]
    all_columns = descriptive_columns + other_columns
    dff = dff[all_columns]

    # Title the columns and region names
    dff = dff.rename(columns={col: col.title() for col in all_columns})
    dff = dff.rename(columns={
        "Bioenergy_All": "Bioenergy_Total",
        "Total_Coal": "Coal_Total",
        "Total_Manufactured": "Manufactured_Total",
        "Total_Petroleum": "Petroleum_Total"
    })
    dff["Name"] = dff["Name"].str.title()

    dff = combine_regions(
        dff,
        ["Inner London", "Outer London", "Greater London"],
        "London",
        "GWh"
    )

    # Reset the index
    dff = dff.reset_index(drop=True)

    # Sort by year then name
    dff = dff.sort_values(["Year", "Name"])
    return dff

def combine_regions(df, subregions, region_name, unit):
    subregion_df = df[df["Name"].isin(subregions)]
    full_df = df[~df["Name"].isin(subregions)]
    region_df = subregion_df.groupby(["Year"], as_index=False).sum()
    region_df["Name"] = region_name
    region_df["Unit"] = unit
    return pd.concat([full_df, region_df])

def melt_dataframe(df: "pandas.DataFrame") -> "pandas.DataFrame":
    descriptive_columns = ["Name", "Year"]

    totals_columns = [col for col in df.columns if "Total" in col and col != "All_Fuels_Total"]
    all_columns = descriptive_columns + totals_columns
    all_columns = [col for col in all_columns if col in df.columns]
    totals_df = df[all_columns]
    totals_df = totals_df.rename(columns={col: col.replace("_Total", "") for col in totals_df.columns})

    id_vars = [col for col in descriptive_columns if col in df.columns]
    long_df = pd.melt(totals_df, id_vars=id_vars, value_vars=[
                    "Coal", "Manufactured", "Petroleum", "Gas", "Electricity", "Bioenergy"])
    long_df = long_df.rename(columns={"variable": "Energy type", "value": "GWh"})
    return long_df

def construct_regional_geojson(location, geojson):
    region_geojson = [val for val in geojson["features"]
                      if val["properties"]["nuts118nm"] == location]
    region_geojson = {'type': 'FeatureCollection',
                      'crs': {'type': 'name',
                              'properties': {'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'}},
                      'features': region_geojson}
    return region_geojson

def click_location(clickData):
    return clickData['points'][0]['x']

def construct_regional_markdown(location):
    region = regional_information[location]
    msg = f"""
{region["description"]}

[Wiki/Source]({region["source"]})
"""
    return msg

def calculate_rate_of_change_df(location, df):
    region_df = df[df["Name"] == location]
    region_df = region_df.drop(
        columns=["Name", "Unit"])
    region_df = region_df.set_index("Year")

    year_change_df = region_df.pct_change().cumsum()
    year_change_df *= 100

    year_change_df = melt_dataframe(
        year_change_df.reset_index())

    year_change_df["Year"] = year_change_df["Year"].apply(
        lambda x: datetime.datetime.strptime(str(x), "%Y"))
    return year_change_df

def calculate_energy_proportion_df(year, df):
    year_df = df[df["Year"] == year]
    total_consumption_df = year_df.groupby("Name").sum()
    highest_region = total_consumption_df[total_consumption_df["All_Fuels_Total"] == total_consumption_df["All_Fuels_Total"].max()].index
    highest_region_df = year_df[year_df["Name"] == highest_region[0]]
    adjusted_df = year_df.copy()
    adjusted_df.iloc[:, 3:-4] = adjusted_df.iloc[:, 3:-4].div(adjusted_df["All_Fuels_Total"], axis=0)
    long_adjusted_sum_df = pd.melt(adjusted_df, id_vars=["Year", "Name"], value_vars=[col for col in highest_region_df.columns if "Total" in col])
    long_adjusted_sum_df = long_adjusted_sum_df.rename(columns={"variable": "Energy type", "value": "%"})
    long_adjusted_sum_df["Energy type"] = long_adjusted_sum_df["Energy type"].str.replace(
        "_Total", "")
    long_adjusted_sum_df["%"] = long_adjusted_sum_df["%"] * 100
    return long_adjusted_sum_df
