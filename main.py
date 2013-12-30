#!/usr/bin/python2.7

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
import time
import math
import xml.etree.ElementTree as ET
import __builtin__
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import taskqueue
from google.appengine.ext import deferred
from backend.routeInfo import *
from backend.dataModel import *
from backend.buildMuniRoute import *
from backend.saveLocations import *
from backend.kdtree import *

tz_offset = 7 # UTC - PDT

class index(webapp2.RequestHandler):
    def get(self):
        self.slow_speed_limit = 5
        path = os.path.join(os.path.dirname(__file__), 'templates/bootstrap_template_index.html')
        t = time.time()
        last_key = getKeys()
        #self.response.out.write('Time elapsed: %s<br>' % (time.time() - t))
        BDA = BusDataAccess()
        
        routeTag = 'All'
        filter = False
        historic_count = 1000
            
        current_bus_locations = BDA.currentBusLocations(last_key, filter)
        #self.response.out.write('Time elapsed: %s<br>' % (time.time() - t))
        recent_bus_data = BDA.recentBusData(historic_count, routeTag, False, 'Array')
        #self.response.out.write('Time elapsed: %s<br>' % (time.time() - t))
        #logging.info(recent_bus_data)
        #self.response.out.write(BDA.recentBusBins())
        count_array             = recent_bus_data['count']
        avg_speed_kmhr_array    = recent_bus_data['avgSpeedKmHr']
        slow_bus_ratio_array    = recent_bus_data['ratioSlowBusses']
        
        current_route_data = BDA.recentBusData(100 , filter, last_key, 'Dict')
        all_route_data = BDA.recentBusData(100 , False, last_key, 'Dict')

        #self.response.out.write('Total render time: %s<br>' % (time.time() - t))
        
        self.response.out.write(template.render(path, {"title": "The Bad Bus",
                                                       "bus_array_str" : json.dumps(current_bus_locations),
                                                       "bus_history_json" : json.dumps(count_array),
                                                       "bus_count": count_array[-1][1],
                                                       "avg_speed_kmhr_array" : json.dumps(avg_speed_kmhr_array),
                                                       "slow_bus_ratio_array" : json.dumps(slow_bus_ratio_array),
                                                       "route_table" : self.dict_array_to_table(current_route_data),
                                                       "route_array" : json.dumps(all_route_data.keys())
                                                       }))
    def dict_array_to_table(self, json_array):
        xml_output = "<table cellpadding='0' cellspacing='0' border='0' id='dtable'><thead><tr><th>"
        xml_output += '</th><th>'.join(['Route','Number Busses','Avg Speed (Km/Hr)','Ratio Slow Busses'])
        xml_output += '</th></tr></thead>\n<tbody>'
        for routeTag in json_array:
            row = json_array[routeTag]
            logging.info('ROW FOR ROUTETAG %s' % routeTag)
            logging.info(row)
            xml_output += '<tr><td><a href="/route/%s">%s</a></td><td>' % (row['route'], row['route']) 
            xml_output += '</td><td>'.join([str(s) for s in [row['count'],row['avgSpeedKmHr'],row['ratioSlowBusses']]]) + '</td></tr>\n'
            
        xml_output += '</tbody></table>\n'
        return xml_output

class displayRoute(webapp2.RequestHandler):
    def get(self, routeTag):
        self.slow_speed_limit = 5
        path = os.path.join(os.path.dirname(__file__), 'templates/bootstrap_template_index.html')
        t = time.time()
        last_key = getKeys()
        #self.response.out.write('Time elapsed: %s<br>' % (time.time() - t))
        BDA = BusDataAccess()
        historic_count =  100
            
        current_bus_locations = BDA.currentBusLocations(last_key, routeTag)
        #self.response.out.write('Time elapsed: %s<br>' % (time.time() - t))
        recent_bus_data = BDA.recentBusData(historic_count, routeTag, False, 'Array')
        count_array             = recent_bus_data['count']
        avg_speed_kmhr_array    = recent_bus_data['avgSpeedKmHr']
        slow_bus_ratio_array    = recent_bus_data['ratioSlowBusses']
        
        current_route_data = BDA.recentBusData(100 , routeTag, last_key, 'Dict')
        all_route_data = BDA.recentBusData(100 , False, last_key, 'Dict') # All busses

        #self.response.out.write('Total render time: %s<br>' % (time.time() - t))        
        self.response.out.write(template.render(path, {"title": "Route %s" % (routeTag),
                                                       "bus_array_str" : json.dumps(current_bus_locations),
                                                       "bus_history_json" : json.dumps(count_array),
                                                       "bus_count": count_array[-1][1],
                                                       "avg_speed_kmhr_array" : json.dumps(avg_speed_kmhr_array),
                                                       "slow_bus_ratio_array" : json.dumps(slow_bus_ratio_array),
                                                       "route_table" : self.dict_array_to_table(current_bus_locations),
                                                       "route_array" : json.dumps(all_route_data.keys())
                                                       }))
        
    def dict_array_to_table(self, array_of_dicts):
        xml_output = "<table cellpadding='0' cellspacing='0' border='0' id='dtable'><thead><tr><th>"
        xml_output += '</th><th>'.join(['Vehicle Id','Speed (Km/Hr)','Heading', 'Next Bus','Direction Tag','Distance Next Bus'])
        xml_output += '</th></tr></thead>\n<tbody>'
        for row in array_of_dicts:
            if type(row['distanceNextBus']) is float:
                dist = round(row['distanceNextBus'],2)
            else:
                dist = 'None'
            xml_output += '<tr><td><a href="/vehicleId/%s">%s</a></td><td>' % (row['vehicleId'], row['vehicleId'])
            xml_output += '</td><td>'.join([str(s) for s in [row['speedKmHr'],row['heading'],row['nextBusId'],row['dirTag'],dist]])
            xml_output += '</td></tr>\n'
            
        xml_output += '</tbody></table>\n'
        return xml_output
