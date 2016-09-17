
import threading
from random import randrange

class Chip8(object):

    def __init__(self, lock):
        self.lock = lock
        self.redrawCount = 0
        self.Redraw = False
        self.Done = 0
        self.memory = [0x00] * 4096
        self.instruction = 0x0000
        self.pc = 0x200
        
        #V and I REGISTERS
        self.V = [0x00] * 16
        self.I = 0x0000
        
        #STACK AND STACK POINTER
        self.stack = [0x0000] * 16
        self.sp = 0x0000
        
        #IO
        self.keypad = [0x00] * 16
        self.display = [0x00] * (64 * 32)
        self.display_grid = [ [0 for w in range(32)] for h in range(64) ]
        
        #TIMERS
        self.delay = 0
        self.sound = 0
        
        #CHIP* FONT
        self.font = [0xF0, 0x90, 0x90, 0x90, 0xF0, \
                     0x20, 0x60, 0x20, 0x20, 0x70, \
                     0xF0, 0x10, 0xF0, 0x80, 0xF0, \
                     0xF0, 0x10, 0xF0, 0x10, 0xF0, \
                     0x90, 0x90, 0xF0, 0x10, 0x10, \
                     0xF0, 0x80, 0xF0, 0x10, 0xF0, \
                     0xF0, 0x80, 0xF0, 0x90, 0xF0, \
                     0xF0, 0x10, 0x20, 0x40, 0x40, \
                     0xF0, 0x90, 0xF0, 0x90, 0xF0, \
                     0xF0, 0x90, 0xF0, 0x10, 0xF0, \
                     0xF0, 0x90, 0xF0, 0x90, 0x90, \
                     0xE0, 0x90, 0xE0, 0x90, 0xE0, \
                     0xF0, 0x80, 0x80, 0x80, 0xF0, \
                     0xE0, 0x90, 0x90, 0x90, 0xE0, \
                     0xF0, 0x80, 0xF0, 0x80, 0xF0, \
                     0xF0, 0x80, 0xF0, 0x80, 0x80]
        
        #POPULATE MEMORY WITH FONT
        for i in range(80):
            self.memory[i + 0x50] = self.font[i]
            
        self.op_table = {0x0000: self.op0,
                         0x1000: self.op1,
                         0x2000: self.op2,
                         0x3000: self.op3,
                         0x4000: self.op4,
                         0x5000: self.op5,
                         0x6000: self.op6,
                         0x7000: self.op7,
                         0x8000: self.op8,
                         0x9000: self.op9,
                         0xA000: self.opA,
                         0xB000: self.opB,
                         0xC000: self.opC,
                         0xD000: self.opD,
                         0xE000: self.opE,
                         0xF000: self.opF
                         }
                           
            
    def loadMemory(self, romPath):
        rom = open(romPath, "rb").read()
        for i in range(len(rom)):
            self.memory[i + 0x200] = ord(rom[i])
         
            
    def clockCycle(self):
        self.instruction = (self.memory[self.pc] << 8) | (self.memory[self.pc + 1])
        self.decodeInstruction(self.instruction)
        self.pc += 2
        pass
    
    
    def decodeInstruction(self, instruction):
        opcode = instruction & 0xF000
        self.op_table[opcode](instruction)
        pass  
    
