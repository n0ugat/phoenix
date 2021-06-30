############################################################################
#
# TEAM PHOENIX
#
# Virum Gymnasium (Denmark)
#
# MISSION SPACE LAB 2021: Is there a noticable difference in vegetation growth around volcanoes?
#
############################################################################
#
# The NoIR camera with the blue filter aboard the ISS takes pictures every x seconds
# and the code logs the corresponding time and coordinates for the picture in a CSV
# file as well as in the picture’s EXIF data.
# The resolution of the camera is set to max (2592 x 1944) and the pictures are
# saved in JPEG format.
# In order to maximize the number of photos taken at max resolution we will only have
# the camera take pictures at daytime. This is achieved by checking if the angle between
# the sun and the ISS is less than 90 degrees.
#
############################################################################


# IMPORT LIBRARIES
import os
import datetime
import ephem
import logging
import logzero
import numpy as np
from logzero import logger, logfile
from time import sleep
from picamera import PiCamera


# DECLARE VARIABLES
# Start time and duration
now_time = datetime.datetime.now()
start_time = datetime.datetime.now()
duration = datetime.timedelta(seconds = 3600 * 3 - 60) # Duration of the while-loop (3 hours)

# Latest TLE data
name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   21049.58925047  .00001229  00000-0  30493-4 0  9993"
line2 = "2 25544  51.6439 209.3206 0003088  29.7259  90.4857 15.48973889270212"
iss = ephem.readtle(name, line1, line2)
sun = ephem.Sun()
photo_counter = 1

# Center coordinates for "boxes" in the Pacific Ocean we want to avoid taking pictures of
pacificOceanNorthLongCenter = float(-166)
pacificOceanSouthLongCenter = float(-122)

# Camera setup
cam = PiCamera()
cam.resolution = (2592,1944) # MAX resolution for v1 camera (5 MP)


# DIRECTORY AND DATA FILE
# Sets current dir
dir_path = os.path.dirname(os.path.realpath(__file__))

# Logfile name for CSV file
logfile(dir_path+"/data01.csv")

# Custom logging.formatter
# The handler at the end specifies the format of the time data
formatter = logging.Formatter('%(asctime)-15s,%(levelname)s,%(message)s', '%Y-%m-%d %H:%M:%S');
logzero.formatter(formatter)

# Header row for the CSV file
logger.info("status, photo_counter, lat_deg, lon_deg, dotproduct")


# CREATE DICTIONARIES
# Dictionaries with the latitude and longitude coordinates of selected volcano groups in the Pacific Ocean
volcanoLat = {

    "Galapagos": float(-0.284722),
    "Hawaii": float(20.053056),
    "Easter Island": float(-27.15),
    "Tahiti": float (-17.6494)
}

volcanoLong = {
# Multiplied with cos(volcanoLat) because of lat and long relationships when measuring distance (in the while-loop)
    "Galapagos": float(-90.333889),
    "Hawaii": float(-155.854444),
    "Easter Island": float(-109.38),
    "Tahiti": float(-149.4764)
}


# DEFINE FUNCTIONS
# Function to compute the dot product (explanation below)
def dotProduct_compute():
    try:
        # Compute ISS and sun positions
        iss.compute()
        sun.compute()

        # Spherical coordinates in float radians
        # (np.cos & np.sin takes in floats)
        issra = float(iss.ra)
        issdec = float(iss.dec)
        sunra = float(sun.ra)
        sundec = float(sun.dec)

        # Spherical coordinates into two vectors with length 1:
        # vectorexample = (x,y,z) = (cos(ra) * cos(dec) , sin(ra) * cos(dec) , sin(dec))
        # Dot product between the two vectors (simplified because of sin cos relations)
        dotProduct_simple = np.cos(issdec) * np.cos(sundec) * np.cos(issra - sunra) + np.sin(issdec) * np.sin(sundec)
        return dotProduct_simple
    except Exception as e:
        logger.error("Error: Dotproduct failed: " + str(e))
        return 1 # If error the function returns a positive dotproduct resulting in a picture


# Gets the longitude and latitude, changes its format and writes it into EXIF of upcoming photo
# (modified example from Astro Pi Mission Space Lab Phase II guide).
def write_latlon(sublat, sublong):
    try:
        long_value = [float(i) for i in str(iss.sublong).split(":")]
        # Check for East or West
        if long_value[0] < 0:
            long_value[0] = abs(long_value[0])
            cam.exif_tags["GPS.GPSLongitudeRef"] = "W"
        else:
            cam.exif_tags["GPS.GPSLongitudeRef"] = "E"

        # Annotate longitude
        cam.exif_tags["GPS.GPSLongitude"] = "%d/1, %d/1, %d/10" % (long_value[0], long_value[1], long_value[2] * 10)
    except Exception as e:
        logger.error("Error: Longitude failed: " + str(e))

    try:
        lat_value = [float(i) for i in str(iss.sublat).split(":")]
        # Check for North or South
        if lat_value[0] < 0:
            lat_value[0] = abs(lat_value[0])
            cam.exif_tags["GPS.GPSLatitudeRef"] = "S"
        else:
            cam.exif_tags["GPS.GPSLatitudeRef"] = "N"

        # Annotate latitude
        cam.exif_tags["GPS.GPSLatitude"] = "%d/1, %d/1, %d/10" % (lat_value[0], lat_value[1], lat_value[2] * 10)
    except Exception as e:
        logger.error("Error: Latitude failed: " + str(e))


