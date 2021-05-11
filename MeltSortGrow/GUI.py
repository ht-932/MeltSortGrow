#Import dependencies. 
from functools import total_ordering
import tkinter as tk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
from numpy.core.numeric import moveaxis, tensordot
import ModularRoboticsToolkit as mrt
import StructMaker as sm
import MeltSortGrow as msg
import numpy as np

#Tk setup + window name.
root = tk.Tk()
root.wm_title('Modular System ReConfig Planner')

#A display holds a single mpl plot and one of the 3 arrays used to store structures.
class Display():

    #Initialise, column is one of three coloms used to locate the plot. 
    def __init__(self, column):

        #Display chaged is used to check if the user has input new structures for the algorithms.
        self.stepCounter = 0
        self.displayChanged = False
        self.movements = []

        #Setup voxel plot.
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().grid(row = 1, column=column)

        #Setup toolbar.
        self.toolbarFrame = tk.Frame(master=root)
        self.toolbarFrame.grid(row=2, column=column)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbarFrame)

        #Add the structure to the voxel plot.
        self.ax = self.fig.add_subplot(111, projection='3d')

    #Get/Set for display changed. Used to stop algorithms running before structures are created.
    def isDisplayChanged(self):
        return self.displayChanged
    def setDisplayChanged(self, displayChanged):
        self.displayChanged = displayChanged

    #Draw a new structure. 
    def overwriteStructure(self, structure):

        #Store the new structure and clear the mpl window.
        self.structure = structure
        self.ax.clear()

        #Draw voxel by voxel, checking the colours of each voxel. 
        for voxel in np.nditer(self.structure):
            if voxel != 0:
                colourForAssignment = mrt.getColourOfModule(int(voxel))
                array = mrt.getSingleArray(structure, voxel)
                self.ax.voxels(array, edgecolors='k', color=colourForAssignment)

        #Draw changes to the screen and set the changed indicator.
        self.fig.canvas.draw()
        self.displayChanged = True

    #Getters and setters for structure and stepable structure (which contains th movements and the current structure state).
    def getStructureAsArray(self):
        return self.structure
    def setSteppableStructure(self, steppableStructure):
        self.steppableStructure = steppableStructure
    def getSteppableStructure(self):
        return self.steppableStructure

#Setup the output box in the lower left corner of the screen.
class OutputFrame():

    def __init__(self):
        
        #Setup Tk.
        outputFrame = tk.Frame(master=root)

        self.outputBox = tk.Text(master=outputFrame, height=1, width=45)
        self.outputBox.pack(side=tk.LEFT)

        outputBoxScroller = tk.Scrollbar(master=outputFrame)
        outputBoxScroller.pack(side=tk.RIGHT, fill='y')

        outputBoxScroller.config(command=self.outputBox.yview)
        self.outputBox.config(yscrollcommand=outputBoxScroller.set)

        #Set the welcome text.
        text = 'Harry Thomas - Uni of York - 2021\n'
        self.outputBox.insert(tk.END, text)

        #Set the location of the output box.
        outputFrame.grid(row=3, column=2)

    #Setter for the message in the box, \n is because previous messages are scrollable.
    def displayMessage(self, messageToDisplay):

        text = ('\n'+messageToDisplay)
        self.outputBox.insert(tk.END, text)
        self.outputBox.see('end')

#Create the controls and all of the button listeners. 
def controlsInit(initialStructureDisplay, goalStructureDisplay, interimStructureDisplay, outputBox):

    controlFrameCentral = tk.Frame(master=root)

    createInitButton = tk.Button(master=controlFrameCentral, text="Create Initial Structure", 
            command=lambda: createInitStructButtonPress(initialStructureDisplay, outputBox))
    createInitButton.grid(row=0, column=2)

    createGoalButton = tk.Button(master=controlFrameCentral, text="Create Goal Structure", 
            command=lambda: createGoalStructButtonPress(goalStructureDisplay, outputBox))
    createGoalButton.grid(row=0, column=3)

    previousButton = tk.Button(master=controlFrameCentral, text="<", 
            command=lambda: previousButtonPress(interimStructureDisplay, outputBox))
    previousButton.grid(row=0, column=1)

    nextButton = tk.Button(master=controlFrameCentral, text=">", 
            command=lambda: nextButtonPress(interimStructureDisplay, outputBox))
    nextButton.grid(row=0, column=4)

    previousTwoButton = tk.Button(master=controlFrameCentral, text="<<", 
            command=lambda: previousTwoButtonPress(interimStructureDisplay, outputBox))
    previousTwoButton.grid(row=0, column=0)

    nextTwoButton = tk.Button(master=controlFrameCentral, text=">>", 
            command=lambda: nextTwoButtonPress(interimStructureDisplay, outputBox))
    nextTwoButton.grid(row=0, column=5)

    controlFrameCentral.grid(row=3, column=1)

    controlFrameLeft = tk.Frame(master=root)

    helpButton = tk.Button(master=controlFrameLeft, text='Help')
    helpButton.grid(column=2, row=0)

    MSGButton = tk.Button(master=controlFrameLeft, text='Melt Sort Grow', 
            command=lambda: MSGButtonPress(initialStructureDisplay, goalStructureDisplay, interimStructureDisplay, outputBox))
    MSGButton.grid(column=0, row=0)

    gFieldsButton = tk.Button(master=controlFrameLeft, text='Gradient Fields', 
            command=lambda: gFieldsButtonPress(interimStructureDisplay, outputBox))
    gFieldsButton.grid(column=1, row=0)

    controlFrameLeft.grid(row=3, column=0)

