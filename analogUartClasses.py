from machine import ADC, Pin
import pico_functions_v1_1 as pf
import asyncio



class Pot():
    def __init__(self, adc, pot_min, pot_max, pot_center):
        self.adc = ADC(adc)
        self.min = pot_min
        self.max = pot_max
        self.center = pot_center



class LocalRudder():
    def __init__(self, travelAngle, pot, deadbandDegrees=1):
        self._PS_MAX = - travelAngle / 2
        self._SB_MAX = travelAngle / 2
        self.pot = pot
        self.deadbandInt = deadbandDegrees / travelAngle * 65535
        self.calibration = False

    @property
    def angle(self):
        angle = pf.scale(self.normalizedAngle, self._PS_MAX, self._SB_MAX, "int")
        return angle
    
    @property
    def normalizedAngle(self):
        val = pf.adc_average(self.pot.adc, 100)
  
        if val < self.pot.center - self.deadbandInt: # PS
            normalized = pf.norm(val, self.pot.min, self.pot.center - self.deadbandInt) / 2
            return normalized
        elif val > self.pot.center + self.deadbandInt: # SB
            normalized = pf.norm(val, self.pot.center + self.deadbandInt, self.pot.max) / 2 + .5
            return normalized
        else: # Center
            return 0.5
    
    def _setMinMax(self):
        val = pf.adc_average(self.pot.adc, 100)
        self.pot.min = val if val < self.pot.min else self.pot.min
        self.pot.max = val if val > self.pot.max else self.pot.max

    async def calibrate(self, button, oled):
        self.calibration = True
        self.pot.min = 32499
        self.pot.max = 32501
        self.pot.center = 32500
        
        while button.value():
            await asyncio.sleep(0)
            
        
        while not button.value():
            self._setMinMax()
            
            oled.fill(0)
            oled.text(f'Val: {pf.adc_average(self.pot.adc, 100)}', 0, 0)
            oled.text(f'Min: {self.pot.min}', 0, 8)
            oled.text(f'Max: {self.pot.max}', 0, 16)
            oled.show()
            await asyncio.sleep(.01)
            
        val = pf.adc_average(self.pot.adc, 1000)
        self.pot.center = val
        
        while button.value():
            await asyncio.sleep(0)
            
        self.calibration = False



    async def uartTx(self, uart):
        while True:
            if self.calibration:
                await asyncio.sleep(0)
                continue
            try:
                uart.write(f'{self.normalizedAngle}\n'.encode())
                pf.blink_led(Pin(25), 5)
                await asyncio.sleep(.01)
            except Exception as e:
                print(e)



class RemoteRudder():
    def __init__(self, travelAngle, uart):
        self._PS_MAX = - travelAngle / 2
        self._SB_MAX = travelAngle / 2
        self.uart = uart
        self.normalizedAngle = -1
        
    @property
    def angle(self):
        if self.normalizedAngle == -1:
            return "Null"
        angle = round(pf.scale(self.normalizedAngle, self._PS_MAX, self._SB_MAX, "float"), 1)
        return angle        
    
    
    
    async def uartRx(self):
        while True:
            try:
                rawMsg = self.uart.readline()
                if not rawMsg:
                    self.normalizedAngle = -1
                    await asyncio.sleep(0)
                    continue
                
                msg = float(rawMsg.decode().strip())
                self.normalizedAngle = msg
                await asyncio.sleep(.01)
                
            except Exception as e:
                self.normalizedAngle = -1
                print(e)


