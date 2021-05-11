#Import dependencies.
import numpy as np
import ModularRoboticsToolkit as mrt
import sys


################
######MELT######
################


#Find the most populated line in the structure, so modules can be appended to it.
def findMeltCoordinates(structure):

    #Count how many modules are behind a face of voxels.
    zArray = np.count_nonzero(structure, axis=0)
    xArray = np.count_nonzero(structure, axis=1)
    yArray = np.count_nonzero(structure, axis=2)

    #Get the largest row of modules from each axis.
    zArrayMax = np.amax(zArray)
    xArrayMax = np.amax(xArray)
    yArrayMax = np.amax(yArray)

    #Find the largest row of modules. Set axis and array values accordingly.
    if zArrayMax > xArrayMax and zArrayMax > yArrayMax:
        axis = 0
        axisArray = zArray
    elif xArrayMax > zArrayMax and xArrayMax > yArrayMax:
        axis = 1
        axisArray = xArray
    else:
        axis = 2
        axisArray = yArray

    #Get 2D coordinates of the Melt Line. 
    optimalCoordinates = np.unravel_index(axisArray.argmax(), axisArray.shape)

    #Convert 2D coordinates to 3D coordinates, with 'm' representing the line along which to melt.
    if axis == 0:
        meltCoordinates = mrt.Location('m', optimalCoordinates[0], optimalCoordinates[1])
    elif axis == 1:
        meltCoordinates = mrt.Location(optimalCoordinates[0], 'm', optimalCoordinates[1])
    elif axis == 2:
        meltCoordinates = mrt.Location(optimalCoordinates[0], optimalCoordinates[1], 'm')

    #Return the melt coordinates to the main program. 
    return meltCoordinates

#Melt a structure along a predetermined melt line.
def melt(structure, meltCoordinates, movements):

    #Run while melt is incomplete.
    meltComplete = isMeltComplete(structure)
    while meltComplete == False:

        #Reset distances and line limiters for every sweep.
        dist = 0
        largestDist = 0
        startOfLine = getStartOfLine(structure, meltCoordinates)
        endOfLine= getEndOfLine(structure, meltCoordinates)

        #Check every voxel, find the one to move.
        for voxel in np.nditer(structure):

                #Check if a module exists in the voxel, if it does check it is not in line.
                if voxel != 0 and isModuleIn(getMeltLine(structure, meltCoordinates), voxel) == False:

                    #Find out which end of the line is closest and store the distance
                    distFromStart = abs(np.linalg.norm(np.argwhere(structure==voxel)-startOfLine.getArray()))
                    distFromEnd = abs(np.linalg.norm(np.argwhere(structure==voxel)-endOfLine.getArray()))
                    if distFromEnd > distFromStart:
                        dist = distFromStart
                        targetSpace = startOfLine
                    else:
                        dist = distFromEnd
                        targetSpace = endOfLine

                    #Find the closest gap for comparason.
                    if gapsExist(structure, meltCoordinates) == True:

                        #Find the start and ends of the melt line. 
                        meltLine = getMeltLine(structure, meltCoordinates)
                        startOfMeltLine, endOfMeltLine = getStartEndOfMeltLine(meltLine)
                        gaps = []

                        #Create a list of gaps in the melt line. 
                        counter = startOfMeltLine
                        while counter <= endOfMeltLine:
                            if meltLine[counter] == 0:
                                gaps.append(counter)
                            counter += 1

                        #For every gap we found calculate a distance and take the smallest.
                        for gap in gaps:

                            gapCoordinates = getPointOnMeltLine(gap, meltCoordinates)
                            distFromGap = abs(np.linalg.norm(np.argwhere(structure==voxel)-gapCoordinates.getArray()))

                            if distFromGap < dist:
                                dist = distFromGap
                                targetSpace = gapCoordinates

                    #Compare the distance from the start, end and gap, take the largest.
                    if dist > largestDist:
                        largestDist = dist
                        space = targetSpace
                        moduleToMoveID = int(voxel)

        #Move the module in the array.
        currentLocation = np.argwhere(structure==moduleToMoveID)
        structure[currentLocation[0,0], currentLocation[0,1], currentLocation[0,2]] = 0
        structure[space.z, space.x, space.y] = moduleToMoveID
        currentLocation = mrt.Location(currentLocation[0,0], currentLocation[0,1], currentLocation[0,2])

        #Store the movement.
        movements.storeMovement(structure, moduleToMoveID)

        #Recheck to see if the melt is complete.
        meltComplete = isMeltComplete(structure)

    #The shuffle function which checks for gaps in the melted line and fills them.
    while gapsExist(structure, meltCoordinates) == True:

            #Get up to date locations and data.
            meltLine = getMeltLine(structure, meltCoordinates)
            startOfLineLocation, endOfLineLocation = getStartEndOfMeltLine(meltLine)
            
            #Set the counter at the start of the line, so the spaces before the line begins are not picked up.
            counter = int(startOfLineLocation)
        
            #Stop at the end of the line so that spaces after the line finishes are not picked up.
            while counter <= endOfLineLocation:

                meltLine = getMeltLine(structure, meltCoordinates)

                #If there is no ID present in the voxel being searched - we have found a gap.
                if meltLine[counter] == 0:

                    #If gap is closest to the start of the line move the module from the start of the line to the gap.
                    if (counter-startOfLineLocation) < (endOfLineLocation-startOfLineLocation)/2:
                        #Move from the start of the line to the gap.
                        meltLine[counter] = meltLine[startOfLineLocation]
                        meltLine[startOfLineLocation] = 0

                    else:
                        #Visa Versa - see above comments.
                        meltLine[counter] = meltLine[endOfLineLocation]
                        meltLine[endOfLineLocation] = 0

                    #Reset counter and locations as things have changed.
                    structure = writeMeltLine(structure, meltCoordinates, meltLine)
                    movements.storeMovement(structure, int(meltLine[counter]))
                    break

                #Increment the counter by one and search the next space.
                counter += 1

    #When the while loops have both been completed, return the new structure. 
    return structure

