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

# Set input variables 
inputFolder = sys.argv[1] 
outputSR = sys.argv[2]
lcFilters = sys.argv[3] #ex 1;2;3
outputFC = sys.argv[4]

# Create a list of files in the user provided folder
inputFiles = os.listdir(inputFolder)

# Split multistring into list
lcValues = lcFilters.split(';')

## Prepare a new feature class to which we'll add tracking points
# Create an empty feature class; requires the path and name as separate parameters, eventually add spatial ref
outPath,outName = os.path.split(outputFC)
arcpy.CreateFeatureclass_management(outPath,outName,"POINT","","","",outputSR)

# Add TagID, LC, IQ, and Date fields to the output feature class
arcpy.AddField_management(outputFC,"SourceFile","TEXT")
arcpy.AddField_management(outputFC,"TagID","LONG")
arcpy.AddField_management(outputFC,"LC","TEXT")
arcpy.AddField_management(outputFC,"Date","DATE")

# Create insert cursor
cur = arcpy.da.InsertCursor(outputFC, ['SHAPE@','SourceFile','TagID', 'LC', 'Date'])

# Create counter variables
lc_filter_count = 0
pt_error_count = 0

# Iterate through each input file
for inputFile in inputFiles:
    # Skip README
    if inputFile == 'README.txt': continue

    # Give user a status update
    arcpy.AddMessage(f'Working on file {inputFile}')
    
    # Add path to input file(s)
    inputFile = os.path.join(inputFolder, inputFile)
    
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
            
            # Skip record if not in LC value list
            if obsLC not in lcValues:
                # Add to the lc tally
                lc_filter_count += 1
                # Move to next record
                lineString = inputFileObj.readline()
                # Skip rest of code block
                continue
            
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
                feature = cur.insertRow((obsPointGeom,os.path.basename(inputFile),
                                         tagID,obsLC,
                                         obsDate.replace(".","/") + " " + obsTime))
                
            # Handle any error
            except Exception as e:
                pt_error_count =+ 1
                print(f"Error adding record {tagID} to the output: {e}")
            
        # Move to the next line so the while loop progresses
        lineString = inputFileObj.readline()
        
    #Close the file object
    inputFileObj.close()
    
#Delete the cursor
del cur

# Give info to user
if lc_filter_count > 0:
    arcpy.AddWarning(f'{lc_filter_count} records not meeting LC class')
else:
    arcpy.AddMessage("No records omitted because of LC value")
    
    
if pt_error_count > 0:
    arcpy.AddWarning(f'{pt_error_count} records had no location data')