class displayVehicleId(webapp2.RequestHandler):
    def get(self, vehicleId):
        path = os.path.join(os.path.dirname(__file__), 'templates/bootstrap_template_index.html')
        t = time.time()
        last_key = getKeys()
        #self.response.out.write('Time elapsed: %s<br>' % (time.time() - t))
        BDA = BusDataAccess()
        historic_count =  100
            
        current_bus_locations = BDA.recentLocationsVehicleId(vehicleId, 100)
        current_bus_locations_simple = filter_keys(current_bus_locations, ['lat','lon','text','speedKmHr','heading','type','vehicleId'])
        avg_speed_kmhr_array    = self.locations_to_chart_data(current_bus_locations)
        all_route_data = BDA.recentBusData(100 , False, last_key, 'Dict') # All busses
        route_table =  self.dict_array_to_table(current_bus_locations)
        #self.response.out.write('Total render time: %s<br>' % (time.time() - t))        
        self.response.out.write(template.render(path, {"title": "Vehicle %s" % (vehicleId),
                                                       "bus_array_str" : json.dumps(current_bus_locations_simple),
                                                       "bus_count": len(current_bus_locations),
                                                       "avg_speed_kmhr_array" : json.dumps(avg_speed_kmhr_array),
                                                       "route_table" : route_table,
                                                       "route_array" : json.dumps(all_route_data.keys())
                                                       }))

    def dict_array_to_table(self, array_of_dicts):
        xml_output = "<table cellpadding='0' cellspacing='0' border='0' id='dtable'><thead><tr><th>"
        xml_output += '</th><th>'.join(['Route','Created','Speed (Km/Hr)','Heading', 'Next Bus','Distance To Next Bus (Km)'])
        xml_output += '</th></tr></thead>\n<tbody>'
        for row in array_of_dicts:
            if type(row['distanceNextBus']) is float:
                dist = round(row['distanceNextBus'],2)
            else:
                dist = 'None'
            xml_output += '<tr><td><a href="/route/%s">%s</a></td><td>' % (row['routeTag'], row['routeTag'])
            xml_output += '</td><td>'.join([str(s) for s in ['%s' % (row['created']),row['speedKmHr'],row['heading'],row['nextBusId'], dist]])
            xml_output += '</td></tr>\n'
            
        xml_output += '</tbody></table>\n'
        return xml_output
    
    def locations_to_chart_data(self, data):
        speed_array = []
        for i in data:
            t = calendar.timegm(i['created'].utctimetuple()) * 1000 - tz_offset * 60 * 60 * 1000
            speed_array.append([t,i['speedKmHr']])
        speed_array.reverse()
        return speed_array
    