#Use the 'm' in the melt coordinates to get the melt line.
def getPointOnMeltLine(point, meltCoordinates):

    if meltCoordinates.z == 'm':
        point = mrt.Location(int(point),  int(meltCoordinates.x), int(meltCoordinates.y))
    elif meltCoordinates.x == 'm':
        point = mrt.Location(int(meltCoordinates.z), int(point), int(meltCoordinates.y))
    elif meltCoordinates.y == 'm':
        point = mrt.Location(int(meltCoordinates.z),  int(meltCoordinates.x), int(point))

    return point

#Return the locations of both the start and end of the melt line.
def getStartEndOfMeltLine(meltLine):

    #This function differs from the individual getters of the same name.
    #Because it uses the actual location of the first and last module, not the spaces before and after them.

    #Ensure the data type is "int" to prevent issues when making comparasons. 
    meltLine = [int(i) for i in meltLine]

    #Append a zero to the end of the line, so that if there is a module at the end of the line, this method of detection will still work.
    meltLine.append(int(0))

    startOfLineFound = False 
    counter = 0

    #For every voxel in the line.
    for voxel in meltLine:

        #Start of line detector.
        if startOfLineFound == False:
            if voxel != 0:
                startOfLineLocation = counter
                startOfLineFound = True

        #End of line detector.
        if startOfLineFound == True:
            if voxel == 0 and prevVoxel != 0:
                #As the space has been detected, not the last module an adjustment must be made.
                endOfLineLocation = counter-1

        #Check the next voxel.
        prevVoxel = voxel
        counter += 1
    
    #Once the for loop is complete, return the results.
    return startOfLineLocation, endOfLineLocation

