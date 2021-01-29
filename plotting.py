import plotly

ENERGY_SOURCE_COLORS = {
    "Coal": '#525B76',
    "Manufactured": '#F4A259',
    "Petroleum": '#7A89C2',
    "Gas": '#F9B5AC',
    "Electricity": '#EE7674',
    "Bioenergy": '#9DBF9E',
}
PLOT_COLORS = {
    'plot_bgcolor': '#fffffa',
    'paper_bgcolor': '#fffffa'
}

CHOROPLETH_COLORS = {
    'plot_bgcolor': '#F2F8FF',
    'paper_bgcolor': '#F2F8FF'
}

places = ["United Kingdom", "Scotland", "Wales", "Northern Ireland", "East Midlands", "East Of England", "London", "North East", "North West", "South East", "South West", "West Midlands", "Yorkshire And The Humber"]
REGION_COLORS = dict(zip(places, plotly.colors.qualitative.Prism))