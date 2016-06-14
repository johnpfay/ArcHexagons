##----------------------------------------------------------------------------------
## HexagonsFromFeatureSet.py
##
## Description: Creates a set of hexagons with the extent of the supplied feature
##              class. The number of hexagons created can be determined multiple 
##              ways: by specifying the desired width of the hexagon, by specifying 
##              the minimnum total number of hexagons desired, or by specifying the 
##              number of hexagons desired along either the X or Y axis. The actual 
##              number produced may be larger to ensure that the entire area is 
##              covered. 
##
## Created: December 2008
## Author:  John Fay, Nicholas School, Duke University
##----------------------------------------------------------------------------------

import string, os, sys, math, arcgisscripting

gp = arcgisscripting.create()
gp.AddMessage("Starting hexagons")

try:
    #Get Input Feature Class
    inputFC = sys.argv[1]
    hexWidth = sys.argv[2]
    hexCount = sys.argv[3]
    hexXCount = sys.argv[4]
    hexYCount = sys.argv[5]
    outputFC = sys.argv[6]
    
    #Get corners from input feature class
    desc = gp.Describe(inputFC)
    corners = desc.Extent.split(" ")
    xMin = float(corners[0])
    yMin = float(corners[1])
    xMax = float(corners[2])
    yMax = float(corners[3])
    if xMax <= xMin: #Reverse the values
        xTmp = xMax;    xMax = xMin;    xMin = xTmp
    if yMax <= yMin: #Reverse the values
        yTmp = yMax;    yMax = yMin;    yMin = yTmp
    gp.AddMessage("Width: " + str(xMax - xMin) + ", Height: " + str(yMax - yMin))

    ## IF HEXAGON WIDTH IS NOT SUPPLIED, DETERMINE FROM OTHER OPTIONS:
    if hexWidth == "#":
        ## Calculate width to fit specific number of hexagons into area
        if hexCount <> "#": # Calculate width from the total that can fit w/in extent
            gp.AddMessage("Breaking area into %s hexagons" %str(hexCount))
            totArea = (xMax - xMin) * (yMax - yMin) 
            hexArea = totArea / int(hexCount)
            # Area of a hexagon is 3*math.sqrt(3)/2 * face^2
            face = math.sqrt((2 * hexArea)/(3 * math.sqrt(3)))
            #hexWidth = math.sqrt((2*hexArea)/math.sqrt(3))
            hexWidth = face * 2
        ## Calculate width to fit specific number of hexagons along X axis
        elif hexXCount <> "#":
            gp.AddMessage("Breaking area into %s hexagons along X axis" %str(hexXCount))
            hexWidth = ((xMax - xMin) / int(hexXCount)) * 1.5 # 1.5 faces per hexagon
       ## Calculate width to fit specific number of hexagons along X axis
        elif hexYCount <> "#":
            gp.AddMessage("Breaking area into %s hexagons along Y axis" %str(hexYCount))
            hexHeight = (yMax - yMin) / int(hexYCount)
            hexWidth = (hexHeight / 2.0) / (math.sin(math.pi/3.0)) * 2
        else:
            raise Exception, "Hexagon width cannot be specified"
    else:
        gp.AddMessage("Creating hexagons of width %s" %str(hexWidth))
        hexWidth = int(hexWidth)
        if int(hexWidth) > (xMax - xMin) or hexWidth > (yMax - yMin):
            gp.AddMessage("Hexagon width is larger than extent!")
            raise Exception, "Hexagons too wide for extent"
    
    #Name of output feature class
    outputWS = os.path.dirname(outputFC)
    if outputWS == "":
        outputWS = os.path.dirname(inputFC)
    outputFN = os.path.basename(outputFC)

    #Output Spatial reference 
    outputSR = desc.SpatialReference 

    # CALCULATE HEXAGON DIMENSIONS
    face = hexWidth / 2.0              # Length of one face
    gap = face / 2.0                   # Lenght of a gap
    h2 = face * math.sin(math.pi/3.0)  # Height of an enclosing triangle (1/2 height)
                                       #  hexFace = (hexWidth/2) / cosine(30*)
                                       #  30 degrees = ((30/180) * pi) radians = pi/6
                                       #  hexFace = hW2 / cos(pi/6)
    hexHeight = h2 * 2.0               # Height of the hexagon
                   
    #CREATE THE HEXAGON FEATURE CLASS
    gp.toolbox = "management"
    #Delete, if the feature class already exists
    if gp.Exists(outputFC):
        print "Deleting " + outputFC + "..."
        gp.AddMessage("Overwriting " + outputFC + "...")
        gp.Delete(outputFC)
    #Create a new empty feature class
    print "Creating new feature class " + outputFC
    gp.AddMessage("Creating " + outputFC + " to contain hexagon features...")
    gp.CreateFeatureclass(outputWS, outputFN, "Polygon", "#", "#", "#", outputSR)
    #Get some information about the new featureclass for later use.
    outDesc = gp.describe(outputFC)
    shapefield = outDesc.ShapeFieldName

    #Initialize the hexagon coordinates
    xCur = xMin    #Start Xs at left side (min)
    yCur = yMax    #Start Ys at top side (max)
    oddCol = 1      #Toggle for offsetting row
    idCounter = 1   #Hexagon ID counter

    #Open and insert cursor for the new feature class.
    cur = gp.InsertCursor(outputFC)
    # create the cursor and objects necessary for the geometry creation
    pnt = gp.createobject("point")
    lineArray = gp.createobject("Array")
    #Loop from left to right
    while xCur <= (xMax):
        #Loop from top row to bottom
        while yCur >= (yMin):
            #Create the hexagon vertices relative to (xCur, yCur)
            pnt.id = 1; pnt.X = xCur;               pnt.Y = yCur + h2;  lineArray.add(pnt)
            pnt.id = 2; pnt.X = xCur + face;        pnt.Y = yCur + h2;  lineArray.add(pnt)
            pnt.id = 3; pnt.X = xCur + face + gap;  pnt.Y = yCur;       lineArray.add(pnt)
            pnt.id = 4; pnt.X = xCur + face;        pnt.Y = yCur - h2;  lineArray.add(pnt)
            pnt.id = 5; pnt.X = xCur;               pnt.Y = yCur - h2;  lineArray.add(pnt)
            pnt.id = 6; pnt.X = xCur - gap;         pnt.Y = yCur;       lineArray.add(pnt)
            pnt.id = 7; pnt.X = xCur;               pnt.Y = yCur + h2;  lineArray.add(pnt)

            #Add the linearray to the featureclass
            feat = cur.NewRow()
            #feat.SetValue(shapefield, lineArray)
            feat.shape = lineArray
            feat.ID = idCounter
            idCounter = idCounter + 1
            cur.InsertRow(feat)
            lineArray.RemoveAll()
            
            #Decrement yCur
            yCur = yCur - (hexHeight)
            
        #Increment xCur
        xCur = xCur + face + gap
        if oddCol == 1:
            oddCol = 0
            yCur = yMax - h2
        else:
            oddCol = 1
            yCur = yMax
        
    del cur, feat
    #Refresh the catalog
    gp.RefreshCatalog(os.path.dirname(outputFC))
    gp.AddMessage("Finished! %d hexagons created" %gp.GetCount(outputFC))
    
    
except Exception, ErrorDesc:
    gp.AddMessage("Error occurred")
    gp.GetMessages()
    if cur:
        del cur
    if feat:
        del feat
        