#Use a for loop to see if there are any gaps in the melt line.
def gapsExist(structure, meltCoordinates):

    meltLine = getMeltLine(structure, meltCoordinates)
    startOfLine, endOfLine = getStartEndOfMeltLine(meltLine)

    #Set the counter at the start of the line, so any spaces before the first module are not counted.
    counter = startOfLine
    
    #End the for loop at the end of the line for the same reason explained above.
    while counter <= endOfLine:
        if meltLine[int(counter)] == 0:
            return True 
        counter += 1

    return False  

#Use the 'm' location to write a melt line (type:list) to a structure (type:3D array).
def writeMeltLine(structure, meltCoordinates, meltLine):

    if meltCoordinates.z == 'm':
        structure[:,  int(meltCoordinates.x), int(meltCoordinates.y)] = meltLine
    elif meltCoordinates.x == 'm':
        structure[int(meltCoordinates.z), :, int(meltCoordinates.y)] = meltLine
    elif meltCoordinates.y == 'm':
        structure[int(meltCoordinates.z),  int(meltCoordinates.x), :] = meltLine

    return structure

#Are all modules lined melted.
def isMeltComplete(structure):

    #Count lines of modules as if facing from x, y and z axes. 
    zArray = np.count_nonzero(structure, axis=0)
    xArray = np.count_nonzero(structure, axis=1)
    yArray = np.count_nonzero(structure, axis=2)

    #Get the largest row of modules from each axis.
    zArrayMax = np.amax(zArray)
    xArrayMax = np.amax(xArray)
    yArrayMax = np.amax(yArray)

    #Find the no of modules in the longest line.
    if zArrayMax > xArrayMax and zArrayMax > yArrayMax:
        longestLine = np.amax(zArray)
    elif xArrayMax > zArrayMax and xArrayMax > yArrayMax:
       longestLine = np.amax(xArray)
    else:
        longestLine = np.amax(yArray)

    #Find the number of modules in the structure.
    totalModules = np.count_nonzero(structure)

    #See if the line is complete by comparason. 
    if longestLine == totalModules:
        return True 
    else:
        return False

#Look for a module in a list.
def isModuleIn(array, module):
    for voxel in array:
        if voxel == module:
            return True
    return False

#Get the location of the space before the start of the melt line.
def getStartOfLine(structure, meltCoordinates):

    startOfLineID = 0

    #Get the start of the line.
    for voxel in getMeltLine(structure, meltCoordinates):
        if voxel > 0:
            #Get the location of the module in the actual structure.
            startOfLineID = np.argwhere(structure==voxel)
            break

    ###This try/catch tends to catch the error if the number of modules in both structures is not the same.###
    try:
        startOfLine = mrt.Location(startOfLineID[0,0], startOfLineID[0,1], startOfLineID[0,2])
    except: 
        print('Mismatch of voxels')
        sys.exit()

    #Adjust so gets the first free space, not the first module.
    if meltCoordinates.x == 0:
        startOfLine.x -= 1
    elif meltCoordinates.y == 0:
        startOfLine.y -= 1
    elif meltCoordinates.z == 0:
        startOfLine.z -= 1

    return startOfLine

#Get the location of the space after the end of the melt line.
def getEndOfLine(structure, meltCoordinates):

    endOfLineID = 0

    #Flip and search the melt line for the first module.
    for voxel in np.flip(getMeltLine(structure, meltCoordinates)):
        if voxel > 0:
            #Find this modules location in the structure.
            endOfLineID = np.argwhere(structure==voxel)
            break

    endOfLine = mrt.Location(endOfLineID[0,0], endOfLineID[0,1], endOfLineID[0,2])

    #Adjust so gets the next free space, not the last module.
    if meltCoordinates.x == 0:
        endOfLine.x += 1
    elif meltCoordinates.y == 0:
        endOfLine.y += 1
    elif meltCoordinates.z == 0:
        endOfLine.z += 1

    return endOfLine

