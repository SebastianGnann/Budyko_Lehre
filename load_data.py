import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from scipy import stats
import seaborn as sns
from functions import plotting_fcts
import geopandas as gpd
from shapely.geometry import Point
import rasterio as rio
from pingouin import partial_corr

# This script loads and analyses Caravan data.

# prepare data
data_path = "D:/Data/Caravan/"

# check if folders exist
results_path = "results/"
if not os.path.isdir(results_path):
    os.makedirs(results_path)
figures_path = "figures/"
if not os.path.isdir(figures_path):
    os.makedirs(figures_path)

# camels datasets
camels_list = ["camels", "camelsaus", "camelsbr", "camelscl", "camelsgb", "hysets", "lamah"]
camels_list = ["camels"]

# load attributes
df_attributes = pd.DataFrame()
for c in camels_list:
    df_attributes_other = pd.read_csv(data_path + "attributes/" + c + "/attributes_other_" + c + ".csv", sep=',')
    df_attributes_caravan = pd.read_csv(data_path + "attributes/" + c + "/attributes_caravan_" + c + ".csv", sep=',')
    df_attributes_tmp = pd.merge(df_attributes_other,df_attributes_caravan)
    df_attributes_hydroatlas = pd.read_csv(data_path + "attributes/" + c + "/attributes_hydroatlas_" + c + ".csv", sep=',')
    df_attributes_tmp = pd.merge(df_attributes_tmp,df_attributes_hydroatlas)

    if len(df_attributes)==0:
        df_attributes = df_attributes_tmp
    else:
        df_attributes = pd.concat([df_attributes,df_attributes_tmp])

#df = df.dropna()

# load timeseries
df_timeseries = pd.DataFrame(columns=["date", "total_precipitation_sum", "potential_evaporation_sum", "streamflow"])
for c in camels_list:

    for id in df_attributes["gauge_id"]:
        #print(id)
        df_tmp = pd.read_csv(data_path + "timeseries/csv/" + c + "/" + id + ".csv", sep=',')
        df_tmp = df_tmp[["date", "total_precipitation_sum", "potential_evaporation_sum", "streamflow", "surface_net_solar_radiation_mean", "surface_net_thermal_radiation_mean"]]
        df_tmp["gauge_id"] = id

        if len(df_timeseries)==0:
            df_timeseries = df_tmp
        else:
            df_timeseries = pd.concat([df_timeseries,df_tmp])

df_timeseries["surface_net_solar_radiation_mean"] = df_timeseries["surface_net_solar_radiation_mean"] * (12.87/365)
df_timeseries["surface_net_thermal_radiation_mean"] = df_timeseries["surface_net_thermal_radiation_mean"] * (12.87/365)
df_timeseries["netrad"] = df_timeseries["surface_net_solar_radiation_mean"] + df_timeseries["surface_net_thermal_radiation_mean"]
print(df_timeseries.groupby('gauge_id').mean())

df_mean = df_timeseries.groupby('gauge_id').mean()
df_mean["aridity_netrad"] = df_mean["netrad"]/df_mean["total_precipitation_sum"]
df_mean["aridity_pet"] = df_mean["potential_evaporation_sum"]/df_mean["total_precipitation_sum"]
df_mean["runoff_ratio"] = df_mean["streamflow"]/df_mean["total_precipitation_sum"]
df_attributes["aridity_hydroatlas"] = 1/(df_attributes["ari_ix_sav"]/100)
df_attributes.index = df_attributes["gauge_id"]
df = df_mean.join(df_attributes, on='gauge_id')

# todo: select only relevant attributes

# todo: use shorter periods for averages (e.g. 10y, 5y, 1y)


# plot standard Budyko plot
fig = plt.figure(figsize=(4, 3), constrained_layout=True)
axes = plt.axes()
x_name = "aridity_netrad"
y_name = "runoff_ratio"
x_unit = " [-]"
y_unit = " [-]"
im = axes.scatter(df[x_name], 1-df[y_name], s=10, c="tab:blue", alpha=0.5, lw=0, label="netrad")
im = axes.scatter(df["aridity_hydroatlas"], 1-df[y_name], s=10, c="tab:orange", alpha=0.5, lw=0, label="hydroatlas")
im = axes.scatter(df["aridity_pet"], 1-df[y_name], s=10, c="tab:green", alpha=0.5, lw=0, label="pet")
axes.set_xlabel(x_name + x_unit)
axes.set_ylabel(y_name + y_unit)
axes.set_xlim([0, 5])
axes.set_ylim([-0.25, 1.25])
plotting_fcts.plot_Budyko_limits(df[x_name], df[y_name])
axes.legend(loc='best')
fig.savefig(figures_path + x_name + '_' + y_name + ".png", dpi=600, bbox_inches='tight')
plt.close()

# save data
df.to_csv(results_path + 'caravan_processed.csv', index=False)