# Is ISS over the Pacific Ocean, and if so is it over important volcanoes
def pacific_volcanoes(lat_deg, long_deg):
    try:
        # Distance to the 'center' of Hawaii, Galapagos, Easter Island and Tahiti using pythagoras
        # When using volcanoLong we multiply by cos(volcanoLat) because of relationship between lat and long
        dist_Hawaii = ((lat_deg - volcanoLat["Hawaii"]) ** 2
                    + (np.cos(volcanoLat["Hawaii"]) * (long_deg - volcanoLong["Hawaii"])) ** 2) ** 0.5
        dist_Galapagos = ((lat_deg - volcanoLat["Galapagos"]) ** 2
                    + (np.cos(volcanoLat["Galapagos"]) * (long_deg - volcanoLong["Galapagos"])) ** 2) ** 0.5
        dist_EasterIsland = ((lat_deg - volcanoLat["Easter Island"]) ** 2
                    + (np.cos(volcanoLat["Easter Island"]) * (long_deg - volcanoLong["Easter Island"])) ** 2) ** 0.5
        dist_Tahiti = ((lat_deg - volcanoLat["Tahiti"]) ** 2
                    + (np.cos(volcanoLat["Tahiti"]) * (long_deg - volcanoLong["Tahiti"])) ** 2) ** 0.5

        # Check if we are within the north or south region of the Pacific Ocean
        # If we are within these areas and NOT close enough to volcanoes -> don't take pictures
        if (lat_deg > 0 and abs(long_deg - pacificOceanNorthLongCenter) < 34 # Within North Pacific
            and dist_Hawaii > 350 / 111 # 350/111: max radius to take pictures within (in degrees)
            or lat_deg < 0 and abs(long_deg - pacificOceanSouthLongCenter) < 40 # Within South Pacific
            and dist_Galapagos > 450 / 111
            and dist_EasterIsland > 250 / 111
            and dist_Tahiti > 350 / 111):

            return True
        else:
            return False
    except Exception as e:
        logger.error("Error: Pacific_volcanoes failed: " + str(e))
        return False # If error the function returns False resulting in a picture


# CAMERA WARMUP
cam.start_preview()
sleep(2)


# WHILE-LOOP
while (now_time < start_time + duration): # While-loop that runs for the set duration
    try:
        dotProduct = dotProduct_compute() # If the dot product < 0 -> (the angle between ISS and sun) > π / 2 and it is night on ISS
        lat_deg = iss.sublat / ephem.degree # Latitude and longitude format to degrees
        long_deg = iss.sublong / ephem.degree

        dotProduct_rounded = round(dotProduct, 4)
        lat_deg_rounded = round(lat_deg, 4)
        long_deg_rounded = round(long_deg, 4)

        if dotProduct < 0 - 0.05: # -0.05 to be sure to get every usable photo
            # It is night on the ISS -> Don't take picture
            logger.info("Night, ,%s,%s,%s" % (lat_deg_rounded, long_deg_rounded, dotProduct_rounded))

        else:
            if pacific_volcanoes(lat_deg, long_deg):
                # ISS is over the Pacific Ocean and not over a volcano -> Don't take picture
                logger.info("Over empty Pacific, ,%s,%s,%s" % (lat_deg_rounded, long_deg_rounded, dotProduct_rounded))

            else:
                # It is day at the ISS, and it is not over non-interesting parts of the Pacific Ocean
                # Take picture and log data
                write_latlon(iss.sublat, iss.sublong)
                image_name = dir_path + "/phoenix_" + str(photo_counter).zfill(3) + ".jpg"

                cam.capture(image_name)
                logger.info("TakePic,%s,%s,%s,%s" % (photo_counter, lat_deg_rounded, long_deg_rounded, dotProduct_rounded))
                photo_counter += 1

        sleep(9.6) # Time between image capture, fraction accounts for the loops runtime
        now_time = datetime.datetime.now() # Recomputes actual real time

    except Exception as e:
        logger.error("Error: " + str(e))

cam.stop_preview()
logger.info("End of mission - PHOENIX")
