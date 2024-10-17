Transmit and receive analog signals (rudder) over UART and display it on an OLED screen.

# Functional description
When uploaded to a Raspberry Pi (RPi) Pico running MicroPython, this program essentially does two things.
- It takes an analog input and transmits its value as a normalized value on UART.
- It receives a normalized value from UART and displays it on the OLED screen as a value, a line indicator and a vector angle indicator. It recognizes when there is no data being received on the UART and will display this on the screen accordingly, with no bar and no vector to indicate an empty UART.
# Setup
To get this working, a few peripherals are required. The pins noted here are default, but can be changed by changing the code.
- SSD1306 I2C interfaced OLED screen, SDA on pin 10 and SCL on pin 11
- Button input on pin 19.
- Potentiometer connected to V+, GND and analog input 1 (pin 27)
- UART connection to another Raspberry Pi Pico, or a jumper from the Tx to Rx to transmit to own Raspberry Pi Pico. Tx on pin 0 and Rx on pin 1.
![image](https://github.com/user-attachments/assets/1275b002-ab22-4535-8f77-f19bc2aad707)


Additionally, download the analogUartClasses.py and pico_functions_v1_1.py libraries to the RPi.
# Operation
Having installed the peripherals and their connections properly, the program should work out of the box. Run asyncUart.py on your RPi. Try changing the potentiometer to see what happens!

For more accurate readings, the potentiometer can be calibrated. Press the button, or connect the pin to V+ to initiate the calibration process. Turn the potentiometer all the way up and down, then put it back in the center. Press the button again and calibration is done.

The program recognizes when the UART connection breaks. Try severing the connection and see what the screen shows.
# Technical description
A problem with uart.readline() and Interrupt Service Requests (ISRs) is that upon running, they block the main loop. This means that everything will be dropped to run the code. This means if, for example, no data is received on the UART, the screen will also not be updated. This program addresses this problem by using [asynchronous](https://docs.python.org/3/library/asyncio.html) functions and [coroutines](https://docs.python.org/3/library/asyncio-task.html). 

There is essentially three loops running in parallel: one main loop for updating the screen, one loop for transmitting data on the UART and one loop for receiving data from the UART. Because these loops run parallel, they do not communicate with each other directly. Exchanging data is done with the help of classes.
## rudderTx
At the beginning of the program, an object `rudderTx` is instantiated from the class `LocalRudder`. This object is used to access the potentiometer and send its value on the UART. The class definition can be found in the `uartRudder.py` file.

`self.normalizedAngle` is not a attribute of the `rudderTx` object, but a [getter](https://www.geeksforgeeks.org/getter-and-setter-in-python/) method. This allows for a complex operation to return any value, as if it is accessed like a normal attribute.

For this potentiometer, three points are set: hard port, center and hard starboard. A small deadband is kept around the center position. This means that the value will be exactly 0.5 when the potentiometer is around the center position.
![image](https://github.com/user-attachments/assets/ee555a3d-a472-4fa7-b094-7c62f0e85076)
```python
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
```
This class has a function `uartTx`. When this function is called, it enters a loop which will transmit the rudder (normalized) angle on the UART roughly 100 times per second. This angle is accessed through the `self` object:
```python
uart.write(f'{self.normalizedAngle}\n'.encode())
```

## rudderRx
Another object `rudderRx` is instantiated from the class `RemoteRudder`. This object is used to access the UART to read the rudder value. A big difference to rudderTx is that this object does not have a getter method for the `normalizedAngle`. Instead, this is an actual object attribute. Why is this?

The asynchronous function `uartRx` reads from the UART buffer continuously. When there is no data on the line, the entire function will have to wait until the `readline` function times out. If `normalizedAngle` were a getter method, the buffer would have to be read every time the method is accessed. This means that a block of code that needs `normalizedAngle` would be getting delayed by waiting for data.

Instead, the UART is read asynchronously from any other processes. When data is received, the `normalizedAngle` attribute is updated with this new data. This way, `normalizedAngle` is *always* accessible.

When there is no data in the UART buffer or the data is corrupted, `normalizedAngle` is set to -1 to indicate that the data is not usable.
## asyncio
The uartTx and uartRx functions are scheduled to run asynchronously using the asyncio library:
```python
asyncio.create_task(rudderTx.uartTx(uart))
asyncio.create_task(rudderRx.uartRx())
```
Note: the `time.sleep()` function does not work together with asyncio. To delay code, use `await asyncio.sleep()`. This only works in asynchronous functions.
## LocalRudder.calibrate()
At the beginning of every iteration of the main loop, the button is checked if it is pressed. When it is pressed, `rudderTx.calibrate()` is called. In this case, the main loop is actually interrupted, as it will wait for the function to finish executing. `rudderTx.uartTx()` still executes, but will not actually transmit any data on the UART.
```python
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
```
# Challenges
Do you want to try to improve this program? Perhaps you can try the following things:
- Currently, calibration settings are not saved when the RPi restarts or shuts down. This means that the potentiometer requires recalibration every time it starts back up. Perhaps you can read and write to a file stored in the flash memory of the RPi, so the calibration settings will be persistent.
- Can you connect another potentiometer to a different UART line and display it on the screen alongside the first one?
- Perhaps you can merge the two UART lines together and only make use of a single UART line. This would require being able to differentiate between the signals for either potentiometers, so you will have to create a more sophisticated data protocol.
