# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 16:42:08 2020

@author: Nathan Pulver nathan.pulver@jpl.nasa.gov, nwpulver@cpp.edu
"""

import numpy as np
import pandas as pd


def load_gps_data(filename):
    """


    Parameters
    ----------
    filename :
        GPS data as retreived from geo-gateway.org as a txt file.
        or from getDisplacement.py
    Returns
    -------
    Pandas Dataframe of Lon, Lat, and Delta Values

    """
    gps_in = np.loadtxt(filename, skiprows=(1), usecols=(1, 2, 3, 4, 5))
    gps_dict = {
        "Lon": gps_in[:, 0],
        "Lat": gps_in[:, 1],
        "Delta E": gps_in[:, 2],
        "Delta N": gps_in[:, 3],
        "Delta V": gps_in[:, 4],
    }
    gps_df = pd.DataFrame(gps_dict)
    return gps_df
