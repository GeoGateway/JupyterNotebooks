#!/usr/bin/env python3
# Author:  Developed for GeoGateway by Michael Heflin
# Date:  September 20, 2016
# Addition of NGL flag, file support by Jay Parker 
# Date:  February 10, 2021
# Organization:  JPL, Caltech

from __future__ import print_function

prolog="""
**PROGRAM**
    getDisplacement.py
      
**PURPOSE**
    Make kml file from displacement observed between two epochs

**USAGE**
"""
epilog="""
**EXAMPLE**
    getDisplacement.py --lat 33 --lon -115 --width 2 --height 2 -t1 2010-04-07 -t2 2010-04-09 -c NGL -o displacement.kml
               
**COPYRIGHT**
    | Copyright 2016, by the California Institute of Technology
    | United States Government Sponsorship acknowledged
    | All rights reserved

**AUTHORS**
    | Developed for GeoGateway by Michael Heflin
    | Jet Propulsion Laboratory
    | California Institute of Technology
    | Pasadena, CA, USA
"""

# Import modules
import os
import sys
import math
import time
import datetime
import calendar
import argparse
import subprocess
import urllib.request

class LocationItem():
   def __init__(self,line,center):
      item = line.split()
      if center == "JPL":
        if (len(item) == 8):
           if (item[1] == 'POS'):
              self.stn, self.lon, self.lat = item[0],float(item[3]),float(item[2])
              if self.lon > 180: self.lon -= 360.
              if self.lon < -180: self.lon += 360.
           else:
              self.stn = False
        else:
           self.stn = False
      if center == "NGL":
        if (len(item) == 4):
           self.stn, self.lon, self.lat = item[0],float(item[2]),float(item[1])
           if self.lon > 180: self.lon -= 360.
           if self.lon < -180: self.lon += 360.
        else:
           self.stn = False
      
class SeriesItem():
    def __init__(self,series,center):
      """
      Extract items from proper columns of line of time series.
      For JPL (position in m, see "methods" link at JPL GNSS Time Series site):
      Columns 1-3 (from 0 ) : East(m) North(m) Vert(m) 
      Columns 4-6             E_sig(m) N_sig(m) V_sig(m)

      1994.00136893         0.877450        -0.309555         0.011551         0.000609         0.000682         0.002465         0.048078        -0.202782        -0.234850    -189302400.00  1994  1  1 12  0  0
      For NGL:
      site YYMMMDD yyyy.yyyy __MJD week d reflon _e0(m) __east(m) ____n0(m) _north(m) u0(m) ____up(m) _ant(m) sig_e(m) sig_n(m) sig_u(m) __corr_en __corr_eu __corr_nu
      USC1 96JAN01 1996.0000 50083  834 2 -118.3   1375  0.510258   3766317  0.946300    21  0.941326  0.0614 0.000863 0.001028 0.004216 -0.094302  0.146021 -0.340417
      """

      ix = series.split() 
      if center == "JPL":
         self.fracYr = ix[0]
         self.ePos,self.nPos,self.uPos = ix[1],ix[2],ix[3]
         self.eSig,self.nSig,self.uSig = ix[4],ix[5],ix[6]
     
      if center == "NGL": 
         self.fracYr = ix[2]
         m2mm = 1000.
         self.ePos,self.nPos,self.uPos = ix[8],  ix[10], ix[12]
         self.eSig,self.nSig,self.uSig = ix[14], ix[15], ix[16]

def runCmd(cmd):
    '''run a command'''

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,executable='/bin/bash')
    (out, err) = p.communicate()
    if p.returncode != 0:
        raise UserWarning('failed to run {}\n{}\n'.format(cmd.split()[0],
            err))
    return out

