import pandas as pd

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
