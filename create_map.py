# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 16:20:06 2020

@author: Nathan Pulver, nathan.pulver@jpl.nasa.gov , nwpulver@cpp.edu
"""
import folium
from folium import plugins
import branca.colormap as cm
import matplotlib.pyplot as plt

ucerf3 = 'UCERF3_.geojson'

def create_contour_overlay(Lon,Lat,Z):
    '''
    input pandas df columns with 
    '''
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.tricontourf(Lon, Lat, Z, cmap='seismic')
    fig.frameon  = False
    ax.set_axis_off()
    plt.close(fig)
    fig.savefig(f'contour_of_{Z.name}.png')
    
    
def create_map(df, lon_col='Lon', lat_col = 'Lat', data_col= 'Delta N'):
    '''
    creates folium map for data exploration using a pandas data frame.
    The default values are created for the table from velocity_table.txt
    '''
    start_cords = (((df[lat_col].min() + 
                 df[lat_col].max()))/2, 
               (df[lon_col].min()+
                df[lon_col].max())/2)
    my_map = folium.Map(start_cords,
                        tiles = 'Stamen Terrain',
                        zoom_start = 8, width = 600, height = 500,
                       prefer_canvas =True)
    minimap = plugins.MiniMap(toggle_display=True)
    my_map.add_child(minimap)
    plugins.Fullscreen(position='topleft').add_to(my_map)
    folium.GeoJson(ucerf3, name = 'UCERF3 Faults').add_to(my_map)
    

    colors_list = ['blue', 'white', 'red']
    minimum = df[data_col].min()
    maximum = df[data_col].max()
    colormap = cm.LinearColormap(colors = colors_list
                        ,vmin = minimum
                        ,vmax= maximum)
    create_contour_overlay(df[lon_col], df[lat_col], df[data_col])
    
    folium.raster_layers.ImageOverlay(f'contour_of_{df[data_col].name}.png', [[df.Lat.min(), df.Lon.min()],[df.Lat.max(), df.Lon.max() ]], opacity = 0.8, name = f'Velocity in mm/yr for {df[data_col].name}').add_to(my_map)
    my_map.add_child(colormap)
    my_map.add_child(folium.LayerControl(postion='bottomleft'))
    my_map.add_child(folium.LatLngPopup())   
    return my_map