#***********************************************************************************
   
    def op0(self, instruction):
        ls_nibble = instruction & 0x00FF
        
        # 00E0 - CLEARS SCREEN
        if ls_nibble == 0x00E0:
            for i in range(len(self.display)  ):
                self.display[i] = 0
            
            while self.Redraw == True:
                pass   
        
            self.lock.acquire()     
            self.Redraw = True
            self.lock.release()
            return
        
        # 00EE - Returns from a subroutine
        elif ls_nibble == 0x00EE:
            self.sp -= 1
            self.pc = self.stack[self.sp]
            
        
    
    # 1NNN - Jumps to address NNN
    def op1(self, instruction):
        addr = instruction & 0x0FFF
        self.pc = addr - 2
    
    # 2NNN - Calls subroutine at NNN
    def op2(self, instruction):
        addr = 0x0FFF & instruction
        self.stack[self.sp] = self.pc
        self.sp += 1
        self.pc = addr - 2
    
    # 3XNN - Skips the next instruction if VX equals NN
    def op3(self, instruction):
        x = (instruction & 0x0F00) >> 8
        if self.V[x] == (instruction & 0x00FF):
            self.pc += 2
            
    # 4XNN - Skips the next instruction if VX doesn't equal NN        
    def op4(self, instruction):
        x = (instruction & 0x0F00) >> 8
        if self.V[x] != (instruction & 0x00FF):
            self.pc += 2

    # 5XY0 - Skips the next instruction if VX equals VY
    def op5(self, instruction):
        x = (instruction & 0x0F00) >> 8
        y = (instruction & 0x00F0) >> 4
        if self.V[x] == self.V[y]:
            self.pc += 2
    
    # 6XNN - Sets VX to NN 
    def op6(self, instruction):
        x = (instruction & 0x0F00) >> 8
        self.V[x] = instruction & 0x00FF

    
    # 7XNN - Adds NN to VX
    def op7(self, instruction):
        x = (instruction & 0x0F00) >> 8
        self.V[x] = (self.V[x] + (instruction & 0x00FF) ) & 0xFF


    def op8(self, instruction):
        x = (instruction & 0x0F00) >> 8
        y = (instruction & 0x00F0) >> 4
        
        ls = instruction & 0x000F
        
        # 8XY0 - Sets VX to the value of VY
        if ls == 0x0000:
            self.V[x] = self.V[y] & 0xFF
            return
        
        # 8XY1 - Sets VX to VX OR VY.
        elif ls == 0x0001:
            self.V[x] = (self.V[x] | self.V[y]) & 0xFF
            return
        
        # 8XY2 - Sets VX to VX AND VY
        elif ls == 0x0002:
            self.V[x] = (self.V[x] & self.V[y]) & 0xFF
            return
        
        # 8XY3 - Sets VX to VX xor VY
        elif ls == 0x0003:
            self.V[x] = (self.V[x] ^ self.V[y]) & 0xFF
            return
        
        # 8XY4 - Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there isn't
        elif ls == 0x0004:
            if self.V[x] > (0xFF - self.V[y]):
                self.V[0xF] = 1
            else:
                self.V[0xF] = 0
            
            self.V[x] += self.V[y] & 0xFF
            
            return
        
        # 8XY5 - VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there isn't
        elif ls == 0x0005:
            
            if self.V[x] > self.V[y]:
                self.V[0xF] = 1
            else:
                self.V[0xF] = 0
                
            self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            return
        
        # 8XY6 - Shifts VX right by one. VF is set to the value of LSB of VX before the shift
        elif ls == 0x0006:
            self.V[0xF] = self.V[x] & 0x01
            self.V[x] = (self.V[x] >> 1) & 0xFF
            return
        
        
        # 8XY7 - Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't
        elif ls == 0x0007:
            if self.V[y] > self.V[x]:
                self.V[0xF] = 1
            else:
                self.V[0xF] = 0
            self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            
            return
        
        # 8XYE - Shifts VX left by one. VF is set to the value of the MSB of VX before the shift
        elif ls == 0x000E:
            self.V[0xF] = self.V[x] & 0x80
            self.V[x] = (self.V[x] << 1) & 0xFF
            return
        
    # 9XY0 - Skips the next instruction if VX doesn't equal VY
    def op9(self, instruction):
        x = (instruction & 0x0F00) >> 8
        y = (instruction & 0x00F0) >> 4
        if self.V[x] != self.V[y]:
            self.pc += 2  
        return

    
    # ANNN - Sets I to the address NNN
    def opA(self, instruction):
        addr = instruction & 0x0FFF
        self.I = addr

    # BNNN - Jumps to the address NNN plus V0
    def opB(self, instruction):
        self.pc = ((instruction & 0x0FFF ) + self.V[0x00]) - 2
        return

    # CXNN - Sets VX to the result of a bitwise and operation on a random number and NN
    def opC(self, instruction):
        x = (instruction & 0x0F00) >> 8
        ls_nibble = instruction & 0x00FF
        self.V[x] = (ls_nibble & randrange(0x00, 0xFF)) & 0xFF

    
    # DXYN - Draws a sprite at coordinate (VX, VY) that has a width of 8 pixels and a height of N pixels
    def opD(self, instruction):
        x = self.V[ (instruction & 0x0F00) >> 8 ] & 0xFF
        y = self.V[ (instruction & 0x00F0) >> 4 ] & 0xFF
        
        height = instruction & 0x000F
        self.V[0xF] = 0
        for i in range(height):
            img_sweep = self.memory[self.I + i]
            for j in range(8):
                pixel = img_sweep & (0x80 >> j)
                if pixel != 0:
                                     
                    if self.display[x + j + (y + i) * 64] == 1:
                        self.V[0xF] = 1
                    self.display[x + j + (y + i) * 64] ^= 1

        
        while self.Redraw == True:
            pass   
        
        self.lock.acquire()     
        self.Redraw = True
        self.lock.release()        

    
    # EXA1 - Skips the next instruction if the key stored in VX isn't pressed    
    def opE(self, instruction):
        ls_nibble = instruction & 0x00FF
        x = (instruction & 0x0F00) >> 8
        if ls_nibble == 0x9E:
            if self.keypad[self.V[x]] == 1:
                self.pc += 2
            return
        elif ls_nibble == 0xA1:
            if self.keypad[self.V[x]] == 0:
                self.pc += 2
            return


    def opF(self, instruction):
        x = (instruction & 0x0F00) >> 8
        ls_nibble = instruction & 0x00FF
        
        # FX07 - Sets VX to the value of the delay timer
        if ls_nibble == 0x07:
            self.V[x] = self.delay
            return
        
        elif ls_nibble == 0x0A:
            print 'WAITING FOR KEYPAD INPUT!!!'
            self.Done = 1
            return
        
        # FX15 - Sets the delay timer to VX
        elif ls_nibble == 0x15:
            self.delay = self.V[x] & 0xFF
            return
        
        # FX18 - Sets the sound timer to VX
        elif ls_nibble == 0x18:
            self.sound = self.V[x] & 0xFF
            return
        
        # FX1E - Adds VX to I
        elif ls_nibble == 0x1E:
            self.I += self.V[x] & 0xFF
            return
        
        # FX29 - Sets I to the location of the sprite for the character in VX
        elif ls_nibble == 0x29:
            font_char =  self.V[x]
            self.I = 0x50 + font_char*5
            return
        
        # FX33 - Stores the binary-coded decimal representation of VX @ addr I, I+1, I+2
        elif ls_nibble == 0x33:
            val = self.V[x]
            a = (val/100) #HUNDREDS
            b = (val - 100*(val/100) ) / 10 #TENS
            c = val - (a*100 + b*10) #ONES
            
            self.memory[self.I] = a
            self.memory[self.I + 1] = b
            self.memory[self.I + 2] = c 
            return
        
        elif ls_nibble == 0x55:
            self.Done = 1
            return
        
        # FX65 - Fills V0 to VX (including VX) with values from memory starting at address I
        elif ls_nibble == 0x65:
            i = 0
            while i <= x:
                self.V[i] = self.memory[self.I + i] & 0xFF
                i += 1
            self.I = self.I + x + 1
            return

    
        