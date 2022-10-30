##---------------------------------------------------------------------
## ImportARGOS.py
##
## Description: Read in ARGOS formatted tracking data and create a line
##    feature class from the [filtered] tracking points
##
## Usage: ImportArgos <ARGOS folder> <Output feature class> 
##
## Created: Fall 2020
## Author: Joshua Meza-Fidalgo jem150@duke.edu (for ENV859)
##Created on Sun Oct 16 15:57:07 2022
##---------------------------------------------------------------------
# Import Packages
import arcpy, sys, os

arcpy.env.overwriteOutput = True

# Set input variables (Hard-wired) Hard wired means the code will read the files in at a later time. Variables are coded as full paths.
inputFile = 'V:/ARGOSTracking/Data/ARGOSData/1997dg.txt'

# Set output spatial reference
outputSR = arcpy.SpatialReference(54002) 
outputFC = "V:/ARGOSTracking/Scratch/ARGOStrack.shp"

## Prepare a new feature class to which we'll add tracking points
# Create an empty feature class; requires the path and name as separate parameters, eventually add spatial ref
outPath,outName = os.path.split(outputFC)
arcpy.CreateFeatureclass_management(outPath,outName,"POINT","","","",outputSR)

# Add TagID, LC, IQ, and Date fields to the output feature class
arcpy.AddField_management(outputFC,"TagID","LONG")
arcpy.AddField_management(outputFC,"LC","TEXT")
arcpy.AddField_management(outputFC,"Date","DATE")

# Create insert cursor
cur = arcpy.da.InsertCursor(outputFC, ['SHAPE@', 'TagID', 'LC', 'Date'])

# Construct a while loop to iterate through all lines in the datafile
# Open the ARGOS data file for reading
inputFileObj = open(inputFile,'r')

# Get the first line of data, so we can use a while loop
lineString = inputFileObj.readline()

# Start the while loop
while lineString:
    
    # Set code to run only if the line contains the string "Date: "
    if ("Date :" in lineString):
        
        # Parse the line into a list
        lineData = lineString.split()
        
        # Extract attributes from the datum header line
        tagID = lineData[0]
        obsDate = lineData[3]
        obsTime = lineData[4]
        obsLC = lineData[7]
        
        # Extract location info from the next line
        line2String = inputFileObj.readline()
        
        # Parse the line into a list
        line2Data = line2String.split()
        
        # Extract the date we need to variables
        obsLat = line2Data[2]
        obsLon= line2Data[5]
        
        # Print results to see how we're doing
        #print (tagID,obsDate,obsTime,obsLC,"Lat:"+obsLat,"Long:"+obsLon)
        
        # Try to convert coordinates to point object
        try:
            # Convert raw coordinate strings to numbers
            if obsLat[-1] == 'N':
                obsLat = float(obsLat[:-1])
            else:
                obsLat = float(obsLat[:-1]) * -1
            if obsLon[-1] == 'E':
                obsLon = float(obsLon[:-1])
            else:
                obsLon = float(obsLon[:-1]) * -1
                
            # Create point object from lat/long coordinates
            
            obsPoint = arcpy.Point()
            obsPoint.X = obsLon
            obsPoint.Y = obsLat
            
            # Convert point object to a geometry
            inputSR = arcpy.SpatialReference(4326)
            obsPointGeom = arcpy.PointGeometry(obsPoint,inputSR)
            
            # Insert feature into feature class
            feature = cur.insertRow((obsPointGeom,tagID,obsLC,obsDate.replace(".","/") + " " + obsTime))
            
        # Handle any error
        except Exception as e:
            print(f"Error adding record {tagID} to the output: {e}")
            
        
        
    # Move to the next line so the while loop progresses
    lineString = inputFileObj.readline()
    
#Close the file object
inputFileObj.close()

#Delete the cursor
del cur