def _getParser():
    parser = argparse.ArgumentParser(description=prolog,epilog=epilog,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', action='store', dest='output',required=True,help='output kml file')
    parser.add_argument('--lat', action='store', dest='lat',required=True,help='center latitude in degrees')
    parser.add_argument('--lon', action='store', dest='lon',required=True,help='center longitude in degrees')
    parser.add_argument('--width', action='store', dest='width',required=True,help='width in degrees')
    parser.add_argument('--height', action='store', dest='height',required=True,help='height in degrees')
    parser.add_argument('-t1', action='store', dest='epoch1',required=True,help='start date given as YYYY-MM-DD')
    parser.add_argument('-t2', action='store', dest='epoch2',required=True,help='stop date given as YYYY-MM-DD')
    parser.add_argument('--scale', action='store', dest='scale',required=False,help='scale for offsets in mm/deg')
    parser.add_argument('--ref', action='store', dest='ref',required=False,help='reference site')
    parser.add_argument('-c', action='store', dest='analysisCenter',required=False,help='analysis center [JPL or NGL]')
    parser.add_argument('-e', action='store_true',dest='eon',required=False,help='include error bars')
    parser.add_argument('--minm', action='store_true',dest='mon',required=False,help='minimize marker size')
    parser.add_argument('--dwin1', action='store',dest='dwin1',required=False,help='specify averaging window in days')
    parser.add_argument('--dwin2', action='store',dest='dwin2',required=False,help='specify averaging window in days')
    parser.add_argument('--vabs', action='store_true',dest='vabs',required=False,help='display absolute verticals')
    return parser

# turn dict object to a class object
class objdict(dict):

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)

def main():

    # Read command line arguments
    parser = _getParser()
    results = parser.parse_args()
    getDisplacement(results)

