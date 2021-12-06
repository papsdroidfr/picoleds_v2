# runs on PICO

import array, time, rp2
from machine import Pin
from random import randrange, randint

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

class LedsRGBws2812:
    ''' Neopixel RGB WS2812 Class
        instance: leds = LedsRGBws2812() or LedsRGBws2812(n_leds, pin_num, brightness)
    '''

    def __init__(self, n_leds=16, pin_num=0, brightness=0.2):
        ''' constructor: Configure the WS2812 LEDs. '''
        
        print('init leds RGB')
        self.NUM_LEDS = n_leds
        self.PIN_NUM = pin_num
        self.brightness = brightness
        self.interrupt = False  # True: current animation is stopped
        self.animation=''       # animation in progress
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 150, 0)
        self.GREEN = (0, 255, 0)
        self.CYAN = (0, 255, 255)
        self.BLUE = (0, 0, 255)
        self.PURPLE = (180, 0, 255)
        self.WHITE = (255, 255, 255)
        self.rgbMIN = 10           # min pour les couleurs au hasard
        self.rgbMAXpastel = 127    # max pour les couleurs au hasard pastel
        self.rgbMAXhigh = 255      # max pour les couleurs au hasard vives
        self.wait_shortms = 0.001  # délais d'attente ultra-court (en secondes)
        self.wait_short = 0.01     # délais d'attente (secondes) courts
        self.wait_long = 0.03       # délais d'attente (secondes) plus long
    
        # Create the StateMachine with the ws2812 program, outputting on pin
        self.sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(self.PIN_NUM))

        # Start the StateMachine, it will wait for data on its FIFO.
        self.sm.active(1)

        # Display a pattern on the LEDs via an array of LED RGB values.
        self.ar = array.array("I", [0 for _ in range(self.NUM_LEDS)])

    #méthodes bas niveau allumage des leds
    #-------------------------------------------------------------------    
    def pixels_set(self, i, color):
        ''' set pixel number i with color=(r,g,b) '''
        self.ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]

    def pixels_show(self):
        ''' add data into sm FIFO: show de pixels '''
        dimmer_ar = array.array("I", [0 for _ in range(self.NUM_LEDS)])
        for i,c in enumerate(self.ar):
            r = int(((c >> 8) & 0xFF) * self.brightness)
            g = int(((c >> 16) & 0xFF) * self.brightness)
            b = int((c & 0xFF) * self.brightness)
            dimmer_ar[i] = (g<<16) + (r<<8) + b
        self.sm.put(dimmer_ar, 8)
        time.sleep_ms(10)
   
    def shuffle(self, l):
        """Fisher–Yates shuffle Algorithm : la methode random.shuffle(l) n'existant pas en micropython
            input: l = liste
            retourne la liste l mélangée
        """
        for i in range(len(l)-1, 0, -1): # parcours la liste à l'envers
            j = randint(0, i)            # random index entier dans l'intervalle [0, i]  
            l[i], l[j] = l[j], l[i]      # Swap l[i] avec l[j]
        return l

    # méthodes de rendus de couleur d'une led
    #-----------------------------------------
    def pcolor_random(self, pastel=True, red=True, green=True, blue=True):
        """ retourne une couleur (r,g,b) au hasard
            pastel: rendu de couleur pastel(True) ou vives(False)
            red=False: couleur sans rouge
            green=False: couelmur sans vert
            blue=False: couleur sans bleu
        """
        rgbMAX = pastel * self.rgbMAXpastel + (not pastel) * self.rgbMAXhigh
        r,g,b = 0,0,0
        #on évite la combinaison (0,0,0) qui éteint la led ...
        while (r+g+b) <= self.rgbMIN :
            r,g,b = red*randrange(0,rgbMAX), green*randrange(0,rgbMAX), blue*randrange(0,rgbMAX)
        return (r,g,b)

    def fade_in_out(self, fadein=True):
        """ retourne tuple (start, end, step) pour parcourir les leds du ruban dans un ordre:
              fadein = True : de la 1ère led à la dernière (valeur par défaut)
              fadein = False: de la dernière led à la première
        """
        start, end, step = 0 , self.NUM_LEDS, 1
        if not fadein:
            start, end, step = self.NUM_LEDS-1, -1 , -1
        return (start, end, step)

    def wheel(self, pos):
        ''' Input a value 0 to 255 to get a color value (r,g,b).
            The colours are a transition r - g - b - back to r.
        '''
        if pos < 0 or pos > 255:
            return (0, 0, 0)
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        if pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)
    
    def pcolor_wheel(self, id_led):
        """ retourne une couleur (r,g,b) arc-en-ciel selon la position de la led """
        pixel_index = (id_led * 256 // self.NUM_LEDS)
        return  self.wheel(pixel_index & 255) 

    #----------------------------------------------------------------------------
    #animation du ruban de leds sans délais entre les leds (toutes en même temps)
    #----------------------------------------------------------------------------
    
    def pixels_off(self):
        ''' turn off the pixels '''
        my_name= 'off'
        self.pixels_fill(self.BLACK)
        self.pixels_show()

    def pixels_fill(self, color):
        my_name = 'fill'
        ''' set all pixels with same color (r,g,b) '''
        for i in range(len(self.ar)):
            self.pixels_set(i, color)
        self.pixels_show()
           
    def fade_out(self, n_steps, color, wait=0.05):
        ''' fade out color(r,g,b) to BLACK in n_steps   '''
        my_name = 'fade_out'
        r_delta, g_delta, b_delta = color[0]//n_steps, color[1]//n_steps, color[2]//n_steps
        for j in range(n_steps):
            self.pixels_fill( (color[0]-j*r_delta , color[1]-j*g_delta , color[2]-j*b_delta) )
            time.sleep(wait)
        self.pixels_off()

    def fade_in(self, n_steps, color, wait=0.05):
        ''' fade in from BLACK to color(r,g,b) in n_steps   '''
        my_name = 'fade_in'
        r_delta, g_delta, b_delta = color[0]//n_steps, color[1]//n_steps, color[2]//n_steps
        for j in range(n_steps, 0, -1 ):
            self.pixels_fill( (color[0]-j*r_delta , color[1]-j*g_delta , color[2]-j*b_delta) )
            time.sleep(wait)
        
    def random(self, pastel=True, red=True, green=True, blue=True):
        """ anime le ruban de leds avec des couleurs aléatoires
            pastel: True/False pour avoir des couleurs pastels ou vives
            red,green,blue : True/False pour activer/désactiver une composante rouge, verte, bleu
        """
        my_name='random'
        for l in range(self.NUM_LEDS):
            self.pixels_set(l, self.pcolor_random(red=red, green=green, blue=blue))
        self.pixels_show()
        time.sleep(self.wait_long)
                
    def mono_wheel(self, delay=0.1):
        """ anime le ruban en allumant toutes les leds de la même couleur
            changmeent de couleur après chaque delay (en secondes)
            en suivant le rythme de couleur arc-en-ciel
        """
        #enchainer les couleurs arc-en-ciel pour toutes le leds
        my_name='mono_wheel'
        for j in range(255):
            for i in range(self.NUM_LEDS):
                self.pixels_set(i, self.wheel(j))
            if self.animation == my_name:
                self.pixels_show()
                time.sleep(delay)
            else:
                break         

    def rainbow_cycle(self, wait=0):
        ''' move colors in a rainbow cycle '''
        my_name = 'rainbow_cycle'
        for j in range(255):
            for i in range(self.NUM_LEDS):
                rc_index = (i * 256 // self.NUM_LEDS) + j
                self.pixels_set(i, self.wheel(rc_index & 255))
            if self.animation == my_name:
                self.pixels_show()
                time.sleep(wait)
            else:
                break

    #----------------------------------------------------------------------------
    #animation du ruban de leds avec délais entre les leds (type guirlande Noël)
    #----------------------------------------------------------------------------
    
    def fade_off(self, fadein = True, wait=0):
        """ éteint toutes les leds une après les autres
             fadein = True pour simuler un fade in en partant de la 1ère led
             fadein = False pour un fade out en partant de la dernière led
        """
        start, end, step = self.fade_in_out(fadein)
        for l in range(start, end, step):
            self.pixels_set(l, (0,0,0))
            self.pixels_show()
            time.sleep(wait)
            
    def fade_wheel(self, fadein=True, wait=0):
        """ anime le ruban de leds avec des couleurs arc-enciel
            fadein = True: fade in depuis la 1ère leds jusqu'à la dernière
            fadein = False: fade out depuis la dernière led jusqu'à la 1ère
        """
        start, end, step = self.fade_in_out(fadein)
        for l in range(start, end, step):
            self.pixels_set(l,self.pcolor_wheel(l))
            self.pixels_show()
            time.sleep(wait)
    
    def shuffle_wheel(self, wait=0):
        """ anime le ruban en allumant les leds au hasard avec couleur arc-en-ciel """
        leds = self.shuffle([i for i in range(self.NUM_LEDS)])
        for l in leds:
            pixel_index = (l * 256 // self.NUM_LEDS)
            self.pixels_set(l, self.wheel(pixel_index & 255))
            time.sleep(wait)
            self.pixels_show()
            
    def fade_random(self, fadein = True, pastel=True, red=True, green=True, blue=True, wait=0):
        """ anime le ruban de leds avec un fade-in de couleurs aléatoires
            params: fadein = True pour un Fade-in False Fade-out
            pastel: True/False pour avoir des couleurs pastels ou vives
            red,green,blue : True/False pour activer/désactiver une composante rouge, verte, bleu
        """
        start, end, step = self.fade_in_out(fadein)
        for l in range(start, end, step):
            self.pixels_set(l, self.pcolor_random(red=red, green=green, blue=blue))
            time.sleep(wait)
            self.pixels_show()
            
    def shuffle_random(self, pastel=True, red=True, green=True, blue=True, wait=0):
        """ anime le ruban en allumant les leds au hasard avec couleur aléatoire """
        leds = self.shuffle([i for i in range(self.NUM_LEDS)])
        for l in leds:
            self.pixels_set(l, self.pcolor_random(red=red, green=green, blue=blue))
            time.sleep(wait)
            self.pixels_show()
