#RUNS ON PICO
from ledRGBws2812 import LedsRGBws2812
from machine import Pin
import time

class Application:
    
    def __init__(self):
        ''' initialize leds RGB and push Button'''
        self.ledStatus = Pin(25, Pin.OUT)     # led témoin du pico
        self.leds = LedsRGBws2812(pin_num=14, n_leds=80, brightness=0.2)  # ruban de leds 
        self.button = Pin(15, Pin.IN, Pin.PULL_DOWN) #bouton poussoir avec resistance de rappel activée
        self.leds.pixels_off()
        self.id_anim=0
        self.l_anims = ['mono_wheel', 'rainbow_cycle', 'random', 'fill', 'fill', 'off']
        self.leds.animation = self.l_anims[0]
        #callback function called with push button
        self.button.irq(self.callback, Pin.IRQ_FALLING)
        self.ledStatus.value(1)
        self.loop()  #inifinite loop of events     
    
    def callback(self, pin):
        ''' callback function called when buton is pushed '''
        time.sleep(0.05) # wait 50ms : stabilization to avoid rebounds.
        if not(self.button.value()): # buton still pressed after the stabilization period ?
            self.id_anim = (self.id_anim+1) % len(self.l_anims)
            self.leds.animation = self.l_anims[self.id_anim] #name animation change
            self.ledStatus.value(1)
            print('button pressed', pin.irq().flags())
            print('animation: ', self.leds.animation)
            #transition to play
            if self.id_anim==0:
                pass
            elif self.id_anim==1:
                pass
            elif self.id_anim==2:
                pass
            elif self.id_anim==3:
                self.leds.fade_in(10, self.leds.BLUE, 0.05)
            elif self.id_anim==4:
                self.leds.fade_out(10, self.leds.BLUE, 0.05)
                self.leds.fade_in(10, self.leds.PURPLE, 0.05)
            else:
                self.leds.fade_out(10, self.leds.PURPLE, 0.05)
                self.ledStatus.value(0)         
    
    def loop(self):
        while(True):
            if self.id_anim==0:
                self.leds.mono_wheel(delay=0.5)
            elif self.id_anim==1:
                self.leds.rainbow_cycle()
            elif self.id_anim==2:
                self.leds.random(green=False)
            elif self.id_anim==3:
                self.leds.pixels_fill(self.leds.BLUE)
                time.sleep(0.5)
            elif self.id_anim==4:
                self.leds.pixels_fill(self.leds.PURPLE)
                time.sleep(0.5)
            else:
                self.leds.pixels_fill(self.leds.BLACK)
                time.sleep(0.5)

appl=Application()

