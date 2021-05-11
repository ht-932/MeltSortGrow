#Hide the welcome message from pygame.
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

#Import dependencies.
import pygame as pg
import math
import numpy as np
import ModularRoboticsToolkit as mrt

#Used to create an instance of the screen.
def createScreen(screen, font):

    #Set the window colour and update the display.
    screen.fill((dark))
    pg.display.update()
    pg.display.flip()

    #By taking advantage of the symmetry, draw the grid in which
    #the structure can be drawn.
    counter = 0
    while counter <= 1000:
        pg.draw.line(screen, blue, (0, counter), (1000, counter), 2)
        counter+=100
        
    counter = 0
    while counter <= 1000:
        pg.draw.line(screen, blue, (counter, 0), (counter, 1000), 2)
        counter+=100

    #Draw the rest of the borders of the grid.
    pg.draw.line(screen, blue, (0, 998), (1000, 998), 2)
    pg.draw.line(screen, lightGrey, (1052, 0), (1052, 1000), 100)

    #Draw the navigational arrows.
    down = font.render(str('↑'), False, white)
    up = font.render(str('↓'), False, white)
    screen.blit(down, (1025, 110))
    screen.blit(up, (1025, 210))

    #Draw the quit button.
    quit = font.render(str('Q'), False, white)
    screen.blit(quit, (1025, 310))

    #Draw the module ID selection buttons.
    voxelTypeOne = font.render(str('1'), False, white)
    screen.blit(voxelTypeOne, (1025, 410))
    voxelTypeTwo = font.render(str('2'), False, white)
    screen.blit(voxelTypeTwo, (1025, 510))
    voxelTypeThree = font.render(str('3'), False, white)
    screen.blit(voxelTypeThree, (1025, 610))
    voxelTypeFour = font.render(str('4'), False, white)
    screen.blit(voxelTypeFour, (1025, 710))
    voxelTypeFive = font.render(str('5'), False, white)
    screen.blit(voxelTypeFive, (1025, 810))
    voxelTypeSix = font.render(str('6'), False, white)
    screen.blit(voxelTypeSix, (1025, 910))

    #Update the screen and return it to the main program.
    pg.display.update()
    pg.display.flip()
    return screen

#Draw the newly selected level.
def drawLevel(array, levelCounter, screen):

    counter = 0
    rowCounter = 0

    #Get the array splice that for the desired level.
    arraySplice = array[levelCounter]

    #Draw the splice.
    for row in arraySplice:
        for voxel in row:

            if voxel != 0:
                pg.draw.rect(screen, mrt.getColourOfModule(voxel), [counter*100+2, rowCounter*100+2, 98, 98])
            counter += 1

        counter = 0
        rowCounter += 1

    #Update the display.
    pg.display.update()
    pg.display.flip()

#Contains the main loop which runs while a structure is being edited. 
def makerLoop(screen, levelCounter, array, font):

    #Set an initial module type to put down when the user clicks.
    moduleType = 1

    #MAIN LOOP
    run = True
    while run == True:

        #Update to show changes 
        pg.display.update()
        pg.display.flip()

        #Draw the menu bar on the right of the screen.
        #This is done in the main loop so that previous level indicators are drawn over.
        pg.draw.rect(screen, lightGrey, [1004, 2, 96, 96])

        #Draw the level ID indicator.
        levelID = font.render(str(levelCounter), False, white)
        screen.blit(levelID, (1020, 2))

        #Checks the event stack for mouse clicks.
        for event in pg.event.get():

            #If click is detected.
            if event.type == pg.MOUSEBUTTONUP:
                pos = pg.mouse.get_pos()

                #Get the location of the click.
                y = math.floor(pos[1]/100)
                x = math.floor(pos[0]/100)

                #If the click is in the structure display area. 
                if x < 10:
                    voxelState = array[int(levelCounter), y, x]

                    #If drawing a module, get the colour, draw the module and edit the array.
                    if voxelState == 0:
                        array[int(levelCounter), y, x] = moduleType
                        x=x*100
                        y=y*100
                        pg.draw.rect(screen, mrt.getColourOfModule(moduleType), [x+2, y+2, 98, 98])

                    #If a module exists there already, get rid of it.
                    elif voxelState != 0:
                        array[int(levelCounter), y, x] = 0
                        x=x*100
                        y=y*100
                        pg.draw.rect(screen, dark, [x+2, y+2, 98, 98])

                    break

                #If the click is in the menu bar respond accordingly.
                elif x == 10:

                    #If user clicks increase level counter.
                    if y == 1:

                        #Overshoot protection.
                        if levelCounter < 9:

                            #Increase level by one.
                            levelCounter += 1
                            createScreen(screen, font)
                            drawLevel(array, levelCounter, screen)

                    #If user clicks decrease level counter.     
                    elif y == 2:

                        #Undershoot protection.
                        if levelCounter > 0:

                            #Decrease Level counter by one.
                            levelCounter -= 1
                            createScreen(screen, font)
                            drawLevel(array, levelCounter, screen)

                    #If user wants to quit.
                    elif y == 3:
                        array = np.transpose(array, (1, 2, 0))
                        run = False

                    #If user selects a module type, choose that module.
                    elif y > 3:
                        moduleType = y-3

            #Detect if user clicks the cross on the window.
            elif event.type == pg.QUIT:
                run = False

    #print(array[0])
    pg.quit()
    return array

#Run to start the program.
def main():

    #Set some colours up.
    #Globally within this program.
    global dark
    dark = (37,  37,  38)
    global blue
    blue = (14, 99, 156)
    global green
    green = (94, 149, 85)
    global lightGrey
    lightGrey = (61, 61, 61)
    global white
    white = (225,225,225)

    #Start pygame and the font engine.
    pg.init()
    pg.font.init()
    
    #Set the screen size + title.
    #The array editing screen size is 1000x1000 to make representing a 10x10 array easier.
    screen = pg.display.set_mode((1100, 1000))
    pg.display.set_caption('Structure Maker - ')

    #Set the font, level counter and array to store the structure up.
    font = pg.font.SysFont("monospace", 90)
    levelCounter = 0
    array = np.zeros((10,10,10))

    #Create the screen, 
    screen = createScreen(screen, font)
    array = makerLoop(screen, levelCounter, array, font)

    #Return the array to the GUI
    return array