#Use the 'm' in the melt line location to get the melt line as a list.
def getMeltLine(structure, meltCoordinates):

    if meltCoordinates.z == 'm':
        meltLine = structure[:,  int(meltCoordinates.x), int(meltCoordinates.y)]
    elif meltCoordinates.x == 'm':
        meltLine = structure[int(meltCoordinates.z), :, int(meltCoordinates.y)]
    elif meltCoordinates.y == 'm':
        meltLine = structure[int(meltCoordinates.z),  int(meltCoordinates.x), :]

    #Ensure the values returned are integers, so comparasons perfromed on the melt line run correctly.
    meltLine = [int(i) for i in meltLine] 

    return meltLine


################
######SORT######
################


#Move the melted initial structure to the melted goal structure, do not sort yet.
def allignMeltLines(initialStructure, goalStructure, movements, widthOfLattice, goalMeltCoordinates):

    voxelsToMove = findUnmatchedModules(initialStructure, widthOfLattice, goalMeltCoordinates)
    
    #While lines don't match.
    while voxelsToMove != []:

        spaces = []
        counter = 0
        currentMeltLine = getMeltLine(initialStructure, goalMeltCoordinates)########################

        #Get the locations of empty spaces we can move into on the melt line.
        for voxel in currentMeltLine:
            if voxel == 0:
                spaces.append(getPointOnMeltLine(counter, goalMeltCoordinates))
            counter += 1

        #Find out which module (which is not in its correct space) is furthest away from its closest space.
        largestDist = 0
        smallestDist = 100000000000000000 #An alternative to this method would be preferable.

        #Find the module bet suited to be moved and store it.
        for voxelToMove in voxelsToMove:
            for space in spaces:

                #Find the distance between the space and the voxel.
                dist = abs(np.linalg.norm(np.argwhere(initialStructure==voxelToMove)-space.getArray()))

                if smallestDist == None: 
                    dist = smallestDist
                    possibleSpace = space
                    possibleModule = voxelToMove

                elif dist < smallestDist:
                    smallestDist = dist
                    possibleSpace = space
                    possibleModule = voxelToMove

            if smallestDist > largestDist:
                largestDist = dist
                moduleToMoveID = possibleModule
                spaceToMoveTo = possibleSpace

        #Move the voxel.
        oldLocation = np.argwhere(initialStructure==moduleToMoveID)
        initialStructure[oldLocation[0,0], oldLocation[0,1], oldLocation[0,2]] = 0
        initialStructure[spaceToMoveTo.getTuple()] = moduleToMoveID

        #Store the movement. 
        movements.storeMovement(initialStructure, moduleToMoveID)

        #Update the list of unmatched voxels. 
        voxelsToMove = findUnmatchedModules(initialStructure, widthOfLattice, goalMeltCoordinates)

    #When the list of unmatched voxels is empty, return the shuffled structure.
    return initialStructure

#Get a list of modules which are not in the melt goal line.
def findUnmatchedModules(initialStructure, widthOfLattice, goalMeltCoordinates):

    #Backup the melt line.
    meltLineBackup = getMeltLine(initialStructure, goalMeltCoordinates)

    #Create a blank melt line.
    meltLine = []
    counter = widthOfLattice
    while counter > 0:
        meltLine.append(0)
        counter -= 1

    #Write the blank melt line to the structure. Deleting all the modules which are in the correct location.
    structure = writeMeltLine(initialStructure, goalMeltCoordinates, meltLine)

    #The left over modules need to be moved. Store and eventually return them.
    modulesToMove = []
    for voxel in np.nditer(structure):
        if voxel > 0:
            modulesToMove.append(int(voxel))

    #Rewrite the melt line so the structure is not affected. 
    initialStructure = writeMeltLine(initialStructure, goalMeltCoordinates, meltLineBackup)

    #Return the list of displaced modules.
    return modulesToMove

