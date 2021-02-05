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
    input pandas df columns with X, Y, Z
    '''
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.tricontourf(Lon, Lat, Z, cmap='seismic')
    # everything below this is to remove white space and axis from plot 
    # in order to save the image and plot on map properly. 
    fig.frameon  = False
    fig.gca().xaxis.set_major_locator(plt.NullLocator())
    fig.gca().yaxis.set_major_locator(plt.NullLocator())
    ax.set_axis_off()
    plt.close(fig)
    fig.savefig(f'contour_of_{Z.name}.png', bbox_inches='tight', 
                pad_inches=0)
    
    
def create_map(df, lon_col='Lon', lat_col = 'Lat', data_col= 'Delta N'):
    '''
    creates folium map for data exploration using a pandas data frame.
    The default values are created for the table from velocity_table.txt
    '''
    start_cords = (((df[lat_col].min() +  # taking average of max
                 df[lat_col].max()))/2,# and min to use as starting cords
               (df[lon_col].min()+
                df[lon_col].max())/2)
    my_map = folium.Map(start_cords,
                        tiles = 'Stamen Terrain',
                        zoom_start = 5, width = 600, height = 500,
                       prefer_canvas =True)
    minimap = plugins.MiniMap(toggle_display=True)
    my_map.add_child(minimap)
    plugins.Fullscreen(position='topleft').add_to(my_map)
    folium.GeoJson(ucerf3, name = 'UCERF3 Faults').add_to(my_map)
    
    # making MPL seismic colormap in Branca
    colors_list = ['blue', 'white', 'red']
    minimum = df[data_col].min()
    maximum = df[data_col].max()
    colormap = cm.LinearColormap(colors = colors_list
                        ,vmin = minimum
                        ,vmax= maximum)
    create_contour_overlay(df[lon_col], df[lat_col], df[data_col])
    
    folium.raster_layers.ImageOverlay(f'contour_of_{df[data_col].name}.png', 
                                      [[df.Lat.min(),
                                        df.Lon.min()],
                                       [df.Lat.max(),
                                        df.Lon.max() ]],
                                      opacity = 0.8,
                                      name = f'Velocity in mm/yr for {df[data_col].name}').add_to(my_map)
    my_map.add_child(colormap)
    my_map.add_child(folium.LayerControl(postion='bottomleft'))
    my_map.add_child(folium.LatLngPopup())   
    return my_map