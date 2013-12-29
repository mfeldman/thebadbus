    """
import logging
from dataModel import *
from common import *
from kdtree import *
import numpy as np

class CalculateBunching():
    def __init__(self, routeTag, bus_array = None, directionTag = None):
        self.routeTag = routeTag
        self.bus_array = bus_array
        self.directionTag = directionTag
        self.setStopLocations()
        #logging.info("INIT CALCULATE BUNCHING")
    def setStopLocations(self):
        # Find all stops within a route of a direction tag
        # If the direction tag is empty, find all routes
        #logging.info("Starting Stop locations for routeTag= %s directionTag %s" % (routeTag, directionTag))
        stops = db.GqlQuery("Select * from MuniStop where routeTag = :1", self.routeTag)
        stop_dict = {}
        total_distance = 0
        stop_array = []
        stop_tag_array = []
        if (stops.count() == 0):
            logging.info("NO STOPS HAVE BEEN FOUND FOR ROUTE %s " % self.routeTag)
        for stop in stops:
            total_distance += 0 if stop.dist == None else stop.dist
            #if self.directionTag == None:
            stop_dict[stop.tag] = {'lat':stop.lat, 'lon':stop.lon, 'next':stop.next,'dist': 0 if stop.dist == None else stop.dist}
            stop_array.append([stop.lat,stop.lon])
            stop_tag_array.append(stop.tag)
            #if (simple_dir_tag(stop.directionTag) == self.directionTag):
            #logging.info("Stop %s lat %s lon %s" % (stop.stopId,stop.lat, stop.lon))
            #stop_dict[stop.tag] = {'lat':stop.lat, 'lon':stop.lon, 'next':stop.next,'dist':stop.dist}
        self.stop_tree = KDTree(np.array(stop_array)) 
        self.stop_dict = stop_dict
        self.total_distance = total_distance
        self.stop_tag_array = stop_tag_array
        
    def getClosestStop(self, lat, lon, heading = None):
        closest_location, best_stop = self.stop_tree.query(np.array([lat, lon]),1)
        return self.stop_tag_array[best_stop]

    def getBusses(self, ancestor_key):
        q = MuniVehicleLocations.all()
        q.filter('routeTag =', self.routeTag) # Only Get the big imports, not the routes
        q.ancestor(ancestor_key)
        self.bus_array =  q.run(limit = count)
    
    def findBunchedBusses(self):#, bus_array, stop_dict):
        # For each bus, find the closest other bus
        # We know the closest stop to each bus.  Create a dict of stops with the busses at each of them.
        # Then use the linked list for each stop and iterate forward until we hit a stop with another bus and set the first bus to be
        # the closest one.
        pass
    def findBunchedBusses(self, bus_array):
        # For each bus find the nearest neighbor and the distnace along the track
        next_bus_dict_set = {}
        bus_id_dict = {}
        for bus in bus_array:
            #if bus['next'] not in next_bus_dict_set.keys():
            #    next_bus_dict_set[bus['next']] = set()
            next_bus_dict_set[bus['next']] = bus['id']
            bus_id_dict[bus['id']] = bus
        logging.info('Closest Stops to current busses %s ' % (str(next_bus_dict_set)))
        logging.info(self.stop_dict)
        bus_distance_dict = {}
        for bus in bus_array:
            logging.info("BUS DATA:  %s" % bus)
            next = bus['next']
            first = bus['next']
            #logging.info("NEXT STOP %s" % next)
            if next in self.stop_dict.keys():
                d = distance(bus['lat'],bus['lon'], self.stop_dict[next]['lat'], self.stop_dict[next]['lon'])
                while next == first or (next not in next_bus_dict_set.keys() and next != None):
                    if next not in self.stop_dict.keys():
                        break
                    #logging.info("NEXT STOP %s" % next)
                    d += stop_dict[next]['dist']
                    next = stop_dict[next]['next']
                d += 0 # TODO add distance to last bus
            else:
                d = None
            if next == None:
                bus_distance_dict[bus['id']] = {'distance': d, 'next_bus_id' : None}
            else:    
                bus_distance_dict[bus['id']] = {'distance': d, 'next_bus_id' : next_bus_dict_set[next]}
        return bus_distance_dict
    
    def heading_angle(self, lat1, long1, lat2, long2, earth_radius = 6371):
        pass    
"""