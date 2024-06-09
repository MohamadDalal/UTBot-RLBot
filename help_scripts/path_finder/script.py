import pygame
from vec import Vec3
from math import sin, cos, atan2, sqrt, pi

class LineVector():

    def __init__(self, locationVec: Vec3, rotationVec: Vec3):
        self.location = locationVec
        self.rotation = rotationVec.normalized()
        self.moving = False
        self.rotating = False

class GameClass():

    def __init__(self, FPS=60, screenSize=(2160, 1280)):
        self.FPS = FPS
        self.ScreenSize = screenSize
        self.player = LineVector(Vec3(1000,400,0), Vec3(0,-1,0).normalized())
        self.desired = LineVector(Vec3(800,600,0), Vec3(0,1,0))


    # Function that uninitializes the pygame module
    def close(self):
        self.runBool = False
        pygame.display.quit()
        pygame.quit()
        exit()

    def calcRadius(self, vec1: LineVector, vec2: LineVector, epsilon=10**-6):
        current_location = vec1.location
        current_orientation = vec1.rotation
        desired_location = vec2.location
        desired_orientation = vec2.rotation
        # Calculate the radius of the circle we need to turn in
        # Needs to consider when we cannot possible turn for the ball with the desired oriantation
        radius_direction = current_orientation.cross(Vec3(0,0,-1)).normalized()
        d = (desired_orientation.dot(radius_direction))*desired_orientation - radius_direction
        if abs(d.dot(d)-1) < epsilon:
            # Return half the distance from current_location to desired line
            #print("Parallel")
            #dist = (current_location - desired_location).length()**2 - current_location.dot(desired_orientation)**2
            dist = 0.5*(desired_location - current_location - desired_orientation.dot(desired_location - current_location)*desired_orientation).length()
            return - dist, dist
        c = desired_location - current_location + (desired_orientation.dot(current_location) - desired_orientation.dot(desired_location))*desired_orientation
        det = c.dot(d)**2-(d.dot(d)-1)*c.dot(c)
        #print(c, d)
        if det < 0:
            print(det)
            return 0, 0
        radius_plus = (-c.dot(d)+sqrt(det))/(d.dot(d)-1)
        radius_minus = (-c.dot(d)-sqrt(det))/(d.dot(d)-1)
        #return radius_plus if abs(radius_plus) < abs(radius_minus) else radius_minus
        return radius_plus, radius_minus
    
    def calcRadius2(self, vec1: LineVector, vec2: LineVector):
        current_location = vec1.location
        current_orientation = vec1.rotation
        desired_location = vec2.location
        desired_orientation = vec2.rotation
        # Calculate the radius of the circle we need to turn in
        # Needs to consider when we cannot possible turn for the ball with the desired oriantation
        radius_direction = current_orientation.cross(Vec3(0,0,-1)).normalized()
        displacement = current_location - desired_location
        a = radius_direction.dot(radius_direction) - radius_direction.dot(desired_orientation)**2
        b = radius_direction.dot(displacement)-2*current_location.dot(desired_orientation)*radius_direction.dot(desired_orientation)-1
        c = displacement.dot(displacement)-current_location.dot(desired_orientation)**2
        det = b**2 - 4*a*c
        #print(a)
        if det < 0:
            print(det)
            return 0, 0
        radius_plus = (-b+sqrt(det))/(a)
        radius_minus = (-b-sqrt(det))/(a)
        #return radius_plus if abs(radius_plus) < abs(radius_minus) else radius_minus
        return radius_plus, radius_minus

    def drawCirclePath(self, vec1: LineVector, vec2: LineVector):
        radius_plus, radius_minus = self.calcRadius(vec1, vec2)
        #print(radius_plus, radius_minus)
        rect_plus = pygame.Rect(0, 0, 2*abs(radius_plus), 2*abs(radius_plus))
        rect_minus = pygame.Rect(0, 0, 2*abs(radius_minus), 2*abs(radius_minus))
        center_plus = (vec1.location + vec1.rotation.cross(Vec3(0,0,-1)).normalized() * radius_plus).as_tuple_2d()
        center_minus = (vec1.location + vec1.rotation.cross(Vec3(0,0,-1)).normalized() * radius_minus).as_tuple_2d()
        rect_plus.center = center_plus
        rect_minus.center = center_minus
        vec1_angle = atan2(vec1.rotation.x, vec1.rotation.y)
        vec2_angle = atan2(vec2.rotation.x, vec2.rotation.y)
        pygame.draw.line(self.screen, (0,255,0), self.player.location.as_tuple_2d(), center_plus, 2)
        pygame.draw.line(self.screen, (255,0,0), self.player.location.as_tuple_2d(), center_minus, 2)
        pygame.draw.arc(self.screen, (0,255,0), rect_plus, vec1_angle, vec2_angle)
        pygame.draw.arc(self.screen, (255,0,0), rect_minus, vec2_angle, vec1_angle)
        

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
            #radius_plus, radius_minus = self.calcRadius(self.player, self.desired)
            #print(radius_plus, radius_minus)
            self.drawCirclePath(self.player, self.desired)
            # Iterate through all events the happened since last frame. Do stuff for the ones you want
            for e in eventList:
                # If the X button to close the window is pressed then close the game
                if e.type == pygame.QUIT:
                    self.close(self.runBool)
                # If the escape key is pressed then close the game
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.close()
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
                if a[1].collidepoint(mouse_pos):
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
                    
                elif a[0].moving:
                    if mouse_up_happened:
                        a[0].moving = False
                        a[0].rotating = False
                    else:
                        a[0].location = Vec3(mouse_pos[0], mouse_pos[1], 0)
                        cursor_current = cursor_hand
                elif a[0].rotating:
                    if mouse_up_happened:
                        a[0].moving = False
                        a[0].rotating = False
                    else:
                        a[0].rotation = (Vec3(mouse_pos[0], mouse_pos[1], 0) - a[0].location).normalized()
                        cursor_current = cursor_hand
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
    gameObj = GameClass(FPS=60)
    gameObj.playGame()