#Sort the modules so that they match the melted goal line. 
def sort(initialStructure, goalStructure, meltCoordinates, movements):

    goalMeltLine = getMeltLine(goalStructure, meltCoordinates)
    meltLine = getMeltLine(initialStructure, meltCoordinates)

    #Check if the modules are already sorted.
    arraysEqual = np.array_equal(goalMeltLine, meltLine)

    while arraysEqual == False:
        meltLine = getMeltLine(initialStructure, meltCoordinates)
        arraysEqual = np.array_equal(goalMeltLine, meltLine)

        #Iterate the goal and current melt lines simultaneously, checking for inconsistencies. 
        for voxel, goalVoxel in zip(meltLine, goalMeltLine):

            hold = False

            #If an inconsistency is found, swap the two modules so that one is now in the correct location.
            if int(voxel) != int(goalVoxel):

                voxelOldLocation = mrt.Location(0,0,0)
                voxelNewLocation = mrt.Location(0,0,0)
                goalVoxelOldLocation = mrt.Location(0,0,0) 
                goalVoxelNewLocation = mrt.Location(0,0,0) 

                #First movement.
                if voxel != 0:

                    voxelOldLocation.setLocationWithTuple(np.where(initialStructure==voxel))
                    voxelNewLocation.setLocationWithTuple(np.where(goalStructure==voxel))

                    #If both spaces are occupied, activate the hold function.
                    if initialStructure[voxelOldLocation.getTuple()] != 0 and initialStructure[voxelNewLocation.getTuple()] != 0:
                        hold = True

                    #Remove first module from current spot.
                    initialStructure[voxelOldLocation.getTuple()] = 0

                    #If not entering hold, redraw first module.
                    if hold == False:
                        initialStructure[voxelNewLocation.getTuple()] = voxel
                        
                    #Record the first movement.
                    movements.storeMovement(initialStructure, voxel)

                #Second movement.
                if goalVoxel != 0:

                    goalVoxelOldLocation.setLocationWithTuple(np.where(initialStructure==goalVoxel))
                    goalVoxelNewLocation.setLocationWithTuple(np.where(goalStructure==goalVoxel))

                    #Remove second module from original spot.
                    initialStructure[goalVoxelOldLocation.getTuple()] = 0

                    #Draw second module in new spot.
                    initialStructure[goalVoxelNewLocation.getTuple()] = goalVoxel 

                    #Record the second movement.
                    movements.storeMovement(initialStructure, goalVoxel)

                #Third Movement. If the first module to be moved was put in the hold, bring it back out.
                if hold == True:

                    initialStructure[goalVoxelOldLocation.getTuple()] = voxel

                    #Record the third movement, if there was one.
                    movements.storeMovement(initialStructure, voxel)

                #Recheck if the modules are sorted.
                arraysEqual = np.array_equal(goalMeltLine, meltLine)
                meltLine = getMeltLine(initialStructure, meltCoordinates)
                break

    #Return the sorted initial structure, ready to grow.
    return initialStructure


################
######MAIN######
################


#Entry point to the program.
def main(initialStructure, goalStructure, widthOfLattice=10):

    ###SETUP###
    #Create movements object to track movements.
    #Melt goal is separate so it can be flipped and combined with overall movements.
    movements = mrt.Movements(initialStructure)
    meltGoalMovements = mrt.Movements(goalStructure)

    ###MELT###
    #Melt initial structure.
    meltCoordinates = findMeltCoordinates(initialStructure)
    initialStructure = melt(initialStructure, meltCoordinates, movements)
    #Melt goal structure.
    goalMeltCoordinates = findMeltCoordinates(goalStructure)
    goalStructure = melt(goalStructure, goalMeltCoordinates, meltGoalMovements)

    ###SORT###
    #Allign melt lines #move the decomposed initial structure to the location of the goal melt structure
    initialStructure = allignMeltLines(initialStructure, goalStructure, movements, widthOfLattice, goalMeltCoordinates)
    #Sort so current line matches goal melt line.
    initialStructure = sort(initialStructure, goalStructure, goalMeltCoordinates, movements)

    ###GROW###
    #Reverse the order in which movements are performed and swap every old and new location.
    meltGoalMovements.flip()
    #Add the new movements to the main list of movements.
    movements.combine(meltGoalMovements)

    #Return to the GUI, letting it know the MSG was a success and return the completed movements.
    return True, movements
