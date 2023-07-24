import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from functions import helper_fcts

# This script loads and analyses CAMELS GB data.

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
GB_attributes_path = data_path + "CAMELS_GB/data/"
attributes_list = ["climatic","humaninfluence","hydrogeology","hydrologic","hydrometry","landcover","soil"]

df_attributes = pd.read_csv(GB_attributes_path + "CAMELS_GB_" + "topographic" + "_attributes.csv", sep=',')
for attribute in attributes_list:
    df_attributes_tmp = pd.read_csv(GB_attributes_path + "CAMELS_GB_" + attribute + "_attributes.csv", sep=',')
    df_attributes = pd.merge(df_attributes,df_attributes_tmp)

# load timeseries
# the model outputs also contain the observed streamflow data alongside precipitation and pet
GB_timeseries_path = "CAMELS_GB/data/timeseries/"

# loop over folder with timeseries
df_timeseries = pd.DataFrame(columns = ["date","precipitation","pet","temperature","discharge_spec","discharge_vol","peti","humidity","shortwave_rad","longwave_rad","windspeed"])
for id in df_attributes["gauge_id"]:
    tmp_path = data_path + GB_timeseries_path + "CAMELS_GB_hydromet_timeseries_" + str(id) + "_19701001-20150930.csv"
    df_tmp = pd.read_csv(tmp_path, sep=',')
    df_tmp["gauge_id"] = id
    if len(df_timeseries) == 0:
        df_timeseries = df_tmp
    else:
        df_timeseries = pd.concat([df_timeseries, df_tmp])

print("finished loading time series")

#df_timeseries['date'] = pd.to_datetime(dict(year=df_timeseries.YR, month=df_timeseries.MNTH, day=df_timeseries.DY))
df_selected = pd.DataFrame()
df_selected["gauge_id"] = df_timeseries["gauge_id"]
df_selected["date"] = df_timeseries["date"]
df_selected["precipitation"] = df_timeseries["precipitation"]
df_selected["pet"] = df_timeseries["pet"]
df_selected["streamflow"] = df_timeseries["discharge_vol"]
df_selected["temperature"] = df_timeseries["temperature"]

# average time series
df_mean = df_selected.groupby('gauge_id').mean()
df_mean["aridity_control"] = df_mean["pet"]/df_mean["precipitation"]
df_mean["runoff_ratio_control"] = df_mean["streamflow"]/df_mean["precipitation"]

print("finished averaging time series")

# todo: select only relevant attributes
df_attributes.index = df_attributes["gauge_id"]

df = df_mean.join(df_attributes, on='gauge_id')

# calculate annual averages
years = ['1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990']
for year in years:
    start_date = year + '-01-01'
    end_date = year + '-12-31'
    mask = (df_selected['date'] >= start_date) & (df_selected['date'] <= end_date)
    df_tmp = df_selected.loc[mask].groupby('gauge_id').mean()
    df_tmp["aridity"] = df_tmp["pet"]/df_tmp["precipitation"]
    df_tmp["runoff_ratio"] = df_tmp["streamflow"]/df_tmp["precipitation"]
    df_tmp = df_tmp.add_suffix('_' + year)
    df = df_tmp.join(df, on='gauge_id')

# calculate decadal averages
decades = [['1981','1990'], ['1991','2000'], ['2001','2010']]
for decade in decades:
    start_date = decade[0] + '-01-01'
    end_date = decade[1] + '-12-31'
    mask = (df_selected['date'] >= start_date) & (df_selected['date'] <= end_date)
    df_tmp = df_selected.loc[mask].groupby('gauge_id').mean()
    df_tmp["aridity"] = df_tmp["pet"]/df_tmp["precipitation"]
    df_tmp["runoff_ratio"] = df_tmp["streamflow"]/df_tmp["precipitation"]
    df_tmp = df_tmp.add_suffix('_' + decade[0] + '-' + decade[1])
    df = df_tmp.join(df, on='gauge_id')

# save data
df.to_csv(results_path + 'camels_GB_processed.csv', index=False)

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
fig.savefig(figures_path + x_name + '_' + y_name + "_CAMELS_GB" + ".png", dpi=600, bbox_inches='tight')
plt.close()