#Listener for MSG trigger.
def MSGButtonPress(initialStructureDisplay, goalStructureDisplay, interimStructureDisplay, outputBox):

    #Check the structures have been setup.
    if initialStructureDisplay.isDisplayChanged() == True and goalStructureDisplay.isDisplayChanged() == True:

        #Display running message.
        outputBox.displayMessage('Melting, Sorting and Growing...')

        #Display the initial structure in the middle box.
        interimStructureDisplay.overwriteStructure(initialStructureDisplay.getStructureAsArray())

        #Setter for the default lattice width.
        widthOfLattice = 10

        #Create a new structure, to protect the original within this program.
        initialStructureForManipulation = np.zeros((widthOfLattice, widthOfLattice, widthOfLattice))
        for voxel in np.nditer(initialStructureDisplay.getStructureAsArray()):
            if voxel != 0:
                initialStructureForManipulation[np.where(initialStructureDisplay.getStructureAsArray()==voxel)] = voxel

        #Send the new structure to be Melted, Sorted and Grown.
        meltSuccsessful, movements = msg.main(initialStructureForManipulation, goalStructureDisplay.getStructureAsArray())

        #Use the returned movements to create the steppable structure. 
        steppableStructure = mrt.StepStructure(initialStructureDisplay.getStructureAsArray(), movements)

        #Display the new structure.
        interimStructureDisplay.overwriteStructure(steppableStructure.getStructure())

        #Set the steppable structure in the diusplay object for easy, global access. 
        interimStructureDisplay.setSteppableStructure(steppableStructure)

        #Display suitable message.
        if meltSuccsessful == True:
            outputBox.displayMessage('Melt Sort Grow Complete!')
        else:
            outputBox.displayMessage('Melt Failed, attempting step recovery...')

    #If structure have not been created alert the user.
    else:
        outputBox.displayMessage('Error! Have you created init/goal structures?')

#Gradient fields button listener.
def gFieldsButtonPress(interimStructureDisplay, outputBox):
    outputBox.displayMessage('Coming Soon!')

#Trigger for the initial structure's maker.
def createInitStructButtonPress(initialStructureDisplay, outputBox):

    #Launch structure maker.
    initialStructure = sm.main()

    #Display new structure. 
    initialStructureDisplay.overwriteStructure(initialStructure)

    #Display message when control returns to this program.
    outputBox.displayMessage('Initial Structure Updated')

#Trigger for the initial structure's maker.
def createGoalStructButtonPress(goalStructureDisplay, outputBox):

    #Launch structure maker.
    goalStructure = sm.main()

    #Display new structure. 
    goalStructureDisplay.overwriteStructure(goalStructure)

    #Display message when control returns to this program.
    outputBox.displayMessage('Goal Structure Updated')

#Display the next step when the button is pressed.
def nextButtonPress(interimStructureDisplay, outputBox):

    #Try to get the steppable structure. If the user has not yet run a reconfiguration alert them.
    try:
        steppableStructure = interimStructureDisplay.getSteppableStructure()
    except: 
        outputBox.displayMessage('Error. Have you run an algorithm?')
        return

    #Try to move a step forward.
    stepComplete, message = steppableStructure.moveStep('forward')

    #Overshoot protection.
    if stepComplete == False: return

    #Display a suitable message and the new structure.
    interimStructureDisplay.overwriteStructure(steppableStructure.getStructure())
    outputBox.displayMessage(message)

#Display the previous step when the button is pressed.
def previousButtonPress(interimStructureDisplay, outputBox):

    #Try to get the steppable structure. If the user has not yet run a reconfiguration alert them.
    try:
        steppableStructure = interimStructureDisplay.getSteppableStructure()
    except:
        outputBox.displayMessage('Error. Have you run an algorithm?')
        return

    #Try to move a step backward.
    stepComplete, message = steppableStructure.moveStep('backward')

    #Overshoot protection.
    if stepComplete == False: return

        #Display a suitable message and the new structure.
    interimStructureDisplay.overwriteStructure(steppableStructure.getStructure())
    outputBox.displayMessage(message)

#If the double move back button is pressed, run the move back function three times. 
def previousTwoButtonPress(interimStructureDisplay, outputBox):

    previousButtonPress(interimStructureDisplay, outputBox)
    previousButtonPress(interimStructureDisplay, outputBox)
    previousButtonPress(interimStructureDisplay, outputBox)
    
#If the double move forward button is pressed, run the move forward function three times. 
def nextTwoButtonPress(interimStructureDisplay, outputBox):

    nextButtonPress(interimStructureDisplay, outputBox)
    nextButtonPress(interimStructureDisplay, outputBox)
    nextButtonPress(interimStructureDisplay, outputBox)

#Initialise the title bar.
def titleBarInit():

    initialStructTitle = tk.Label(master=root, text='Initial Structure')
    initialStructTitle.grid(row=0, column=0)

    interimStructureTitle = tk.Label(master=root, text='Interim Structure')
    interimStructureTitle.grid(row=0, column=1)

    goalStructureTitle = tk.Label(master=root, text='Goal Structure')
    goalStructureTitle.grid(row=0, column=2)

    return

#Main loop to start the GUI and the entire program. 
def main():
    
    #Setup the three voxel plots.
    initialStructureDisplay = Display(0)
    interimStructureDisplay = Display(1)
    goalStructureDisplay = Display(2)

    #Setup the output box.
    outputBox = OutputFrame()

    #Initialise buttons and title bar.
    controlsInit(initialStructureDisplay, goalStructureDisplay, interimStructureDisplay, outputBox)
    titleBarInit()

    #Start the Tk mainloop, to listen for button presses.
    tk.mainloop()

#GUI is the entry point to the program.
main()
