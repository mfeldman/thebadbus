from common import * 
import webapp2
from dataModel import *
from google.appengine.ext import deferred

class buildMuniRoute(webapp2.RequestHandler):
    def get(self, routeName = ''):
        text = ""
        if (len(routeName)==0):
            text += "NO ROUTE GIVEN. DOING IT ALL INSTEAD"
            f = urllib2.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=routeConfig&a=sf-muni')
        else:
            f = urllib2.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=routeConfig&a=sf-muni&r=%s' % (routeName))

        #d = deleteMuniRoute()
        #d.get(routeName)
        output =  f.read()
        output2 = re.sub('& ','',output)
        root = ET.fromstring(output2)
        
        counter = 0
        for route in root.findall('route'):
            counter += 1
            if (len(routeName)==0):
                text += '<li>Building %s on count %s </li>' % (route.attrib['tag'], counter)
                deferred.defer(deferred_build_wrapper, route)
            else:
                text += self.buildAndSaveRoute(route)

        path = os.path.join(os.path.dirname(__file__), '/template/bootstrap_template.html')
        self.response.out.write(template.render(path, {"title": "Building Route",
                                               "text":text,
                                               "more_text":''}))
    def deleteMuniRoute(self, route):
        output = ''
        stops =  db.GqlQuery("SELECT * from MuniStop where routeTag = :1",
                             route)
        logging.info("Stops deleted %s " % stops.count())
        output += "%s stops deleted from %s" % (stops.count(), route)
        db.delete(stops)
        routes = db.GqlQuery("SELECT * from MuniRoute where tag = :1",
                                                        route)
        output += "%s directions deleted from %s<br>\n" % (routes.count(), route)
        db.delete(routes)
        return output
                
    def buildAndSaveRoute(self, route):
        output = ""
        #logging.info(route)
        r = route.attrib
        logging.info(self.deleteMuniRoute(r['tag']))
        ro = MuniRoute(tag = r['tag'], title = r['title'], color = r['color'], 
                       latMin = float(r['latMin']), latMax = float(r['latMax']),
                       lonMin = float(r['lonMin']), lonMax = float(r['lonMax']))
        #self.response.out.write(ro)
        ro.put()# TODO ADD THIS BACK FOR SPEED TEST  

        #  dwrite stops
        stop_dict = {}
        output += "<h2 style='color:%s'>%s</h2>" % (r['color'],r['title'])
        for stops in route.findall('stop'):
            c = stops.attrib           
            output += "<ul>%s %s</ul>" % (c['tag'], c['title']) #, c['stopId']))
            s = MuniStop(parent = ro,# TODO REMOVE THIS COMMENT
                         routeTag = r['tag'],
                         #stopId = int(c['stopId']),
                         tag=int(c['tag']), title = c['title'],
                         lat = float(c['lat']), lon = float(c['lon']),
                         next = None, dist = None, directionTag = None)
            stop_dict[int(c['tag'])] = s
        
        prev = None
        #logging.info(stop_dict.keys())
        for dir in route.findall('direction'):
            d = dir.attrib
            output += '<li>%s</li></br>\n' % d['tag']
            for stops in dir.findall('stop'):
                cur = int(stops.attrib['tag'])
                if prev != None:
                    stop_dict[prev].next = int(stops.attrib['tag'])
                    stop_dict[prev].dist = round(distance(stop_dict[prev].lat,
                                            stop_dict[prev].lon, stop_dict[cur].lat,
                                            stop_dict[cur].lon),4)
                    stop_dict[prev].directionTag = d['tag'] 
                    stop_dict[prev].put()
                else:
                    pass
                prev = int(stops.attrib['tag'])
            stop_dict[prev].directionTag = d['tag']
            stop_dict[prev].put()
        output += str(stop_dict)  +" </br>\n"

        return output


def deferred_build_wrapper(routeName):
    A = buildMuniRoute()
    output = A.buildAndSaveRoute(routeName)
    logging.info(output)
    return output

