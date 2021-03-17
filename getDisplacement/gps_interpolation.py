import numpy as np
import pandas as pd
from pykrige.ok import OrdinaryKriging


def create_grid(array, spacing=0.005):
    """
    creates evenly spaced grid from the min and max of an array
    """
    grid = np.arange(np.amin(array), np.amax(array), spacing)
    return grid


def reshape_and_create_df(grid_x, grid_y, z1, new=True, z_name="Z"):
    """
    Takes outputs of interpolate function and converts them
    to a pandas data frame. If it is a new data frame, use new =True
    otherwise you can get a dictionairy out to add a single col to an
    existing data frame
    """
    if new == True:

        mesh_x, mesh_y = np.meshgrid(grid_x, grid_y)
        size = np.size(mesh_x)
        reshape_meshx = np.reshape(mesh_x, size)
        reshape_meshy = np.reshape(mesh_y, size)
        z1_reshape = np.reshape(z1, size)
        array = np.dstack([reshape_meshx, reshape_meshy, z1_reshape])
        df_dict = {
            "Lon": array[0, range(size), 0],
            "Lat": array[0, range(size), 1],
            z_name: array[0, range(size), 2],
        }

        Df = pd.DataFrame(df_dict)
        return Df
    else:
        mesh_x, mesh_y = np.meshgrid(grid_x, grid_y)
        size = np.size(mesh_x)
        z1_reshape = np.reshape(z1, size)
        col_dict = {z_name: z1_reshape}
        return col_dict


def interpolate(
    x, y, grid_spacing=0.004, model="spherical", returngrid=False, **kwargs
):
    """Interpolates any number of z values
    and uses create_grid to create a grid of values based on min and max of x and y"""
    grid_x = create_grid(x, spacing=grid_spacing)
    grid_y = create_grid(y, spacing=grid_spacing)
    counter = 0
    for k, v in kwargs.items():

        if counter == 0:
            # nlags is number of averaging bins, default is 6 and I found much better results with higher values
            OK = OrdinaryKriging(
                x,
                y,
                v,
                variogram_model=model,
                verbose=False,
                enable_plotting=False,
                nlags=40,
                coordinates_type="geographic",
            )
            z1, ss1 = OK.execute("grid", grid_x, grid_y, mask=False)
            vals = np.ma.getdata(z1)
            sigma = np.ma.getdata(ss1)
            df = reshape_and_create_df(grid_x, grid_y, vals, z_name=k)
            counter += 1
        else:
            OK = OrdinaryKriging(
                x,
                y,
                v,
                variogram_model=model,
                verbose=False,
                enable_plotting=False,
                nlags=40,
            )
            z1, ss1 = OK.execute("grid", grid_x, grid_y, mask=False)
            vals = np.ma.getdata(z1)
            sigma = np.ma.getdata(ss1)
            col = reshape_and_create_df(grid_x, grid_y, vals, z_name=k, new=False)
            df[k] = col[k]
    return df
