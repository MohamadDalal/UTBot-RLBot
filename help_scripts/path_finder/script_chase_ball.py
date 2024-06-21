import pygame
import numpy as np
from vec import Vec3
from orientation import Orientation, relative_location
from math import sin, cos, atan2, sqrt, pi
from threading import Thread
from time import sleep

class LineVector():

    def __init__(self, locationVec: Vec3, rotationVec: Vec3):
        self.location = locationVec
        self.rotation = rotationVec.normalized()
        self.moving = False
        self.rotating = False

class Rotation():
    def __init__(self, yaw, pitch, roll):
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

class GameClass():

    def __init__(self, FPS=60, screenSize=(2160, 1280)):
        self.FPS = FPS
        self.ScreenSize = screenSize
        self.player = LineVector(Vec3(1000,400,0), Vec3(0,-1,0).normalized())
        self.desired = LineVector(Vec3(800,600,0), Vec3(0,1,0))
        self.editLock = False
        self.threads = []



    # Function that uninitializes the pygame module
    def close(self):
        self.runBool = False
        pygame.display.quit()
        pygame.quit()
        exit()

    # v is the magnitude of the velocity in the car's forward direction
    def curvature(self, v):
        if 0.0 <= v < 500.0:
            return 0.006900 - 5.84e-6 * v
        if 500.0 <= v < 1000.0:
            return 0.005610 - 3.26e-6 * v
        if 1000.0 <= v < 1500.0:
            return 0.004300 - 1.95e-6 * v
        if 1500.0 <= v < 1750.0:
            return 0.003025 - 1.1e-6 * v
        if 1750.0 <= v < 2500.0:
            return 0.001800 - 4e-7 * v

        return 0.0

    def calc_turning_time(self, speed, desiredSpeed=850, epsilon=0.01, deltaT=1/120):
        """
        Calculate the time it takes to turn the car to a certain orientation
        """


        brakeSpeed=350
        self.editLock = True
        s = speed
        a = self.player.rotation.normalized().as_numpy()
        b = self.desired.location.as_numpy()
        c = self.player.location.as_numpy()
        time_to_desired_speed = (s - desiredSpeed) / brakeSpeed
        time_taken = time_to_desired_speed
        # TODO: Decide if we are to turn left or right
        turn_dir = np.sign(np.cross(a, b - c)[2]) # -1 if left, 1 if right
        print(turn_dir)

        # Calculate the angle between the car orientation and the target orientation
        angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(b - c)))
        #print("Start angle: ", angle)
        for i in range(int(time_to_desired_speed//deltaT)):
            if np.abs(angle) < epsilon:
                print("Breaking at angle: ", angle)
                break
            else:
                s -= brakeSpeed*deltaT
                vel_ang = speed * self.curvature(s)
                a = np.array([[np.cos(turn_dir*vel_ang*deltaT), -np.sin(turn_dir*vel_ang*deltaT), 0],
                        [np.sin(turn_dir*vel_ang*deltaT), np.cos(turn_dir*vel_ang*deltaT), 0],
                        [0, 0, 1]])@a
                vel = s*a
                c = c+vel*deltaT
                # Calculate the angle between the car orientation and the target orientation
                angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(b - c)))
                print(angle)

                # Pygame specific stuff
                self.player.location = Vec3(c[0], c[1], c[2])
                self.player.rotation = Vec3(a[0], a[1], a[2])
                if self.runBool == False:
                    return
                sleep(deltaT)

        #print("Middle angle: ", angle)
        while np.abs(angle) > epsilon:
            time_to_turn = angle / vel_ang
            c = c+np.sqrt(2*(1/self.curvature(s))**2*(1-np.cos(turn_dir*angle)))*np.array([[np.cos(turn_dir*angle/2), -np.sin(turn_dir*angle/2), 0],
                                                                                           [np.sin(turn_dir*angle/2), np.cos(turn_dir*angle/2), 0],
                                                                                           [0, 0, 1]])@a
            a = np.array([[np.cos(turn_dir*angle), -np.sin(turn_dir*angle), 0],
                          [np.sin(turn_dir*angle), np.cos(turn_dir*angle), 0],
                          [0, 0, 1]])@a
            vel = s*a
            # Calculate the angle between the car orientation and the target orientation
            angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(b - c)))
            time_taken += time_to_turn

            # Pygame specific stuff
            self.player.location = Vec3(c[0], c[1], c[2])
            self.player.rotation = Vec3(a[0], a[1], a[2])
            if self.runBool == False:
                return
            sleep(time_to_turn)
        #print("End angle: ", angle)
        self.editLock = False
        #return time_taken

    def drawArrow(self, start: Vec3, end: Vec3):
        lineRect = pygame.draw.line(self.screen, (255,255,255), start.as_tuple_2d(), end.as_tuple_2d(), 2)
        # Get the vector from start to end
        vec = end - start
        vec = vec.flat()
        # Get the angle of the vector
        angle = atan2(vec.x, vec.y)
        # Draw the first half of the arrow
        arrowRect1 = pygame.draw.line(self.screen, (255,255,255), end.as_tuple_2d(), (end + Vec3(sin(angle + 3.93), cos(angle + 3.93), 0) * 10).as_tuple_2d(), 2)
        # Draw the second half of the arrow
        arrowRect2 = pygame.draw.line(self.screen, (255,255,255), end.as_tuple_2d(), (end + Vec3(sin(angle - 3.93), cos(angle - 3.93), 0) * 10).as_tuple_2d(), 2)
        return lineRect.unionall([arrowRect1, arrowRect2])

    # Function that setups the game, draws the game window, checks for movement and updates all variables.
    def playGame(self):
        # Initialize pygame
        pygame.init()
        # A boolean that makes the while loop keep running. Loops stops if this goes false
        self.runBool = True
        # Pygame stuff. Read a pygame tutorial or the documentations for help
        self.screen = pygame.display.set_mode(self.ScreenSize)
        self.clock =  pygame.time.Clock()
        # Make the entire screen black (To remove anything already drawn there)
        self.screen.fill((0,0,0))
        # Create pygame rectangles for the FPS counter and the player circle (They specify where they are located in the windwo)
        fpsRect = pygame.Rect(0,0,20,20)
        # Create mouse cursors
        cursor_arrow = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)
        cursor_hand = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND)
        cursor_current = cursor_arrow
        mouse_down_happened = False
        mouse_up_happened = False
        arrow_transform = 0
        
        
        
        # Loop through the level screen until the runBool is set to false or the player beats the level
        while self.runBool:
            # Set FPS of the game and get events (for example button presses or keyboard presses. More info in pygame documentation)
            self.clock.tick(self.FPS)
            eventList = pygame.event.get()
            self.screen.fill((0,0,0))
            # Paint the FPS counter area black so we can draw a new FPS value. Otherwise they will be drawn on top of each other
            self.screen.fill((0,0,0), fpsRect)
            # Draw arrows
            arrows = []
            arrows.append((self.player, self.drawArrow(self.player.location, self.player.location + self.player.rotation * 20)))
            arrows.append((self.desired, self.drawArrow(self.desired.location, self.desired.location + self.desired.rotation * 20)))
            # Iterate through all events the happened since last frame. Do stuff for the ones you want
            for e in eventList:
                # If the X button to close the window is pressed then close the game
                if e.type == pygame.QUIT:
                    self.close(self.runBool)
                # If the escape key is pressed then close the game
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.close()
                    if e.key == pygame.K_SPACE and not self.editLock:
                        Thread(target=self.calc_turning_time, args=(230,), kwargs={"desiredSpeed":85}).start()
                    arrow_transform = 0 if e.key == pygame.K_t else arrow_transform
                    arrow_transform = 1 if e.key == pygame.K_r else arrow_transform

                if e.type == pygame.MOUSEBUTTONDOWN:
                    #print(e.button)
                    if e.button == 1:
                        mouse_down_happened = True
                    else:
                        mouse_down_happened = False
                else:
                    mouse_down_happened = False
                if e.type == pygame.MOUSEBUTTONUP:
                    #print(e.button)
                    if e.button == 1:
                        mouse_up_happened = True
                    else:
                        mouse_up_happened = False
                else:
                    mouse_up_happened = False
                
            
            mouse_pos = pygame.mouse.get_pos()
            for a in arrows:
                if self.editLock:
                        a[0].moving = False
                        a[0].rotating = False
                        cursor_current = cursor_arrow
                        continue
                elif a[1].collidepoint(mouse_pos):
                    #print("Collided")
                    cursor_current = cursor_hand
                    if mouse_down_happened:
                        if arrow_transform == 0:
                            a[0].moving = True
                        elif arrow_transform == 1:
                            a[0].rotating = True
                    elif mouse_up_happened:
                        a[0].moving = False
                        a[0].rotating = False
                    if a[0].moving:
                        a[0].location = Vec3(mouse_pos[0], mouse_pos[1], 0)
                    break
                    
                elif a[0].moving:
                    if mouse_up_happened:
                        a[0].moving = False
                        a[0].rotating = False
                    else:
                        a[0].location = Vec3(mouse_pos[0], mouse_pos[1], 0)
                        cursor_current = cursor_hand
                    break
                elif a[0].rotating:
                    if mouse_up_happened:
                        a[0].moving = False
                        a[0].rotating = False
                    else:
                        a[0].rotation = (Vec3(mouse_pos[0], mouse_pos[1], 0) - a[0].location).normalized()
                        cursor_current = cursor_hand
                    break
                else:
                    cursor_current = cursor_arrow
                    continue

            pygame.mouse.set_cursor(cursor_current)
            # Get current game FPS to display on the window
            currentFPS = self.clock.get_fps()
            # Create the text to be displayed by specifying font, font size, text and color. Check documentation for more into
            FPS_Text = pygame.font.SysFont("Arial", 16).render("FPS: " + str(int(currentFPS)), False, (255,255,255))
            # Draw FPS counter and player
            fpsRect = self.screen.blit(FPS_Text, (0,0))
            pygame.display.flip()

if __name__=="__main__":
    gameObj = GameClass(FPS=60, screenSize=(1920, 1080))
    gameObj.playGame()