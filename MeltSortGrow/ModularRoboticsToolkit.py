#Import dependencies.
import numpy as np
import matplotlib.pyplot as plt
import sys, os, inspect

#Object for storing a 3D cartesian coodinate.
class Location():

    #Initialise with 3 coordinates, can be zero if need be.
    def __init__(self, z, x, y):
        self.x = x
        self.y = y
        self.z = z

    #Get the coordinates as a list. 
    def getArray(self):
        return np.array([self.z, self.x, self.y])

    #Get the coordinates as a human readable string.
    def getString(self):
        return ('(' + str(self.x) + ',' + str(self.y) + ',' + str(self.z) + ')')

    #Set the location.
    def setLocation(self, z, x, y):

        if str(z) != 'm':
            if str(z) != 'h': z = int(z)
            if str(x) != 'h': x = int(x)
            if str(y) != 'h': y = int(y)

        self.z = z
        self.x = x
        self.y = y

    #Set the location with an array type used by NumPy. 
    def setLocationWithArray(self, npArray):

        z = npArray[0,0]
        x = npArray[0,1]
        y = npArray[0,2]

        self.setLocation(z, x, y)

    #Set the location with tuples, as used by NumPy. 
    def setLocationWithTuple(self, tuple):
        z = tuple[0]
        x = tuple[1]
        y = tuple[2]

        self.setLocation(z, x, y)

    #Get the coodinate as a tuple, for NumPy inputs.
    def getTuple(self):
        return (self.z, self.x, self.y)

#The class created to solve various movement recording issues. 
#Detects and stores all movements
class Movements():

    #Initialise with a structure and a the default structure size. 
    def __init__(self, initialStructure, widthOfLattice=10):

        self.movements = []
        self.structure = np.zeros((widthOfLattice, widthOfLattice, widthOfLattice))

        #Create an isolated object to store the structure in, preventing unwanted changes.
        for voxel in np.nditer(initialStructure):
            if voxel != 0:
                self.structure[np.where(initialStructure==voxel)] = voxel

    #Find the amount of movements in the array.
    def legnth(self, string=False):
        if string == True:
            return str(int(np.size(self.movements)/3))
        else:
            return int(np.size(self.movements)/3)

    #Compares old/new array to store movement.
    def storeMovement(self, newStructure, voxelMoved):

        #Find out whats changed and if the voxel has entered the hold.
        oldLocation = Location(0,0,0)
        newLocation = Location(0,0,0)

        #See if module is entering hold.
        enteringHold = True 
        for voxel in np.nditer(newStructure):
            if voxel == voxelMoved:
                enteringHold = False
                break

        #See if module is leaving hold.
        leavingHold = True
        for voxel in np.nditer(self.structure):
            if voxel == voxelMoved:
                leavingHold = False
                break

        #Store the hold movement if appropriate.
        if enteringHold == True:
            newLocation.setLocation('h','h','h')
        elif enteringHold == False:
            newLocation.setLocationWithTuple(np.where(newStructure==voxelMoved))

        #Store the hold movement if appropriate.
        if leavingHold == True:
            oldLocation.setLocation('h','h','h')
        elif leavingHold == False:
            oldLocation.setLocationWithTuple(np.where(self.structure==voxelMoved))

        #Store the movement
        movement = []
        movement.append(voxelMoved)
        movement.append(oldLocation)
        movement.append(newLocation)

        #Append the movement to the movements array.
        self.movements = np.append(self.movements, movement)
        self.movements = np.reshape(self.movements, (-1, 3))

        #Apply the movement to the stored structure
        self.structure = applyMovement(self.structure, movement)

    #Reverse that array for the grow phase. 
    def flip(self):

        #Flip the order movements are carried out in.
        self.movements = np.flip(self.movements, axis=0)

        #Swap the old and new positions.
        for step in self.movements:

            newLocation = step[1]
            oldLocation = step[2]

            step[1] = oldLocation
            step[2] = newLocation

    #Combine two movements arrays, for after grow phase has been flipped. 
    def combine(self, newMovements):

        for newMovement in newMovements.getMovements():

            self.movements = np.append(self.movements, newMovement)
            self.movements = np.reshape(self.movements, (-1, 3))

    #Get array of movements.
    def getMovements(self):
        return self.movements
    
    #Get a single movement, counts from zero.
    def getMovement(self, stepNo, string=False):

        step = self.movements[stepNo]
        moduleToMoveID = step[0]
        oldLocation = step[1]
        newLocation = step[2]

        if string == True:
            return str(moduleToMoveID), oldLocation.getString(), newLocation.getString
        else:
            return moduleToMoveID, oldLocation, newLocation
        