def getDisplacement(results):

    if (type(results) is dict):
        results = objdict(results)

    # Set bounds
    latmin = float(results.lat) - float(results.height)/2
    latmax = float(results.lat) + float(results.height)/2
    lonmin = float(results.lon) - float(results.width)/2
    lonmax = float(results.lon) + float(results.width)/2

    # Set scale
    scale = 320 
    if (results.scale != None):
        scale = float(results.scale)

    # Set marker size
    if (results.mon == True):
        msize = 0.2
    else:
        msize = 0.5
    
    # Set analysis center
    if (results.analysisCenter != None):
       analysisCenter = results.analysisCenter
    else: #default
       analysisCenter = "JPL"

    # Set averaging window
    dwin1 = 10./365.25/2. 
    dwin2 = 10./365.25/2. 
    if (results.dwin1 != None):
        dwin1 = float(results.dwin1)/365.25/2.
    if (results.dwin2 != None):
        dwin2 = float(results.dwin2)/365.25/2.

    # Set first epoch
    if (len(results.epoch1) == 10):
        results.epoch1 = datetime.datetime.strptime(results.epoch1,"%Y-%m-%d").strftime("%y%b%d").upper()
        ntime = time.strptime(results.epoch1,"%y%b%d")
        jtime = time.strptime("2000JAN01","%Y%b%d")
        ytime1 = float(calendar.timegm(ntime)-calendar.timegm(jtime))
        ytime1 = ytime1/(86400.*365.25)
        ytime1 = ytime1 + 2000.

    # Set second epoch
    if (len(results.epoch2) == 10):
        results.epoch2 = datetime.datetime.strptime(results.epoch2,"%Y-%m-%d").strftime("%y%b%d").upper()
        ntime = time.strptime(results.epoch2,"%y%b%d")
        jtime = time.strptime("2000JAN01","%Y%b%d")
        ytime2 = float(calendar.timegm(ntime)-calendar.timegm(jtime))
        ytime2 = ytime2/(86400.*365.25)
        ytime2 = ytime2 + 2000.

    # Read table of positions
    if analysisCenter == "JPL":
       response1 = urllib.request.urlopen(\
          'https://sideshow.jpl.nasa.gov/post/tables/table2.html')
       fileLines = response1.read().decode('utf-8').splitlines()

    elif analysisCenter == "NGL":
       response1 = urllib.request.urlopen(\
          'http://geodesy.unr.edu/NGLStationPages/llh.out')
       fileLines = response1.read().decode('utf-8').splitlines()

    else:
       raise Exception("analysisCenter supplied as "+analysisCenter+" but only JPL,NGL are supported")
       

    # Read reference series
    rlon = 0
    rlat = 0
    rrad = 0
    stop = 0
    refsite = 'NONE'
    if (results.ref != None):
        refsite = results.ref
        # JPL data has no header row
        if analysisCenter == "JPL":
            path = 'https://sideshow.jpl.nasa.gov/pub/JPL_GPS_Timeseries/' + \
                   'repro2018a/post/point/' + refsite + '.series'
        # NGL data first line is the header
        elif analysisCenter == "NGL":
            path = 'http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/'\
                  + refsite +'.tenv3'
        request = urllib.request.Request(path)
        response2 = urllib.request.urlopen(request)
        series = response2.read().decode('utf-8').splitlines()
        if analysisCenter == "NGL":
            series = series[1:]
    

        # Compute reference values
        rlon = 0
        rlat = 0
        rrad = 0
        rlon1 = 0
        rlat1 = 0
        rrad1 = 0
        slon1 = 0
        slat1 = 0
        srad1 = 0
        rlon2 = 0
        rlat2 = 0
        rrad2 = 0
        slon2 = 0
        slat2 = 0
        srad2 = 0
        scount1 = 0
        scount2 = 0
        for j in range(0,len(series)):
            item = SeriesItem(series[j],analysisCenter)
            if (math.sqrt((float(item.fracYr)-ytime1)*(float(item.fracYr)-ytime1))) < dwin1:
                sigs1 = float(item.eSig)*float(item.eSig)
                sigs2 = float(item.nSig)*float(item.nSig)
                sigs3 = float(item.uSig)*float(item.uSig)
                rlon1 = rlon1 + float(item.ePos)/sigs1
                rlat1 = rlat1 + float(item.nPos)/sigs2
                rrad1 = rrad1 + float(item.uPos)/sigs3
                slon1 = slon1 + 1/sigs1
                slat1 = slat1 + 1/sigs2
                srad1 = srad1 + 1/sigs3
                scount1 = scount1 + 1
            if (math.sqrt((float(item.fracYr)-ytime2)*(float(item.fracYr)-ytime2))) < dwin2:
                sigs1 = float(item.eSig)*float(item.eSig)
                sigs2 = float(item.nSig)*float(item.nSig)
                sigs3 = float(item.uSig)*float(item.uSig)
                rlon2 = rlon2 + float(item.ePos)/sigs1
                rlat2 = rlat2 + float(item.nPos)/sigs2
                rrad2 = rrad2 + float(item.uPos)/sigs3
                slon2 = slon2 + 1/sigs1
                slat2 = slat2 + 1/sigs2
                srad2 = srad2 + 1/sigs3
                scount2  = scount2  + 1
        if ((scount1 >= 1) & (scount2 >= 1)):
            rlon = 1000.*(rlon2/slon2-rlon1/slon1)
            rlat = 1000.*(rlat2/slat2-rlat1/slat1)
            rrad = 1000.*(rrad2/srad2-rrad1/srad1)

        # Only use displacements computed from both epochs
        if ((scount1 < 1) | (scount2 < 1)):
            stop = 1
            print("Reference site has missing data!")

    # Start kml file
    outFile1 = open(results.output+'_horizontal.kml','w')
    print("<?xml version=\"1.0\" encoding=\"UTF-8\"?>",file=outFile1)
    print("<kml xmlns=\"http://www.opengis.net/kml/2.2\" xmlns:gx=\"http://www.google.com/kml/ext/2.2\" xmlns:kml=\"http://www.opengis.net/kml/2.2\" xmlns:atom=\"http://www.w3.org/2005/Atom\">",file=outFile1)
    print(" <Folder>",file=outFile1)

    # Start kml file
    outFile2 = open(results.output+'_vertical.kml','w')
    print("<?xml version=\"1.0\" encoding=\"UTF-8\"?>",file=outFile2)
    print("<kml xmlns=\"http://www.opengis.net/kml/2.2\" xmlns:gx=\"http://www.google.com/kml/ext/2.2\" xmlns:kml=\"http://www.opengis.net/kml/2.2\" xmlns:atom=\"http://www.w3.org/2005/Atom\">",file=outFile2)
    print(" <Folder>",file=outFile2)

    # Start txt file
    outFile3 = open(results.output+'_table.txt','w')
    print("Site          Lon          Lat      Delta E      Delta N      Delta V      Sigma E      Sigma N      Sigma V",file=outFile3)

    # return data table
    data_table = []
    # Add markers and vectors
    for i in range(0,len(fileLines)):
        location = LocationItem(fileLines[i],analysisCenter)
        
        if location.stn != False:
           lon = location.lon
           lat = location.lat
           if ((lon > lonmin) & (lon < lonmax) & (lat > latmin) & (lat < latmax)):

              # Read time series
              if analysisCenter == "JPL":
                  #series = get_localdata(location.stn)
                  path = 'https://sideshow.jpl.nasa.gov/pub/' +\
                       'JPL_GPS_Timeseries/repro2018a/post/point/' \
                       + location.stn + '.series'
                
              elif analysisCenter == "NGL":
                    path = 'http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/'\
                        + location.stn +'.tenv3'
              
              request = urllib.request.Request(path)
              response2 = urllib.request.urlopen(request)
              series = response2.read().decode('utf-8').splitlines()
              series = series[1:]
              if analysisCenter == "NGL":
                 series = series[1:]
              
              # Compute displacment
              vlon = 0
              vlat = 0
              vrad = 0
              slon = 0
              slat = 0
              srad = 0
              vlon1 = 0
              vlat1 = 0
              vrad1 = 0
              slon1 = 0
              slat1 = 0
              srad1 = 0
              vlon2 = 0
              vlat2 = 0
              vrad2 = 0
              slon2 = 0
              slat2 = 0
              srad2 = 0
              scount1 = 0
              scount2 = 0
              for j in range(0,len(series)):
                 item = SeriesItem(series[j],analysisCenter)
                 if (math.sqrt((float(item.fracYr)-ytime1)*(float(item.fracYr)-ytime1))) < dwin1:
                    sigs1 = float(item.eSig)*float(item.eSig)
                    sigs2 = float(item.nSig)*float(item.nSig)
                    sigs3 = float(item.uSig)*float(item.uSig)
                    vlon1 = vlon1 + float(item.ePos)/sigs1
                    vlat1 = vlat1 + float(item.nPos)/sigs2
                    vrad1 = vrad1 + float(item.uPos)/sigs3
                    slon1 = slon1 + 1/sigs1
                    slat1 = slat1 + 1/sigs2
                    srad1 = srad1 + 1/sigs3
                    scount1 = scount1 + 1
                 if (math.sqrt((float(item.fracYr)-ytime2)*(float(item.fracYr)-ytime2))) < dwin2:
                    sigs1 = float(item.eSig)*float(item.eSig)
                    sigs2 = float(item.nSig)*float(item.nSig)
                    sigs3 = float(item.uSig)*float(item.uSig)
                    vlon2 = vlon2 + float(item.ePos)/sigs1
                    vlat2 = vlat2 + float(item.nPos)/sigs2
                    vrad2 = vrad2 + float(item.uPos)/sigs3
                    slon2 = slon2 + 1/sigs1
                    slat2 = slat2 + 1/sigs2
                    srad2 = srad2 + 1/sigs3
                    scount2  = scount2  + 1
              
              if ((scount1 >= 1) & (scount2 >= 1)):
                 vlon = 1000.*(vlon2/slon2-vlon1/slon1)
                 vlat = 1000.*(vlat2/slat2-vlat1/slat1)
                 vrad = 1000.*(vrad2/srad2-vrad1/srad1)
                 slon = 1000.*math.sqrt(1/slon1+1/slon2)
                 slat = 1000.*math.sqrt(1/slat1+1/slat2)
                 srad = 1000.*math.sqrt(1/srad1+1/srad2)

              # Subtract reference values
              vlon = vlon-rlon
              vlat = vlat-rlat
              vrad = vrad-rrad
              if (results.vabs == True):
                 vrad = vrad+rrad

              # Only use displacements computed from both epochs
              if ((scount1 >= 1) & (scount2 >= 1) & (stop != 1)):

                 # Set marker color
                 if (location.stn == refsite):
                    mcolor = 'FF0000FF'
                 else:
                    mcolor = 'FF78FF78'

                 # Draw marker 
                 if analysisCenter == "JPL":
                    linkPlot = \
