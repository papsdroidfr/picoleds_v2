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
        self.leds.animation = ''
        #callback function called with push button
        self.button.irq(self.callback, Pin.IRQ_FALLING)
        self.ledStatus.value(1)
        self.loop()  #inifinite loop of events     
    
    def callback(self, pin):
        ''' callback function called when buton is pushed '''
        time.sleep(0.05) # wait 50ms : stabilization to avoid rebounds.
        if not(self.button.value()): # buton still pressed after the stabilization period ?
            self.ledStatus.value(0)
            machine.reset()
    
    def anim_cool_clignotante(self, nb_repet=1):
        for i in range(nb_repet):
            #anim wheel fade in
            self.leds.fade_wheel()
            self.leds.pixels_off()
            self.leds.shuffle_wheel()
            self.leds.pixels_off()
 
            #anim random fade out, sans rouge
            self.leds.fade_in(n_steps=10, color=(0,127,127) )
            self.leds.fade_out(n_steps=10, color=(0,127,127) )
            self.leds.shuffle_random(red=False)  
            
            #anim random fade out, sans vert
            self.leds.fade_in(n_steps=10, color=(127,0,127) )
            self.leds.fade_out(n_steps=10, color=(127,0,127) )
            self.leds.shuffle_random(green=False)
            
            #anim random fade out, sans bleu
            self.leds.fade_in(n_steps=10, color=(127,127,0) )
            self.leds.fade_out(n_steps=10, color=(127,127,0) )
            self.leds.shuffle_random(blue=False)
            self.leds.pixels_off()
            
    def anim_cool_arc_en_ciel(self, nb_repet=1):
        self.leds.animation='rainbow_cycle'
        for i in range(nb_repet):
            self.leds.rainbow_cycle()
    
    def anim_cool_random(self, nb_repet=1):
        for i in range(nb_repet):
            for j in range(20):
                self.leds.random()             #couleurs aléatoires pastel
            for j in range(20):
                self.leds.random(red=False)    #couleur aléatoires pastel sans rouge
            for j in range(20):
                self.leds.random(green=False)  #couleurs aléatoires pastel sans vert
            for j in range(20):
                self.leds.random(blue=False)   #couleurs aléatoires pastel sans bleu
    
    def anim_cool_mono_wheel(self, nb_repet=1):
        self.leds.animation='mono_wheel'
        for i in range(nb_repet):
            self.leds.mono_wheel(delay=0.02)
    
    def loop(self):
        while(True):
            self.anim_cool_clignotante(nb_repet=1)
            self.anim_cool_arc_en_ciel(nb_repet=1)
            self.anim_cool_random(nb_repet=1)
            self.anim_cool_mono_wheel(nb_repet=1)  

appl=Application()


