# pico_functions_v1_1.py
# AJo/MIWB, versie-datum = 12-10-2024

# Initialiseer het ssd1306 OLED scherm (128 x 64 pixels)
def display_init(ID:int, sda_pin:int, scl_pin:int) -> object:
    from machine import Pin, I2C     # Pin & I2C classes importeren
    from ssd1306 import SSD1306_I2C  # SSD1306_I2C class importeren
    # creëer een I2C object voor communicatie tussen de pico en randapparatuur
    # https://docs.micropython.org/en/latest/library/machine.I2S.html#constructor
    i2c=I2C(ID,                      # ID van het I2C randapparaat (0 of 1)
            sda=Pin(sda_pin),        # serial data line (sd) pin nr
            scl=Pin(scl_pin),        # serial clock line (sck) pin nr
            freq=400000)             # de communicatie-snelheid (400 kHz)
    # creëer een SSD1306_I2C object om het oled schermpje te kunnen gebruiken
    # https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html
    display = SSD1306_I2C(128,       # het aantal pixels horizontaal
                          64,        # het aantal pixels verticaal
                          i2c)       # het I2C protocol object
    return display                   # het display object is het resultaat van de functie

# Geeft de gemiddelde waarde van een aantal metingen van een analoge ingang
def adc_average(ai_pin:object, count:int) -> int:
    ai_sum = 0                        # start met een som van nul
    for i in range(0,count):          # herhaal 0 t/m count-1 maal
        ai_sum = ai_sum + ai_pin.read_u16()
    return int(ai_sum/count)

# Normaliseren: waarde tussen in_min en in_max omzetten naar een percentage (0.0 .. 1.0)
def norm(value:int, in_min:int, in_max:int) -> float:
    if value > in_max:   return 1.0  # waarde > maximum
    elif value < in_min: return 0.0  # waarde < minimum
    else:
        in_range = in_max - in_min
        level = value - in_min
        return level / in_range

# Verschalen: percentage omzetten naar een waarde op een schaal tussen
# output_min en output_max
def scale(perc:float, output_min:int, output_max:int, output_type:str):
     if (perc < 0 or perc > 1):             # onjuist percentage
         print("scale: input out of range")
         return 0
     else:
        output_range = output_max - output_min
        if output_type == 'int':
            return int(output_min + perc * output_range)
        elif output_type == 'float':
            return output_min + perc * output_range
        else: print('error: wrong output type chosen')

# Tekent een horizontale niveau indicatie op een SSD1306 OLED display
def hor_level_indicator(perc:float,      # het weer te geven percentage
                        x:int, y:int,    # x, y is de positie links boven
                        length:int,      # lengte van de indicatie balk
                        width: int,      # breedte van de indicatiebalk
                        indication:str,  # 'line' of 'bar'
                        display:object): # het SSD1306 object
    display.rect(x, y, length, width, 1) # basis rechthoek tekenen
    level = int(perc * length)           # niveau van de indicatie (balk of lijn)
    if indication == 'bar':
        display.fill_rect(x, y, level, width,1)
    elif indication == 'line':
        display.vline(x+level, y, width, 1)
        if level!=0:
            display.vline(x+level-1, y, width, 1)
        if level!=length:
            display.vline(x+level+1, y, width, 1)
    else:
        print("error: wrong indication type ('bar' or 'line')")

# Tekent een verticale niveau indicatie op een SSD1306 OLED display
def vert_level_indicator(perc:float,      # het weer te geven percentage
                         x:int, y:int,    # x, y is de positie links boven
                         length:int,      # lengte van de indicatie balk
                         width:int,       # breedte van de indicatie balk
                         indication:str,  # 'line' of 'bar'
                         display:object): # het SSD1306 object
    display.rect(x, y, width, length, 1)  # basis rechthoek tekenen
    level = int(perc * length)            # niveau van de indicatie (balk of lijn)
    if indication == 'bar':
        display.fill_rect(x, y+length-level, width, level, 1)      
    elif indication == 'line':
        display.hline(x, y+length-level, width, 1)
        if level!=0:
            display.hline(x, y+length-level-1, width, 1)
        if level!=length:
            display.hline(x, y+length-level+1, width, 1)
    else:
        print("error: wrong indication type ('bar' or 'line')")

# Teken een vector met startpunt, lengte en hoek op een SSD1306 OLED display
# De hoek is positief tegen de klok in vanaf horizontaal naar rechts
def draw_vector(x1:int, y1:int, length:int, angle:int, display:object):
    from math import sin, cos, radians
    x2 = x1 + int(cos(radians(angle)) * length) 
    y2 = y1 + int(-sin(radians(angle)) * length)
    display.line(x1, y1, x2, y2, 1)

def blink_led(led:object, blink_time:int=100): # default blinktime = 100 ms
    from time import sleep_ms
    led.on()
    sleep_ms(blink_time)
    led.off()