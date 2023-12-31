import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
import os
from functions import helper_fcts

# This script loads and analyses CAMELS US data.

# prepare data
data_path = "D:/Data/CAMELS/"

# check if folders exist
results_path = "results/"
if not os.path.isdir(results_path):
    os.makedirs(results_path)
figures_path = "figures/"
if not os.path.isdir(figures_path):
    os.makedirs(figures_path)

# load camels dataset
# load attributes
US_attributes_path = data_path + "CAMELS_US/camels_attributes_v2.0/camels_attributes_v2.0/"
attributes_list = ["clim","geol","hydro","soil","topo","vege"]

df_attributes = pd.read_csv(US_attributes_path + "camels_" + "name" + ".txt", sep=';')
for attribute in attributes_list:
    df_attributes_tmp = pd.read_csv(US_attributes_path + "camels_" + attribute + ".txt", sep=';')
    df_attributes = pd.merge(df_attributes,df_attributes_tmp)

# select only relevant attributes
df_attributes = df_attributes[['gauge_id', 'gauge_name', 'area_gages2', 'gauge_lat', 'gauge_lon',
                               'p_seasonality', 'frac_snow', 'high_prec_freq',
                               'frac_forest', 'slope_mean', 'elev_mean',
                               'soil_depth_pelletier', 'clay_frac', 'carbonate_rocks_frac', 'geol_permeability']]

# load timeseries
# the model outputs also contain the observed streamflow data alongside precipitation and pet
US_modelled_path = "CAMELS_US/basin_timeseries_v1p2_modelOutput_daymet/model_output_daymet/model_output/flow_timeseries/daymet/"

# loop over folder with timeseries
df_timeseries = pd.DataFrame(columns = ["YR", "MNTH", "DY", "HR", "SWE", "PRCP", "RAIM", "TAIR", "PET", "ET", "MOD_RUN", "OBS_RUN"])
gauge_id_control = []
for path, subdirs, files in os.walk(data_path+US_modelled_path):
    for name in files:
        if '05_model_output' in name:
            #print(os.path.join(path, name))
            df_tmp = pd.read_csv(os.path.join(path, name), sep='\s+')
            df_tmp["gauge_id"] = name[0:8]
            if name[0:8] in gauge_id_control:
                #print('existing twice')
                continue
            gauge_id_control.append(name[0:8])
            df_tmp.loc[df_tmp["OBS_RUN"] < 0, "OBS_RUN"] = np.nan # nan is -999 in CAMELS
            #df_tmp = df_tmp.dropna()
            if len(df_timeseries) == 0:
                df_timeseries = df_tmp
            else:
                df_timeseries = pd.concat([df_timeseries, df_tmp])

print("finished loading time series")

df_timeseries['date'] = pd.to_datetime(dict(year=df_timeseries.YR, month=df_timeseries.MNTH, day=df_timeseries.DY))
df_selected = pd.DataFrame()
df_selected["gauge_id"] = df_timeseries["gauge_id"]
df_selected["date"] = df_timeseries["date"]
df_selected["precipitation"] = df_timeseries["PRCP"]
df_selected["pet"] = df_timeseries["PET"]
df_selected["streamflow"] = df_timeseries["OBS_RUN"]
df_selected["temperature"] = df_timeseries["TAIR"]

# average time series
df_mean = df_selected.groupby('gauge_id').mean()
df_mean["aridity"] = df_mean["pet"]/df_mean["precipitation"]
df_mean["runoff_ratio"] = df_mean["streamflow"]/df_mean["precipitation"]

# calculate aridity and climatic water balance
df_mean["aridity_class"] = 0 # assign aridity class (0 = energy-limited, 1 = water-limited)
df_mean.loc[df_mean["aridity"] > 1, "aridity_class"] = 1
df_mean["climatic_water_balance"] = df_mean["precipitation"] - df_mean["pet"] # climatic water balance is defined as PET - P

