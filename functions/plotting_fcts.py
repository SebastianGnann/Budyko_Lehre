import numpy as np
import matplotlib.pyplot as plt

# This script contains a collection of function that make or help with making plots.

def plot_origin_line(x, y, **kwargs):

    ax = plt.gca()
    lower_lim = min([ax.get_xlim()[0], ax.get_ylim()[0]])
    upper_lim = max([ax.get_xlim()[1], ax.get_ylim()[1]])
    ax.plot(np.linspace(lower_lim, upper_lim, 1000), np.linspace(lower_lim,  upper_lim, 1000), '--', color='black', alpha=0.5, zorder=1)


def plot_Budyko_limits(x, y, **kwargs):

    ax = plt.gca()
    lim = max([ax.get_xlim()[1], ax.get_ylim()[1]])
    ax.plot(np.linspace(0, 1, 100), np.linspace(0, 1, 100), '--', c='gray')
    ax.plot(np.linspace(1, lim, 100), np.linspace(1, 1, 100), '--', c='gray')
