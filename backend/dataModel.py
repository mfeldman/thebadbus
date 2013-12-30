from google.appengine.ext import db
class MuniRoute(db.Model):
    """Models an individual route with bus stops"""
    tag = db.StringProperty()
    title = db.StringProperty()
    color = db.StringProperty()
    latMin = db.FloatProperty()
    latMax =db.FloatProperty()  
    lonMin = db.FloatProperty()
    lonMax = db.FloatProperty()
    totalDist = db.FloatProperty()# TODO Fill this in
    created = db.DateTimeProperty(auto_now_add=True)
    
class MuniStop(db.Model):
    routeTag = db.StringProperty()
    tag = db.IntegerProperty()
    title = db.StringProperty()
    #stopId = db.IntegerProperty()
    lat = db.FloatProperty()
    lon = db.FloatProperty()
    next = db.IntegerProperty()
    directionTag = db.StringProperty()
    dist = db.FloatProperty()
    created = db.DateTimeProperty(auto_now_add=True)

class MuniVehicleLocations(db.Model):
    routeTag = db.StringProperty()
    vehicleId = db.StringProperty()
    dirTag = db.StringProperty()
    lat = db.FloatProperty()
    lon = db.FloatProperty()
    secsSinceReport = db.FloatProperty()
    predictable = db.StringProperty()
    heading = db.FloatProperty()
    speedKmHr = db.FloatProperty()
    nextStop = db.IntegerProperty()
    nextBusId = db.StringProperty()
    distanceNextBus = db.FloatProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    
class VehicleImport(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    count = db.IntegerProperty()
    
class ImportRouteMetrics(db.Model):
    routeTag = db.StringProperty()
    count = db.IntegerProperty()
    avgSpeedKmHr = db.FloatProperty()
    avgSecsStale = db.FloatProperty()
    ratioSlowBusses = db.FloatProperty()
    countBunchedBusses = db.IntegerProperty()
    created = db.DateTimeProperty(auto_now_add=True)
