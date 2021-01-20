from pandas import DataFrame

def filter_energy_type(df, energy_type):
    descriptive_columns = ["Name", "Year", "Unit"]
    energy_columns = [col for col in df.columns if energy_type.lower() in col.lower()]
    all_columns = descriptive_columns + energy_columns
    series_dict = {}
    for col in all_columns:
        try:
            series_dict[col] = df[col]
        except KeyError:
            pass
    return DataFrame.from_dict(series_dict).reset_index(drop=True).T