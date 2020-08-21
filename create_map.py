# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 16:20:06 2020

@author: Nathan Pulver, nathan.pulver@jpl.nasa.gov , nwpulver@cpp.edu
"""
import folium
from folium import plugins
import branca.colormap as cm

ucerf3 = 'UCERF3_.geojson'
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
                        zoom_start = 8, width = 800, height = 350,
                       prefer_canvas =True)
    minimap = plugins.MiniMap(toggle_display=True)
    my_map.add_child(minimap)
    plugins.Fullscreen(position='topleft').add_to(my_map)
    folium.GeoJson(ucerf3, name = 'UCERF3 Faults').add_to(my_map)
    

    colors_list = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    minimum = df[data_col].min()
    maximum = df[data_col].max()
    colormap = cm.LinearColormap(colors = colors_list
                        ,vmin = minimum
                        ,vmax= maximum)
    data_group = folium.FeatureGroup(name = 'Velocities in mm/yr for ' + data_col)
    df.apply(lambda row: folium.Circle(
        location = (row[lat_col], row[lon_col]),
        radius = 0.1,
        fill = True, 
        color= colormap(row[data_col]),
        fill_opacity = 0.8
        ).add_to(data_group), axis=1)          
    my_map.add_child(colormap)
    my_map.add_child(data_group)
    my_map.add_child(folium.LayerControl(postion='bottomleft'))
    my_map.add_child(folium.LatLngPopup())   
    return my_map