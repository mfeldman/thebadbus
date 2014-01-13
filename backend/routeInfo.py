import logging
import common   
from dataModel import *
from kdtree import *
import numpy as np

class routeInfo():
    def __init__(self, parent_key, slow_speed_limit = 5, is_all_route = True, routeTag = 'All'):
        self.parent_key = parent_key
        self.slow_speed_limit = slow_speed_limit
        self.is_all_route = is_all_route
        self.routeTag = routeTag
        
        self.bus_array = []
        self.bus_dir_tag_dict = {}
        self.speed_array = []
        self.stale_array = []
        
        self.slow_bus_count = 0
        self.avg_speed_kmhr = 0
        self.avg_seconds_stale = 0
        self.count = 0

        self.routeInfoDict = {}
        
        self.stop_dict = {}
        self.route_distance = None
            
    def __str__(self):
        return """ %s %s %s %s""" % (self.speed_array, self.stale_array, self.count, str(self.routeInfoDict)[0:144])
    
    def addBus(self, bus, key = None):
        ## Add bus to a route object
        self.count += 1
        #logging.info("ADDING A BUS %s " % (bus))
        self.bus_array.append({"id" : bus.vehicleId, "lat" : bus.lat,
                               "lon" : bus.lon, "type" : str("bus"), 
                               "text" : "Vehicle: %s Route: %s Speed(Km/hr): %s" % 
                               (str(bus.vehicleId), str(bus.routeTag), str(bus.speedKmHr))})

        if bus.dirTag not in self.bus_dir_tag_dict:
            self.bus_dir_tag_dict[bus.dirTag] = []
        self.bus_dir_tag_dict[bus.dirTag].append(bus)

        self.speed_array.append(float(bus.speedKmHr))
        self.stale_array.append(float(bus.secsSinceReport))
    
        if float(bus.speedKmHr) <= self.slow_speed_limit:
            self.slow_bus_count += 1
        
        if self.is_all_route:
            if bus.routeTag not in self.routeInfoDict:
                self.routeInfoDict[bus.routeTag] = routeInfo(self.parent_key, 
                                                             self.slow_speed_limit,
                                                             False, bus.routeTag)
            self.routeInfoDict[bus.routeTag].addBus(bus)
            
    def calculateRouteMetrics(self):
        logging.info("STARTING CALCUALTE ROUTE METRICS")
        for r in self.routeInfoDict: # This only occurs for routes Not for ALL Routes
            logging.info('Route %s ' % (r))
            self.routeInfoDict[r].calculateRouteMetrics()
            self.routeInfoDict[r].getStopLocations()
            # Find bunchers
        if self.routeTag != 'All':
            self.bus_distance_dict = self.findBunchingInRoute()
            self.bus_distance_stop_dict = self.findClosestStop()
        self.avg_speed_kmhr     = sum(self.speed_array) / float(self.count)
        self.avg_seconds_stale  = sum(self.stale_array) / float(self.count)
        self.slow_bus_ratio     = self.slow_bus_count / (.01 + self.count)
    
        
    def findBunchingInRoute(self):
        return_dict  = {}
        for dir_tag in self.bus_dir_tag_dict:
            #logging.info(dir_tag)
            bus_loc_array = []
            bus_id_array = []

            for bus in self.bus_dir_tag_dict[dir_tag]:
                bus_loc_array.append([float(bus.lon), float(bus.lat)])
                bus_id_array.append(str(bus.vehicleId)) # TODO what is this really?
            #logging.info(bus_loc_array)
            tree = KDTree(np.array(bus_loc_array))
            for bus in self.bus_dir_tag_dict[dir_tag]:
                if len(bus_id_array) > 1: #True:#try:
                    #logging.info(tree.query(np.array([float(bus.lon), float(bus.lat)]),2))
                    closest_bus_distance, index = tree.query(np.array([float(bus.lon), float(bus.lat)]),2)
                    closest_bus = bus_id_array[index[1]]
                    dist = common.distance(bus.lon, bus.lat, 
                                    bus_loc_array[index[1]][0], bus_loc_array[index[1]][1])
                    bus.nextBusId = closest_bus
                    bus.distanceNextBus = float(dist)
                    return_dict[bus.vehicleId] = {'closest_bus' : closest_bus, 
                                       'closest_bus_distance' : dist}
                else:#except:
                    return_dict[bus.vehicleId] = {'closest_bus' : None, 
                                       'closest_bus_distance' : None}
        return return_dict
    
    def findClosestStop(self):
        return_dict  = {}
        for dir_tag in self.bus_dir_tag_dict:
            #logging.info(dir_tag)
            stop_loc_array = []
            stop_id_array = []

            for stop in self.stop_dict:
                stop_loc_array.append([float(self.stop_dict[stop]['lat']),
                                       float(self.stop_dict[stop]['lon'])])
                stop_id_array.append(str(stop)) # TODO what is this really?
            tree = KDTree(np.array(stop_loc_array))
            for bus in self.bus_dir_tag_dict[dir_tag]:
                if len(bus_id_array) > 1: #True:#try:
                    # TODO make this use bus heading to find the next stop, not the closest stop
                    logging.info("CLOSEST STOP TO BUS %s")
                    closest_bus_distance, index = tree.query(np.array([float(bus.lon), float(bus.lat)]),2)
                    for i in range(3):
                        closest_stop = stop_id_array[index[i]]
                        dist = common.distance(bus.lon, bus.lat, 
                                        stop_loc_array[index[i]][0], stop_loc_array[index[i]][1])
                        heading = common.heading_angle(bus.lon, bus.lat, stop_loc_array[index[i]][0], stop_loc_array[index[i]][1])
                        logging.info("STOP %s DIST %s HEADING %s" % (closest_stop, dist, heading))

                    bus.nextStopId = closest_stop
                    bus.distanceNextBus = float(dist)
                    return_dict[bus.vehicleId] = {'closest_stop' : closest_stop, 
                                       'closest_stop_distance' : dist}
                else:#except:
                    return_dict[bus.vehicleId] = {'closest_stop' : None, 
                                       'closest_stop_distance' : None}
        return return_dict
    
    def returnRouteMetrics(self):      
        return {'bus_array' : self.bus_array,
                'avg_speed_kmhr' : self.avg_speed_kmhr,
                'avg_seconds_stale': self.avg_seconds_stale,
                'slow_bus_ratio' : self.slow_bus_ratio}
        
    def saveRouteMetrics(self):
        for r in self.routeInfoDict:
            self.routeInfoDict[r].saveRouteMetrics()

        s = ImportRouteMetrics(parent = self.parent_key, routeTag = self.routeTag,
                               count = self.count, avgSpeedKmHr = self.avg_speed_kmhr,
                               avgSecsStale = self.avg_seconds_stale, ratioSlowBusses = self.slow_bus_ratio)
        s.put()
    
    def returnBusses(self):
        return_array = []
        for dir_tag in self.bus_dir_tag_dict:
            for bus in self.bus_dir_tag_dict[dir_tag]:
                return_array.append(bus)
        return return_array
    
    def getStopLocations(self, directionTag = None):
        # Find all stops wihtin a route fo a direction tag
        # If the direction tag is empty, find all routes
        #logging.info("Starting Stop locations for routeTag= %s directionTag %s" % (routeTag, directionTag))
        #logging.info("ACESIBLE DIRECTORIES %s for dirtag " % (dir()))
        stops = db.GqlQuery("""Select * from MuniStop where routeTag = :1""", self.routeTag)
        stop_dict = {}
        #stop_array = []
        #stop_index = []
        total_distance = 0
        
        if (stops.count() == 0):
            logging.info("NO STOPS HAVE BEEN FOUND FOR ROUTE %s " % self.routeTag)
        for stop in stops:
            total_distance += 0 if stop.dist == None else stop.dist
            #logging.info("STOP DIRECTION %s" % stop.directionTag)
            if directionTag == None:
                stop_dict[stop.tag] = {'lat':stop.lat, 'lon':stop.lon, 'next':stop.next,'dist': 0 if stop.dist == None else stop.dist}
            if (common.simple_dir_tag(stop.directionTag) == directionTag):
                #logging.info("Stop %s lat %s lon %s" % (stop.stopId,stop.lat, stop.lon))
                stop_dict[stop.tag] = {'lat':stop.lat, 'lon':stop.lon, 'next':stop.next,'dist':stop.dist}
                #stop_array.append([stop.lon, stop.lat])
                #stop_index.append(stop.id)
        self.stop_dict = stop_dict
        self.route_distance = total_distance
        #self.stop_array = stop_array
        #self.stop_index = stop_index 
        #return [stop_dict, total_distance]