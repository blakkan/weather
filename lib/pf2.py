#! /usr/bin/python
import urllib2
from lxml import etree



uri = 'http://graphical.weather.gov/xml/sample_products/browser_interface/ndfdBrowserClientByDay.php'
args = "lat=40.77&lon=-73.98&format=24+hourly&numDays=7" #new york city
response = urllib2.urlopen(uri + '?' + args)
the_page = response.read()

#print the_page, for future reference
fh = open("output.txt", "w")
fh.write(the_page)
fh.close




context = etree.XML(the_page)

#
# Get the start times for the 24 hr periods
#
start_times_with_zone = context.xpath("//data/time-layout[@summarization='24hourly']/layout-key[.='k-p24h-n7-1']/../start-valid-time")
start_times_with_zone = [ x.text for x in start_times_with_zone ]
#convert the ISO time/date format (starting at morning or early evening, local time) to a simple day format
start_days_24 = map(lambda x: x.split('T')[0], start_times_with_zone)

#
# max temps come by 24 hour period
#
#was xpathEval
max_temps = context.xpath("//data/parameters/temperature[@type='maximum']/value")
max_temps = [ x.text for x in max_temps ]

#
# min temps come by 24 hour period
#
min_temps = context.xpath("//data/parameters/temperature[@type='minimum']/value")
min_temps = [ x.text for x in min_temps ]

#
# Basic weather type by 24 hour period
#
weathers = context.xpath("//data/parameters/weather/weather-conditions/@weather-summary")


#
# probablity of percipitation comes in 12 hr periods; we mus map it into the proper day, then take the max
# if we have multiple values
#
prob_precip_12_hr = context.xpath("//data/parameters/probability-of-precipitation[@type='12 hour']/value")
prob_precip_12_hr = [ x.text for x in prob_precip_12_hr ]
#
#convert 12 hr max probability of precip to 24 hr by consolidating pairs.
# because we usually have 2 12 hrs to take the max of, but sometimes have only one (for the current day
# or the last day)

start_times12_with_zone = context.xpath("//data/time-layout[@summarization='12hourly']/layout-key[.='k-p12h-n14-2']/../start-valid-time")
start_times12_with_zone = [ x.text for x in start_times12_with_zone ]
#convert the ISO time/date format (starting at morning or early evening, local time) to a simple day format
start_days_12 = map(lambda x: x.split('T')[0], start_times12_with_zone)

#
# Make a hash, reducing all the probabbilities for each day with the "MAX" function
#
prob_precip_24_hr = []
day_hash = dict([ ( sd, [] ) for sd in start_days_24 ])

for idx, val in enumerate(zip(start_days_12, prob_precip_12_hr)):
    if not(val[1] is None):
	if val[0] in day_hash:
            day_hash[val[0]].append(int(val[1]))

#take the max of each 12 hour precipitation prediction
day_hash.update((x, max(y)) for x,y in day_hash.items())

prob_precip_24_hr = [ day_hash[i] for i in sorted(day_hash.keys())]


#Build a consolidated list to put in the database
the_data = []
for idx, val in enumerate(start_days_24):
   the_data.append({"start":val, "max":max_temps[idx], "min":min_temps[idx], "weather":weathers[idx],
      "prob_precip":prob_precip_24_hr[idx] })

#
# put in database
#
import psycopg2
try:
    conn = psycopg2.connect("dbname='postgres' user='postgres' host='localhost' password='pass'")
    conn.set_isolation_level(3)  #want to control our own committing
except:
    print "didn't connect to database"
    exit()


cur = conn.cursor()
cur.execute("""SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'weather_prediction';""")
if cur.fetchone()[0] == 0:
    try:
        cur.execute("""CREATE TABLE weather_prediction (timestamp timestamp default current_timestamp, start VARCHAR, max INT, min INT, weather VARCHAR, prob_precip INT);""")
    except:
        print "Error when attempting to create weather_prediction table"


# We're constantly trimming off the top of the table (but not until commit)

cur.execute("""DELETE FROM weather_prediction;""")  #using delete rather than truncate, because not sure if truncate
                                                    #plays nicely with transactions


for idx, val in enumerate(start_days_24[0:6]):
    #print idx, val, max_temps[idx], min_temps[idx], weathers[idx], prob_precip_24_hr[idx] #just for debug
    try:
      cur.execute("""INSERT INTO weather_prediction (start,max,min,weather,prob_precip) VALUES ( %s, %s, %s, %s, %s );""",
        (val, max_temps[idx], min_temps[idx], weathers[idx], prob_precip_24_hr[idx]))

    except:
      print "something went awry with the database write"

conn.commit()
conn.close()