# calculate evaporative fraction using the Budyko equation and use it to calculate Budyko anomalies
df_mean["evaporative_fraction"] = helper_fcts.Budyko_curve(df_mean["aridity"])
df_mean["Budyko_anomaly"] = (1 - df_mean["runoff_ratio"]) - df_mean["evaporative_fraction"]

print("finished averaging time series")

df_attributes["gauge_id"] = df_attributes["gauge_id"].astype(str).str.zfill(8)
df_attributes.index = df_attributes["gauge_id"]

df = df_mean.join(df_attributes, on='gauge_id')

# calculate annual averages
#years = ['1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990']
years = np.linspace(2000,2009,10)
for i in range(len(years)):
    year = years[i]
    print(year)
    start_date = str(int(year-1)) + '-10-01'
    end_date = str(int(year)) + '-09-30'
    mask = (df_selected['date'] >= start_date) & (df_selected['date'] <= end_date)
    df_tmp = df_selected.loc[mask].groupby('gauge_id', dropna=False).mean()
    df_tmp["aridity"] = df_tmp["pet"]/df_tmp["precipitation"]
    df_tmp["runoff_ratio"] = df_tmp["streamflow"]/df_tmp["precipitation"]
    df_tmp = df_tmp.add_suffix('_' + str(int(year)))
    df = df_tmp.join(df, on='gauge_id')

"""
# calculate decadal averages
decades = [['1980','1989'], ['1990','1999'], ['2000','2009']]
for decade in decades:
    start_date = decade[0] + '-01-01'
    end_date = decade[1] + '-12-31'
    mask = (df_selected['date'] >= start_date) & (df_selected['date'] <= end_date)
    df_tmp = df_selected.loc[mask].groupby('gauge_id', dropna=False).mean()
    df_tmp["aridity"] = df_tmp["pet"]/df_tmp["precipitation"]
    df_tmp["runoff_ratio"] = df_tmp["streamflow"]/df_tmp["precipitation"]
    df_tmp = df_tmp.add_suffix('_' + decade[0] + '-' + decade[1])
    df = df_tmp.join(df, on='gauge_id')
"""

# save data
df.to_csv(results_path + 'camels_US_processed.csv', index=False)

print("finished saving data")

# plot standard Budyko plot
fig = plt.figure(figsize=(4, 3), constrained_layout=True)
axes = plt.axes()
x_name = "aridity"
y_name = "runoff_ratio"
x_unit = " [-]"
y_unit = " [-]"
im = axes.scatter(df[x_name], 1-df[y_name], s=10, c="tab:blue", alpha=0.5, lw=0, label="netrad")
axes.set_xlabel(x_name + x_unit)
axes.set_ylabel(y_name + y_unit)
axes.set_xlim([0, 5])
axes.set_ylim([-0.25, 1.25])
helper_fcts.plot_Budyko_limits(df[x_name], df[y_name], axes)
helper_fcts.plot_Budyko_curve(np.linspace(0,10,100), axes)
fig.savefig(figures_path + x_name + '_' + y_name + "_CAMELS_US" + ".png", dpi=600, bbox_inches='tight')
plt.close()

# plot map
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
#us = world[world.name == 'United States of America']
scatter_df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.gauge_lon, df.gauge_lat))
fig, ax = plt.subplots(figsize=(6, 3))
world.boundary.plot(ax=ax, linewidth=0.5, color='black')
world.plot(ax=ax, color='lightgrey', edgecolor='black')
scatter_df.plot(ax=ax, markersize=10, color='tab:blue')
plt.title('CAMELS US Einzugsgebiete')
plt.xlabel('Längengrad')
plt.ylabel('Breitengrad')
plt.xlim(-130, -65); plt.ylim(20, 55)
fig.savefig(figures_path + "map_CAMELS_US" + ".png", dpi=600, bbox_inches='tight')
plt.close()
