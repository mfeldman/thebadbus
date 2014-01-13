from __future__ import division
import copy
import logging
import cgi
import datetime
import calendar
import urllib
import urllib2
import webapp2
import random
import re
import numpy as np
import copy
import pickle
import os
import json
import xml.etree.ElementTree as ET
import time
import __builtin__
import routeInfo

def filter_keys(data, keys_wanted):
    return_array = []
    for i in data:
        return_array.append({k:i[k] for k in keys_wanted})
    return return_array

def simple_dir_tag(dirTag=''):
    m = re.match(r"[\w]+_(I|O)B",dirTag)
    try:
        return m.string[m.start(): m.end()]
    except:
        return None

def distance(lat1, long1, lat2, long2, earth_radius = 6371):
    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    degrees_to_radians = np.pi/180.0
        
    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
        
    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
    
    cos = (np.sin(phi1)*np.sin(phi2)*np.cos(theta1 - theta2) + 
           np.cos(phi1)*np.cos(phi2))
    arc = np.arccos( cos )

    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return arc * earth_radius

def heading_angle(lat1, long1, lat2, long2):
    #http://software.intel.com/en-us/blogs/2012/11/30/calculating-a-bearing-between-points-in-location-aware-apps
    degToRad = np.pi / 180.0
    
    def initial(lat1, long1, lat2, long2):
        return (bearing(lat1, long1, lat2, long2) + 360) % 360
    def final(lat1, long1, lat2, long2):
        return (bearing(lat2, long2, lat1, long1) + 180.0) % 360
    def bearing(lat1, long1, lat2, long2):
        phi1 = lat1 * degToRad;
        phi2 = lat2 * degToRad;
        lam1 = long1 * degToRad;
        lam2 = long2 * degToRad;
        return np.arctan2(np.sin(lam2-lam1)*np.cos(phi2),
                np.cos(phi1)*np.sin(phi2) - np.sin(phi1) * np.cos(phi2)*np.cos(lam2-lam1)) * 180 / np.pi
    return initial(lat1, long1, lat2, long2)