#Creates an array to be stepped through after manipulation is compete for the GUI to display to the user.
class StepStructure():

    #Initialise with the initial structure, completed list of movements and the default lattice width.
    def __init__(self, structure, movements, widthOfLattice = 10):

        self.structure = structure
        self.step = 0
        self.movements = movements
        self.noOfSteps = self.movements.legnth(string=True)

    #Move a step and keep track of where the step counter is.
    def moveStep(self, direction):

        if direction == 'forward': 
            self.step += 1
        elif direction == 'backward': 
            self.step -= 1

        #Quit if reached last movement.
        if self.step > self.movements.legnth(): 
            self.step -= 1
            return False, ''
        if self.step < 0: 
            self.step += 1
            return False, ''

        #Get individual movement objects using mrt.
        moduleToMoveID, oldLocation, newLocation = self.movements.getMovement(self.step-1)

        #Make the movement, get total no of steps for display and increment counter.
        self.structure = applyMovement(self.structure, self.movements.getMovement(self.step-1))

        #Prepare message for outbox showing what has happened.
        moduleToMoveID = str(moduleToMoveID)
        if newLocation.x == 'h':
            message = 'Step ' + str(self.step) + '/' + self.noOfSteps + ' Module ID:' + moduleToMoveID +' entering holding.'
        elif oldLocation.x == 'h':
            message = 'Step ' + str(self.step) + '/' + self.noOfSteps +' Module ID:' + moduleToMoveID + ' leaving holding.'  
        else:
            message = 'Step ' + str(self.step) + '/' + self.noOfSteps + ' Module ID:' + moduleToMoveID + ' moving to ' + newLocation.getString()

        return True, message
    
    #REturn the raw structure for the voxel plots in the GUI.
    def getStructure(self): 
        return self.structure

#Save an array as a text file.
def saveArrayTxt(array, widthOfLattice=10, fileName='1'):

    array = np.reshape(array, (-1,widthOfLattice))

    try:
        filePath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        np.savetxt(filePath+'/Test Structures/'+fileName+'.txt',
            array,  fmt='%s', header='#ID, oldLocation(z,x,y), newLocation(z,x,y)#')
    except Exception as e:
        print(e)
        print('Save Failed - This is probably an issue with the .os dependency')
        print('Ending Program...')
        sys.exit()

#Load a previously saved text array. Used for the welcome structures. 
def loadTxtArray(widthOfLattice=10, fileName='1'):

    try:
        filePath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        array = np.loadtxt(filePath+'/Test Structures/'+fileName+'.txt')
    except Exception as e:
        print(e)
        print('Load failed')

    array = np.reshape(array, ([widthOfLattice, widthOfLattice, widthOfLattice]))

    return array

#Apply a movement to a structure.
def applyMovement(structure, movement):

    if movement[1].x != 'h':
    
        structure[movement[1].getTuple()] = 0

    if movement[2].x != 'h':

        structure[movement[2].getTuple()] = movement[0]


    return structure

#Load an array of movements stored in a text array.
def loadTxtMovements(fileName='1'):

    array = []

    try:
        filePath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        array = np.loadtxt(filePath+'/Movement Cache/'+fileName+'.txt')
    except Exception as e:
        print(e)
        print('Load failed error 123')

        return array

#Store an array of movements as a text array.
def storeMovements(movements, taskID):

    try:
        filePath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        np.savetxt(filePath+'/Movement Cache/'+taskID+'.txt',
            movements, fmt='%s', header='#ID, oldLocation(z,x,y), newLocation(z,x,y)#')
    except:
        print('Save Failed - This is probably an issue with the .os dependency')
        print('Ending Program...')
        sys.exit()

#Changes all the ID's in an array to 1, leaving only zeros and ones in the array.
#Used for the color schemes of voxel plots.
def getSingleArray(array, moduleID, widthOfLattice=10):

    singleArray = np.zeros((10,10,10))

    singleArray[np.where(array==moduleID)] = 1

    return singleArray

#Used to ensure uniform colour schemes are applied throughtout the program.
colours = { 1: 'blue',
            2: 'green',
            3: 'red',
            4: 'cyan',
            5: 'magenta',
            6: 'yellow'}

#Used to get a colour, ensuring they are the same throughout the program.
def getColourOfModule(moduleID):
    return colours[moduleID]
