import urllib2

uri = 'http://graphical.weather.gov/xml/sample_products/browser_interface/ndfdBrowserClientByDay.php'
args = "lat=40.77&lon=-73.98&format=24+hourly&numDays=7" #new york city
response = urllib2.urlopen(uri + '?' + args)
the_page = response.read()

#print the_page, for future reference
fh = open("output.txt", "w")
fh.write(the_page)
fh.close

#import libxml2
from lxml import etree

#doc = libxml2.parseDoc(the_page)
#context = doc.xpathNewContext()
context = etree.XML(the_page)

#was xpathEval
start_times_zone = context.xpath("//data/time-layout[@summarization='24hourly']/layout-key[.='k-p24h-n7-1']/../start-valid-time")
start_times_zone = [ x.text for x in start_times_zone ]


#was xpathEval
max_temps = context.xpath("//data/parameters/temperature[@type='maximum']/value")
max_temps = [ x.text for x in max_temps ]

#was xpathEval
min_temps = context.xpath("//data/parameters/temperature[@type='minimum']/value")
min_temps = [ x.text for x in min_temps ]

#was xpathEval
prob_precip_12_hr = context.xpath("//data/parameters/probability-of-precipitation[@type='12 hour']/value")
prob_precip_12_hr = [ x.text for x in prob_precip_12_hr ]

#was xpathEval
weathers = context.xpath("//data/parameters/weather/weather-conditions/@weather-summary")

#convert 12 hr max probability of precip to 24 hr by conslidating pairs
#TODO- bug here- depending on the time of day, the 12 hr times aren't starting at 6am (they're half a day early)
# Fix here or earlier when the probabilities are read.


prob_precip_24_hr = []
for idx, val in enumerate(prob_precip_12_hr):
    localVal = val
    if localVal.isdigit():  #Done at the end of list; have a nil value from NOAA there.
      if idx % 2 == 1: #if odd index, emit.  And yes, we lose the last one if it's an odd number.  This is OK.
          prob_precip_24_hr.append( str(max(int(val), int(pairmax))) )
      else:
          pairmax = val



#convert the ISO time/date format (starting at 6:00am local times) to a simple day format
start_times = map(lambda x: x.split('T')[0], start_times_zone[0:6])

#Build a consolidated list to put in the database
the_data = []
for idx, val in enumerate(start_times):
   the_data.append({"start":val, "max":max_temps[idx], "min":min_temps[idx], "weather":weathers[idx],
      "prob_precip":prob_precip_24_hr[idx] })


#
# put in database
#
import psycopg2
try:
    conn = psycopg2.connect("dbname='john' user='john' host='localhost' password='john'")
except:
    print "didn't connect to database"
    exit()


cur = conn.cursor()
cur.execute("""TRUNCATE TABLE weather;""")
for idx, val in enumerate(start_times):
    print idx, val, max_temps[idx], min_temps[idx], weathers[idx], prob_precip_24_hr[idx]
    try:
      cur.execute("""INSERT INTO weather (start,max,min,weather,prob_precip) VALUES ( %s, %s, %s, %s, %s );""",
        (val, max_temps[idx], min_temps[idx], weathers[idx], prob_precip_24_hr[idx]))

    except:
      print "something went awry with the database write"
#cur.executemany("""INSERT INTO weather(start,max,min,weather) VALUES (%(start)s, %(max)s, %(min)s, %(weather)s)""", the_data)
conn.commit()
conn.close()