'"https://sideshow.jpl.nasa.gov/post/links/{:s}.html\">'.format(location.stn)
                    imgPlot = \
'"https://sideshow.jpl.nasa.gov/post/plots/{:s}.jpg\"'.format(location.stn)
                 if analysisCenter == "NGL":
                    linkPlot = \
'"http://geodesy.unr.edu/NGLStationPages/stations/{:s}.sta\"'.format(location.stn)
                    imgPlot = \
'"http://geodesy.unr.edu/tsplots/IGS14/IGS14/TimeSeries/{:s}.png"'.format(location.stn)

                 print("  <Placemark>",file=outFile1)
                 print("   <description><![CDATA[",file=outFile1)
                 #print("    <a href=\"https://sideshow.jpl.nasa.gov/post/links/{:s}.html\">".format(location.stn),file=outFile1)
                 #print("     <img src=\"https://sideshow.jpl.nasa.gov/post/plots/{:s}.jpg\" width=\"300\" height=\"300\">".format(location.stn),file=outFile1)
                 print("    <a href=" + linkPlot, file=outFile1)
                 print("     <img src=" + imgPlot + " width=\"300\" height=\"300\">",file=outFile1)
                 print("    </a>",file=outFile1)
                 print("   ]]></description>",file=outFile1)
                 print("   <Style><IconStyle>",file=outFile1)
                 print("    <color>{:s}</color>".format(mcolor),file=outFile1)
                 print("    <scale>{:f}</scale>".format(msize),file=outFile1)
                 print("    <Icon><href>https://maps.google.com/mapfiles/kml/paddle/wht-blank.png</href></Icon>",file=outFile1)
                 print("   </IconStyle></Style>",file=outFile1)
                 print("   <Point>",file=outFile1)
                 print("    <coordinates>",file=outFile1)
                 print("     {:f},{:f},0".format(lon,lat),file=outFile1)
                 print("    </coordinates>",file=outFile1)
                 print("   </Point>",file=outFile1)
                 print("  </Placemark>",file=outFile1)

                 # Draw marker 
                 print("  <Placemark>",file=outFile2)
                 print("   <description><![CDATA[",file=outFile2)
                 #print("    <a href=\"https://sideshow.jpl.nasa.gov/post/links/{:s}.html\">".format(location.stn),file=outFile2)
                 #print("     <img src=\"https://sideshow.jpl.nasa.gov/post/plots/{:s}.jpg\" width=\"300\" height=\"300\">".format(location.stn),file=outFile2)
                 print("    <a href=" + linkPlot, file=outFile2)
                 print("     <img src=" + imgPlot + " width=\"300\" height=\"300\">",file=outFile2)
                 print("    </a>",file=outFile2)
                 print("   ]]></description>",file=outFile2)
                 print("   <Style><IconStyle>",file=outFile2)
                 print("    <color>{:s}</color>".format(mcolor),file=outFile2)
                 print("    <scale>{:f}</scale>".format(msize),file=outFile2)
                 print("    <Icon><href>https://maps.google.com/mapfiles/kml/paddle/wht-blank.png</href></Icon>",file=outFile2)
                 print("   </IconStyle></Style>",file=outFile2)
                 print("   <Point>",file=outFile2)
                 print("    <coordinates>",file=outFile2)
                 print("     {:f},{:f},0".format(lon,lat),file=outFile2)
                 print("    </coordinates>",file=outFile2)
                 print("   </Point>",file=outFile2)
                 print("  </Placemark>",file=outFile2)

                 # Draw vector    
                 print("  <Placemark>",file=outFile1)
                 print("   <Style><LineStyle>",file=outFile1)
                 print("    <color>FFB478FF</color>",file=outFile1)
                 print("    <width>2</width>",file=outFile1)
                 print("   </LineStyle></Style>",file=outFile1)
                 print("   <LineString>",file=outFile1)
                 print("   <coordinates>",file=outFile1)
                 print("   {:f},{:f},0".format(lon,lat),file=outFile1)
                 print("   {:f},{:f},0".format(lon+vlon/scale/math.cos(lat*math.pi/180.),lat+vlat/scale),file=outFile1)
                 print("    </coordinates>",file=outFile1)
                 print("   </LineString>",file=outFile1)
                 print("  </Placemark>",file=outFile1)

                 # Draw sigmas
                 if (results.eon == True):
                    print("  <Placemark>",file=outFile1)
                    print("   <Style>",file=outFile1)
                    print("    <LineStyle>",file=outFile1)
                    print("     <color>FF000000</color>",file=outFile1)
                    print("     <width>2</width>",file=outFile1)
                    print("    </LineStyle>",file=outFile1)
                    print("    <PolyStyle>",file=outFile1)
                    print("     <color>FF000000</color>",file=outFile1)
                    print("     <fill>0</fill>",file=outFile1)
                    print("    </PolyStyle>",file=outFile1)
                    print("   </Style>",file=outFile1)
                    print("   <Polygon>",file=outFile1)
                    print("    <outerBoundaryIs>",file=outFile1)
                    print("     <LinearRing>",file=outFile1)
                    print("      <coordinates>",file=outFile1)

                    theta = 0
                    for k in range(0,31):
                        angle = k/30*2*math.pi
                        elon = slon*math.cos(angle)*math.cos(theta)-slat*math.sin(angle)*math.sin(theta)
                        elat = slon*math.cos(angle)*math.sin(theta)+slat*math.sin(angle)*math.cos(theta)
                        elon = (elon+vlon)/scale/math.cos(lat*math.pi/180.)
                        elat = (elat+vlat)/scale
                        print("      {:f},{:f},0".format(lon+elon,lat+elat),file=outFile1)

                    print("      </coordinates>",file=outFile1)
                    print("     </LinearRing>",file=outFile1)
                    print("    </outerBoundaryIs>",file=outFile1)
                    print("   </Polygon>",file=outFile1)
                    print("  </Placemark>",file=outFile1)

                 # Set circle color
                 if (vrad > 0):
                    lcolor = 'FF0000FF'
                    pcolor = '7F0000FF'
                 else:
                    lcolor = 'FFFF0000'
                    pcolor = '7FFF0000'

                 # Draw circle size proportional to vertical
                 print("  <Placemark>",file=outFile2)
                 print("   <Style>",file=outFile2)
                 print("    <LineStyle>",file=outFile2)
                 print("     <color>{:s}</color>".format(lcolor),file=outFile2)
                 print("     <width>1</width>",file=outFile2)
                 print("    </LineStyle>",file=outFile2)
                 print("    <PolyStyle>",file=outFile2)
                 print("     <color>{:s}</color>".format(pcolor),file=outFile2)
                 print("     <fill>1</fill>",file=outFile2)
                 print("    </PolyStyle>",file=outFile2)
                 print("   </Style>",file=outFile2)
                 print("   <Polygon>",file=outFile2)
                 print("    <outerBoundaryIs>",file=outFile2)
                 print("     <LinearRing>",file=outFile2)
                 print("      <coordinates>",file=outFile2)

                 theta = 0
                 for k in range(0,31):
                     angle = k/30*2*math.pi
                     elon = vrad*math.cos(angle)*math.cos(theta)-vrad*math.sin(angle)*math.sin(theta)
                     elat = vrad*math.cos(angle)*math.sin(theta)+vrad*math.sin(angle)*math.cos(theta)
                     elon = (elon+0)/scale/math.cos(lat*math.pi/180.)
                     elat = (elat+0)/scale
                     print("      {:f},{:f},0".format(lon+elon,lat+elat),file=outFile2)

                 print("      </coordinates>",file=outFile2)
                 print("     </LinearRing>",file=outFile2)
                 print("    </outerBoundaryIs>",file=outFile2)
                 print("   </Polygon>",file=outFile2)
                 print("  </Placemark>",file=outFile2)

                 # Make table
                 print("{:s} {:12f} {:12f} {:12f} {:12f} {:12f} {:12f} {:12f} {:12f}".format(
                 location.stn,lon,lat,vlon,vlat,vrad,slon,slat,srad),file=outFile3)

                 data_table.append([location.stn,lon,lat,vlon,vlat,vrad,slon,slat,srad])

    # Finish files
    print(" </Folder>",file=outFile1)
    print("</kml>",file=outFile1)
    outFile1.close()
    print(" </Folder>",file=outFile2)
    print("</kml>",file=outFile2)
    outFile2.close()
    outFile3.close()
    return data_table

if __name__ == '__main__':
    main()
