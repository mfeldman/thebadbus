import urllib2

url = "http://www.google.com/"
try:
  result = urllib2.urlopen(url)
  print(result)
except urllib2.URLError, e:
  handleError(e)