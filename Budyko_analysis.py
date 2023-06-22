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

# load data
df = pd.read_csv(results_path + "caravan_processed.csv")

df["aridity_class"] = 0
df.loc[df["aridity_netrad"] > 1, "aridity_class"] = 1
df["climatic_water_balance"] = df["total_precipitation_sum"] - df["netrad"]

# plot scatter plot between P, PET, and Q for energy-limited and water-limited regions
fig = plt.figure(figsize=(3, 3), constrained_layout=True)
axes = plt.axes()
x_name = "total_precipitation_sum"
y_name = "streamflow"
x_unit = " [mm/d]"
y_unit = " [mm/d]"
im = axes.scatter(df.loc[df["aridity_class"] == 1, x_name], df.loc[df["aridity_class"] == 1, y_name],
                  s=10, c="tab:orange", alpha=0.5, lw=0, label="water-limited")
im = axes.scatter(df.loc[df["aridity_class"] == 0, x_name], df.loc[df["aridity_class"] == 0, y_name],
                  s=10, c="tab:blue", alpha=0.5, lw=0, label="energy-limited")
axes.set_xlabel(x_name + x_unit)
axes.set_ylabel(y_name + y_unit)
axes.set_xlim([0, 10])
axes.set_ylim([0, 10])
#plotting_fcts.plot_origin_line(df[x_name], df[y_name])
#axes.set_xscale('log')
#axes.set_yscale('log')
axes.legend(loc='best')
fig.savefig(figures_path + x_name + '_' + y_name + ".png", dpi=600, bbox_inches='tight')
plt.close()

fig = plt.figure(figsize=(3, 3), constrained_layout=True)
axes = plt.axes()
x_name = "climatic_water_balance"
y_name = "streamflow"
x_unit = " [mm/d]"
y_unit = " [mm/d]"
r_sp_energy_limited, _ = stats.spearmanr(df.loc[df["aridity_class"] == 0, x_name],
                                         df.loc[df["aridity_class"] == 0, y_name],
                                         nan_policy='omit')
im = axes.scatter(df.loc[df["aridity_class"] == 0, x_name], df.loc[df["aridity_class"] == 0, y_name],
                  s=10, c="tab:blue", alpha=0.5, lw=0,
                  label="Ep/P < 1; corr = " + str(np.round(r_sp_energy_limited,2)))
r_sp_water_limited, _ = stats.spearmanr(df.loc[df["aridity_class"] == 1, x_name],
                                        df.loc[df["aridity_class"] == 1, y_name],
                                        nan_policy='omit')
im = axes.scatter(df.loc[df["aridity_class"] == 1, x_name], df.loc[df["aridity_class"] == 1, y_name],
                  s=10, c="tab:orange", alpha=0.5, lw=0,
                  label="Ep/P > 1; corr = " + str(np.round(r_sp_water_limited,2)))
axes.set_xlabel(x_name + x_unit)
axes.set_ylabel(y_name + y_unit)
axes.set_xlim([-5, 5])
axes.set_ylim([0, 10])
#plotting_fcts.plot_origin_line(df[x_name], df[y_name])
#axes.set_xscale('log')
#axes.set_yscale('log')
axes.legend(loc='best')
fig.savefig(figures_path + x_name + '_' + y_name + ".png", dpi=600, bbox_inches='tight')
plt.close()

# plot standard Budyko plot
fig = plt.figure(figsize=(4, 2), constrained_layout=True)
axes = plt.axes()
x_name = "aridity_netrad"
y_name = "runoff_ratio"
x_unit = " [-]"
y_unit = " [-]"
im = axes.scatter(df[x_name], 1-df[y_name], s=10, c="tab:blue", alpha=0.5, lw=0)
axes.set_xlabel(x_name + x_unit)
axes.set_ylabel(y_name + y_unit)
axes.set_xlim([0, 5])
axes.set_ylim([-0.25, 1.25])
plotting_fcts.plot_Budyko_limits(df[x_name], df[y_name])
fig.savefig(figures_path + x_name + '_' + y_name + ".png", dpi=600, bbox_inches='tight')
plt.close()

# plot Budyko plot with different attributes: snow, seasonality, size, storage capacity?
fig = plt.figure(figsize=(4, 2), constrained_layout=True)
axes = plt.axes()
x_name = "aridity_netrad"
y_name = "runoff_ratio"
x_unit = " [-]"
y_unit = " [-]"
z_name = "frac_snow"
z_unit = " [-]"
im = axes.scatter(df[x_name], 1-df[y_name], s=10, c=df[z_name], alpha=0.5, lw=0) #, s=df["area"]/100
axes.set_xlabel(x_name + x_unit)
axes.set_ylabel(y_name + y_unit)
axes.set_xlim([0, 5])
axes.set_ylim([-0.25, 1.25])
plotting_fcts.plot_Budyko_limits(df[x_name], df[y_name])
#axes.set_xscale('log')
cbar = fig.colorbar(im, ax=axes)
cbar.set_label(z_name + z_unit)
fig.savefig(figures_path + x_name + '_' + y_name + '_' + z_name + ".png", dpi=600, bbox_inches='tight')
plt.close()

# todo: plot Budyko plot for different time periods