class BusDataAccess():
    def recentBusData(self, count = 1000, filter = 'All', ancestor_key = False, output = 'Array'):
        #get array with time stamps and number of busses
        time_start = time.time()
        q = ImportRouteMetrics.all()
        if filter: # Only take the 'ALL' Tag
            q.filter('routeTag =', filter) # Only Get the big imports, not the routes
        if ancestor_key:
            q.ancestor(ancestor_key)
        q.order('-created')
        
        bus_data =  q.run(limit = count)

        #self.response.out.write('Time elapsed: %s<br>' % (time.time() - time_start))
        if output == 'Array':
            return_data = {'count':[],'avgSpeedKmHr':[],"ratioSlowBusses":[],"created":[]}
            for i in bus_data:
                #logging.info(time.time() - time_start)
                t = calendar.timegm(i.created.utctimetuple()) * 1000 - tz_offset * 60 * 60 * 1000
                return_data['count'].append([t, i.count])
                return_data['avgSpeedKmHr'].append([t, i.avgSpeedKmHr])
                return_data['ratioSlowBusses'].append([t, i.ratioSlowBusses])
            return_data['count'].reverse()
            return_data['avgSpeedKmHr'].reverse()
            return_data['ratioSlowBusses'].reverse()
            #self.response.out.write('DATA TYPE BUS DATA %s </br>' % (cgi.escape(str(type(bus_data)))))
            #self.response.out.write('recent bus data Time elapsed: %s<br>' % (time.time() - time_start))
            return return_data
        elif output == 'Dict':
            return_data = {}
            for i in bus_data:
                return_data[i.routeTag] = {'route': i.routeTag, 'count':i.count, 'avgSpeedKmHr': round(i.avgSpeedKmHr,2), 'ratioSlowBusses' : round(i.ratioSlowBusses,2)}
            #self.response.out.write('Time elapsed: %s<br>' % (time.time() - time_start))
            return return_data

    def currentBusLocations(self, ancestor_key, filter =  False, count = 10):
        q = MuniVehicleLocations.all()
        q.ancestor(ancestor_key)
        return_array = []
        if filter != False:
            count = 1000
        fetched_results = q.fetch(limit = count)
        for s in fetched_results:
            if s.routeTag == filter or filter == False:
                return_array.append({"lat":s.lat, "lon":s.lon,
                                       "type" : "bus",
                                       "text" : "Speed %s Km/Hr" % (s.speedKmHr),
                                       "speedKmHr": s.speedKmHr,
                                       "heading" : s.heading,
                                       "vehicleId": s.vehicleId,
                                       "nextBusId": s.nextBusId,
                                       "distanceNextBus": s.distanceNextBus,
                                       "routeTag": s.routeTag,
                                       "dirTag": s.dirTag})
        return return_array
    def recentBusBins(self, count = 10000, bin_round = 0.01):
        q = MuniVehicleLocations.all()
        q.order('-created')
        fetched_results = q.fetch(limit = count)
        bin_dict = {}
        for s in fetched_results:
            lon_bin, lat_bin = math.floor(s.lon / bin_round) * bin_round, math.floor(s.lat / bin_round) * bin_round
            if lon_bin not in bin_dict:
                bin_dict[lon_bin] = {}
            if lat_bin not in bin_dict[lon_bin]:
                bin_dict[lon_bin][lat_bin]=[]
            bin_dict[lon_bin][lat_bin].append(s.speedKmHr)
        
        return_dict = {}
        for x in bin_dict:
            for y in bin_dict[x]:
                if x not in return_dict:
                    return_dict[x] = {}
                return_dict[x][y] = {'count' : len(bin_dict[x][y]), 'avg_speed': sum(bin_dict[x][y]) / len(bin_dict[x][y])}
        return return_dict
    def recentLocationsVehicleId(self, vehicleId, count = 1000):
        q = MuniVehicleLocations.all()
        q.filter('vehicleId = ', vehicleId)
        q.order('-created')
        fetched_results = q.fetch(limit = count)
        return_array = []
        for s in fetched_results:
            return_array.append({"lat":s.lat, "lon":s.lon,
                        "type" : "bus",
                        "text" : "Speed %s Km/Hr" % (s.speedKmHr),
                        "created" : s.created,
                        "speedKmHr": s.speedKmHr,
                        "heading" : s.heading,
                        "vehicleId":s.vehicleId,
                        "nextBusId":s.nextBusId,
                        "distanceNextBus":s.distanceNextBus,
                        "routeTag":s.routeTag})
        return return_array


class deleteMuniRoute(webapp2.RequestHandler):
    def get(self, routeName):
        stops =  db.GqlQuery("SELECT * from MuniStop where routeTag = :1",
                             routeName)
        logging.info("Stops deleted %s " % stops.count())
        self.response.out.write("<li>%s stops deleted</li><br>\n" % 
                                (stops.count()))
        db.delete(stops)
        routes = db.GqlQuery("SELECT * from MuniRoute where tag = :1",
                                                        routeName)
        self.response.out.write("<li>%s directions deleted</li><br>\n" % 
                                (routes.count()))
        db.delete(routes)

def findTotalDist(stop_dict):
    # Sum up distance along stop dist
    pass

def getKeys(offset = 0, limit = 1):
    q = VehicleImport.all()
    q.order('-created')
    ancestor_key =  None
    for p in q.run(offset = offset, limit = limit):
        ancestor_key = p.key()
    return ancestor_key
 
app = webapp2.WSGIApplication([
                               (r'/buildMuniRoute/(.*)',buildMuniRoute),
                               (r'/deleteMuniRoute/(.*)',deleteMuniRoute),
                               (r'/saveCurrentMuniLocations',saveCurrentMuniLocations),
                               (r'/route/(.*)',displayRoute),
                               (r'/vehicleId/(.*)',displayVehicleId),
                               ('/',index),
                               ],
                              debug=False)
