from common import *
from dataModel import *
from routeInfo import *
import webapp2
from google.appengine.ext.webapp import template

class saveCurrentMuniLocations(webapp2.RequestHandler):
    def get(self):
        logging.info(dir())
        f = urllib2.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=sf-muni&r=&t=0')
        output =  f.read()
        output2 = re.sub('& ','',output)
        root = ET.fromstring(output2)
        #self.response.out.write(output2)
        bus_counter = 0
        for bus in root.findall('vehicle'):
            bus_counter += 1
        import_key = VehicleImport(count = bus_counter)
        import_key.put()
        parent_key = import_key.key()
        text_array = []
        bus_save_array = []
        bus_counter = 0
        
        # Set Up bunching Data
        self.bunching_route_dict = {}
        route_info_instance = routeInfo(parent_key)
        route_dict = {}       
        for bus in root.findall('vehicle'):
            bus_data = bus.attrib
            if 'routeTag' in bus_data and 'dirTag' in bus_data and 'leadingVehicleId' not in bus_data:
                try:
                    route_info_instance.addBus(self.busDictToClass(bus_data, parent_key))
                except():
                    logging.info("PARSED BUS %s" % bus_data)
        route_info_instance.calculateRouteMetrics()
        route_info_instance.saveRouteMetrics()
        bus_object_array = route_info_instance.returnBusses()
        db.put(bus_object_array)#.put() 
        for bus in bus_object_array:
            #self.saveBus(bus)
            text_array.append('Bus %s Route %s Speed %s Next Bus %s' % 
                              (bus.vehicleId, bus.routeTag, bus.speedKmHr, bus.nextBusId))
        
        
        path = os.path.join(os.path.dirname(__file__), '../templates/bootstrap_template3.html')
        self.response.out.write(template.render(path, {"title": "Saving Muni Routes",
                                               "text": "subtext",
                                               "text_array" : text_array,
                                               "more_text":' even more text about busses'}))    
    def saveBus(self, bus):#bus_data, parent_key, next_stop, next_bus, distance_next_bus):
        bus.put()

    def busDictToClass(self, bus_data, parent_key = None, next_stop = None, next_bus = None, distance_next_bus = None):
        return MuniVehicleLocations(parent = parent_key, routeTag = bus_data['routeTag'],
                             vehicleId = str(bus_data['id']),
                             dirTag = str(bus_data['dirTag']), lat = float(bus_data['lat']),
                             lon = float(bus_data['lon']), secsSinceReport = float(bus_data['secsSinceReport']),
                             predictable = bus_data['predictable'], heading = float(bus_data['heading']),
                             speedKmHr = float(bus_data['speedKmHr']), nextStop = next_stop,
                             nextBusId = next_bus, distanceNextBus = distance_next_bus)
