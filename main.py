
import time
import math
import pygame
import threading
import Chip8
from threading import Thread

FILENAME = "invaders.c8"

lock = threading.Lock()

myChip = Chip8.Chip8(lock)
myChip.loadMemory(FILENAME)
print 'loading program...'
    
done = False

count = 0
pygame.init()


#Threaded class that uses pygame to get key presses, and writes those
#keypresses to the Chip8 keypad array
class getKeyInput(Thread):
    def __init__(self, lock):
        Thread.__init__(self)
        self.lock = lock
        
    def run(self):
        global done
        global myChip
        while not done:
            myChip.keypad = [0x00] * 16
            pressed = pygame.key.get_pressed()
                
            if pressed[pygame.K_1]:
                myChip.keypad[0x01] = 1
            if pressed[pygame.K_2]:
                myChip.keypad[0x02] = 1
            if pressed[pygame.K_3]:
                myChip.keypad[0x03] = 1
            if pressed[pygame.K_4]:
                myChip.keypad[0x0C] = 1
                
            if pressed[pygame.K_q]:
                myChip.keypad[0x04] = 1
            if pressed[pygame.K_w]:
                myChip.keypad[0x05] = 1
            if pressed[pygame.K_e]:
                myChip.keypad[0x06] = 1
            if pressed[pygame.K_r]:
                myChip.keypad[0x0D] = 1
                
            if pressed[pygame.K_a]:
                myChip.keypad[0x07] = 1
            if pressed[pygame.K_s]:
                myChip.keypad[0x08] = 1
            if pressed[pygame.K_d]:
                myChip.keypad[0x09] = 1  
            if pressed[pygame.K_f]:
                myChip.keypad[0x0E] = 1  
                
            if pressed[pygame.K_z]:
                myChip.keypad[0x0A] = 1
            if pressed[pygame.K_x]:
                myChip.keypad[0x00] = 1
            if pressed[pygame.K_c]:
                myChip.keypad[0x0B] = 1
            if pressed[pygame.K_v]:
                myChip.keypad[0x0F] = 1
            
                
            time.sleep(.025)
        

#Threaded class that uses pygame to draw pixels onto a canvas
#"pixels" are actually scaled up into squares in order to fill the
#display, which is itself scaled up by a factor of 100
class drawScreen(Thread):
    def __init__(self, lock):
        Thread.__init__(self)
        self.lock = lock
        
    def run(self):
        global done
        global myChip
        
        global count
        color = {}
        black = (0, 0, 0)
        white = (255, 255, 255)  
        
        
        clock = pygame.time.Clock()
        screen = pygame.display.set_mode((650, 330))
        screen.fill((0, 0, 0))
        
        while not done:
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                    
            
            self.lock.acquire()
            if myChip.Redraw == True:
                for ii in range(len(myChip.display)):
                    if myChip.display[ii] == 0:
                        color = black
                    else:
                        color = white
                    
                    xx = ii % 64
                    yy = math.floor(ii/64)
                    pygame.draw.rect(screen, color, pygame.Rect(xx * 10 , yy * 10, 10, 10))
                myChip.Redraw = False
                count += 1
                
            pygame.display.flip()
            
            self.lock.release()
            clock.tick(60)
        
  

#Main function
if __name__ == '__main__':
    print 'start thread'
    dS = drawScreen(lock)
    dS.start()
    
    keys = getKeyInput(lock)
    keys.start()

    while (myChip.pc != len(myChip.memory) - 2) & (done != True)  :
        myChip.clockCycle()
        if myChip.delay > 0:
            myChip.delay -= 1
        if myChip.sound > 0:
            myChip.sound -= 1
