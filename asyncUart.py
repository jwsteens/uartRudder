from machine import Pin, UART, ADC
from time import sleep, sleep_ms, ticks_ms
import pico_functions_v1_1 as pf
import asyncio
from analogUartClasses import *

button = Pin(19, Pin.IN, pull=Pin.PULL_DOWN)
uart = UART(0, 19200, tx=Pin(0), rx=Pin(1), timeout=10)
rudderTx = LocalRudder(120, Pot(1, 288, 65435, 32500))
rudderRx = RemoteRudder(120, uart)
oled = pf.display_init(ID=1, sda_pin=10, scl_pin=11)

async def main():
    
    asyncio.create_task(rudderTx.uartTx(uart))
    asyncio.create_task(rudderRx.uartRx())
    
    while True:
        
        if button.value(): await rudderTx.calibrate(button, oled)
        
        oled.fill(0)
        
        angleString = f'{rudderRx.angle}'
        
        oled.text(angleString, 64 - len(angleString) * 4, 6)
        pf.hor_level_indicator(rudderRx.normalizedAngle, 32, 16, 64, 8, "line", oled)
        if not rudderRx.normalizedAngle == -1: pf.draw_vector(64, 32, 32, rudderRx.angle - 90, oled)
        
        oled.show()
        
        await asyncio.sleep(0)
    
    
asyncio.run(main())