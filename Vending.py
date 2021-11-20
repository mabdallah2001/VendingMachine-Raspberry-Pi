import RPi.GPIO as GPIO  #importing GPIO library to configure GPIOs
import time  #importing time library
import LCD1602 as LCD   #importing the LCD
import PCF8591 as ADC   # importing the ADC
import urllib.request   #import url library request to open thingspeak
from picamera import PiCamera   #importing picamera
from flask import Flask #importing flask to start server
from flask import send_file
from datetime import datetime
import math     #importing math library
import serial
SERIAL_PORT = '/dev/ttyS0'      #Serial port for the RFID
GPIO.setmode(GPIO.BCM)  #setting operation mode of GPIO to BCM





#Keypad inputs and outputs setup. GPIO 19 - 22: inputs. GPIO 23 - 26: Outputs
GPIO.setup(19, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
GPIO.setup(20, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
GPIO.setup(21, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
GPIO.setup(22, GPIO.IN, pull_up_down = GPIO.PUD_UP)

GPIO.setup(23, GPIO.OUT) 
GPIO.setup(24, GPIO.OUT) 
GPIO.setup(25, GPIO.OUT) 
GPIO.setup(26, GPIO.OUT)



LCD.init(0x27,1) #address of LCD is 27 (slave address & background light). Initalization
ADC.setup(0x48) #Setting up ADC and storing it to address 48

MYcamera = PiCamera()   #PiCamera instance
app = Flask(__name__)       
API_KEY = "E3D8HWJVK7T15FE6"    #Thingspeak write API key

#setting the LEDs to their pins
YELLOWLED = 16     # Yellow LED connected to GPIO 16. Flashes during maintenance
BLUELED = 12    # Blue LED connected to GPIO 12 Turns on when System is on.
DISPENSE = 6    #push button set to pin 6 to dispense item
CANCEL = 4     # push button set to GPIO 4 to cancel input
TRIG = 18   #trig set to pin 18
ECHO = 5    #echo set to pin 5
BUZZ = 27   #buzzer set to pin 27

Flag=0


# GPIO.setup(REDLED,GPIO.OUT) #setting switch as output
GPIO.setup(BLUELED,GPIO.OUT) #setting switch as output
GPIO.setup(YELLOWLED,GPIO.OUT) #setting switch as output
GPIO.setup(DISPENSE,GPIO.IN, pull_up_down= GPIO.PUD_DOWN) #setting switch as input
GPIO.setup(CANCEL,GPIO.IN, pull_up_down= GPIO.PUD_DOWN) #setting switch as output
GPIO.setup(TRIG, GPIO.OUT) #setting switch as output
GPIO.setup(ECHO,GPIO.IN) #setting switch as input
GPIO.setup(BUZZ, GPIO.OUT) #setting switch as output


#Buzzer
Buzzer = GPIO.PWM(BUZZ,250) # setting initial  frequency to 250
Buzzer.start(0) #Start buzzer with inital duty cycle 0

GPIO.setwarnings(False)


# Trigger camera function
def camera():
    timestamp = datetime.now().isoformat()
    photoPath = "/home/pi/Desktop/securityPic.jpg" # Save to this directory and file path
    MYcamera.annotate_text="Pic taken at time %s" %timestamp    # Display annotation on pic
    time.sleep(2)   #Sleep for 2 secs for camera sensors to adjust and stabilize to the ambient light
    MYcamera.capture(photoPath)     # Take a picture and store to photoPath Directory.
    
#Index Route
@app.route('/')
def index():
    return "Welcome to the vending machine. Please navigate to route /Vending to start using the machine."

#First Static route
@app.route('/Vending')
def vending():
    return '''
                1A = Coke           (AED 2)
                2B = 7UP            (AED 2)
                3C = Fanta          (AED 2)
                4D = Mountain Dew   (AED 2)
            '''

#Second Static Route
@app.route('/Vending/help')
def vendingHelp():
    return "Hello! If you're having trouble with the vending machine, please contact maintainance at 06 515 5555. Have a nice day :)"

#Third static route (Display image captured from camera)
@app.route('/Vending/securityImage')
def vendingImage():
    photoPath = "/home/pi/Desktop/securityPic.jpg"
    response = send_file(photoPath)
    return response

#First dynamic route, passes in the limit for temperature of vending machine.
@app.route('/Vending/temp/<limit>')
def vendingTemp(limit):
    limit = float(limit)    # Cast string to float
    temp = tempSensor(1)    # Read temp from ch 1
    if (temp>limit):
        msg = "Warning! Temperature is too high. Temp = {} C. Call Maintainance".format(temp)
        return msg
    else:
        msg = "Temperature is good. Temp = {} C".format(temp)
        return msg

#Second dynamic route, passes in the limit for quantity of drinks stored in vending machine.
@app.route('/Vending/quantity/<limit>')
def vendingQ(limit):
    limit = float(limit)    # Cast string to float
    quantity = math.floor(quantityFunc(0))  # Read quantity from ch 0
    if (quantity<limit):
        return "Warning! We're making money but quantity is reaching out of stock. Call Maintainance. Quantity = {}".format(quantity)
        
    else:
        return "Not making enough sales unforunately. Quantity = {}".format(quantity)
    
    

    
# Distance Function from Ultrasonic Sensor
def distanceFunc():
        GPIO.output(TRIG, GPIO.LOW)     # make it low
        time.sleep(0.000002)    
        GPIO.output(TRIG, 1)    # generate pulse of 10us
        time.sleep(0.00001)
        GPIO.output(TRIG, 0)    # read echo pin and calculate distance in cm
        while GPIO.input(ECHO) == 0:
            a = 0       # dummy                                     
        time1 = time.time()                 # Capture time1           
        while GPIO.input(ECHO) == 1:
            a = 0                   # dummy                               
        time2 = time.time()                 # Capture time2            
        duration = time2 - time1
        return duration*1000000/58      # Sensor equation

# RFID Function:
def validate_rfid(code):
    s = code.decode("ascii")    # Decode the code to ascii
    if (len(s) == 12) and (s[0] == "\n") and (s[11] == "\r"):   # Checks if we matched a code and byte length is 12, first byte is a start byte and last byte is a stop byte.
        return s[1:-1]  # Return the unique ID 
    else:
        return False    # Return false boolean as we didnt match a code
ser = serial.Serial(baudrate = 2400,
                    bytesize = serial.EIGHTBITS,
                    parity   = serial.PARITY_NONE,
                    port     = SERIAL_PORT,
                    stopbits = serial.STOPBITS_ONE,
                    timeout  = 1)


#Read input from keypad Function

def keypad(): 
    while(True): 

        #Scan row 1 for inputs
        GPIO.output(26, GPIO.LOW)
        GPIO.output(25, GPIO.HIGH)
        GPIO.output(24, GPIO.HIGH)
        GPIO.output(23, GPIO.HIGH)

        if (GPIO.input(22)==0):
            return(1)
            break

        if (GPIO.input(21)==0):
            return(4)
            break

        if (GPIO.input(20)==0):
            return(7)
            break

        if (GPIO.input(19)==0):
            return('#')
            break

        #Scan row 2 for inputs
        GPIO.output(26, GPIO.HIGH)
        GPIO.output(25, GPIO.LOW)
        GPIO.output(24, GPIO.HIGH)
        GPIO.output(23, GPIO.HIGH)

        if (GPIO.input(22)==0):
            return(2)
            break

        if (GPIO.input(21)==0):
            return(5)
            break

        if (GPIO.input(20)==0):
            return(8)
            break
 
        if (GPIO.input(19)==0):
            return(0)
            break

        #Scan row 3 for inputs
        GPIO.output(26, GPIO.HIGH)
        GPIO.output(25, GPIO.HIGH)
        GPIO.output(24, GPIO.LOW)
        GPIO.output(23, GPIO.HIGH)

        if (GPIO.input(22)==0):
            return(3)
            breakGPIO.output(BLUELED, GPIO.LOW)  

        if (GPIO.input(21)==0):
            return(6)
            break
        if (GPIO.input(20)==0):
            return(9)
            break
 
        if (GPIO.input(19)==0):
            return('#')
            break
        
        #Scan row 4 for inputs
        GPIO.output(26, GPIO.HIGH)
        GPIO.output(25, GPIO.HIGH)
        GPIO.output(24, GPIO.HIGH)
        GPIO.output(23, GPIO.LOW)

        if (GPIO.input(22)==0):
            return('A')
            break

        if (GPIO.input(21)==0):
            return('B')
            break

        if (GPIO.input(20)==0):
            return('C')
            break

        if (GPIO.input(19)==0):
            return('D')
            break


# Interrupt Function for cancelling button
def action(self):
    global Flag     #Sets flag as global
                    
    if (Flag==1):   #Checks if flag = 1 to trigger the interrupt
        print("Canceling..")    #Print cancelling
        print('Thanks Come Again!')
        GPIO.output(BLUELED, GPIO.LOW)  # Turn off the BLUE LED
        Flag=0  # Set flag back to 0

        
        
GPIO.add_event_detect(CANCEL,GPIO.FALLING, callback=action, bouncetime=2000)  #Interrupt triggered when pressing the cancel button.

#Flash Function (ADC)
def flash():
    for i in range (0,2):   #Loop Twice
        ADC.write(255)      #Write to ADC high (2^8) which turns on the RED LED
        time.sleep(1.5)     #Sleep 1.5s
        ADC.write(0)    #Write to ADC low (0) which turns off the RED LED
        time.sleep(1.5) #Sleep 1.5s
            
        

#Temperature sensor function
def tempSensor(ch):
    tempUnits = ADC.read(ch)    #Read ADC of channel number
    tempVolts = (tempUnits * 3.3) / 256     #Convert units to voltage 
    tempC = tempVolts / 0.125    #Convert Voltage to C  (range 0-27 degrees)

    return tempC    #Return temp in C

#Quantity Function
def quantityFunc(ch):
    qUnits = ADC.read(ch)   #Read ADC of channel number 
    qVolts = (qUnits*3.3) / 256     #Convert units to voltage 
    
    quantity = qVolts / 0.38 # Convert Voltage to quantity. 8 drinks is the maximum quantity that the vending machine can store
    return quantity     #Return quantity
    

# The MAIN Program:
balance = 10.0      # Customer starts off with 10 Dhs balance
quantity = math.floor(quantityFunc(0))  # Read quantity from ch0 and floor the value
temp = tempSensor(1)     # Read temperature from ch1
drinks = [quantity, quantity, quantity, quantity]  # Store Drinks in order of Coke, 7up, Fanta, Dew
repair = 0  #Temp flag
restock = 0    #quantity flag
start = 0   #start flag
tempMSG = "Temp: %d C" %temp
quantityMSG = "C:%d 7:%d F:%d D:%d" %(drinks[0], drinks[1], drinks[2], drinks[3])
LCD.write(0,0,tempMSG)  #Display Temp on LCD when system idle
LCD.write(0,1,quantityMSG)  #Display quantity of drinks on LCD when system idle
while True:
    distance = distanceFunc()   # Continuously read distance from ultrasonic sensor
    temp = tempSensor(1)    # Read temperature from ch1
    
    x = urllib.request.urlopen("https://api.thingspeak.com/update?api_key={}&field1={}&field2={}&field3={}&field4={}&field5={}".
    format(API_KEY ,temp,drinks[0],drinks[1], drinks[2], drinks[3]))    #Write to thingspeak the temp and drink values
    if(temp>15):    # checks if temp is too high 
        if(repair == 0):
            print('Warning! Refregiator is broken. Temp = {} C'.format(temp))
            repair = 1  #Trigger temp broken flag

    if(distance < 40):  # Detects if person is infront of vending machine and start the system.
        if(start == 0):
            LCD.clear()
            LCD.write(0,0,'Welcome')
            LCD.write(0,1,'Pls swipe card')  
            print('Welcome. Please swipe card')
            data = ser.read(12)     #Read RFID Tag
            ser.flushInput()    #Flushes RFID input
            ser.flushOutput()       #Flushes RFID output
            time.sleep(0.5)
            code = validate_rfid(data)      #Validate the RFID tag and get the 10 byte code.
            if code:    # if RFID reader read code, begin
                print("Read RFID: " + code) #Print code that was read
                start = 0   # set flag to 0
                if (code == "5300C8121A"):      # Customer RFID Tag
                    GPIO.output(BLUELED, GPIO.HIGH)     # Trigger BLUE LED 
                    fundsMSG = "Balance: AED %f " %balance 
                    LCD.write(0,0, fundsMSG)    #Display current balance on LCD
                    LCD.write(0,1,'Enter Selection')
                    print(fundsMSG)
                    print('Enter Selection')
                    print('''
                    1A = Coke [{}]           (AED 2)
                    2B = 7UP [{}]            (AED 2)
                    3C = Fanta [{}]          (AED 2)
                    4D = Mountain Dew [{}]   (AED 2)
                    '''.format(drinks[0], drinks[1], drinks[2], drinks[3]))     #Prints vending machine selection
                    Flag = 1    # Trigger interrupt flag to 1
                    key1 = keypad()     #Read first key input from keypad
                    time.sleep(1)
                    key2 = keypad() #Read second key input from keypad
                    time.sleep(1)
                    keyf = str(key1)+str(key2)  # concatenate both keys
                    LCD.write(0,1,'                ')   #clear lcd line 1
                    keyMSG = "Selection: " + keyf  
                    print(keyMSG)
                    LCD.write(0,1,keyMSG)   #Display user input on LCD
                    
                    

                    # Dispensing Soft Drinks:
                    invalid = 0     # Set invalid flag to 0
                    while(GPIO.input(DISPENSE) == 0):   #Wait until dispense button is pressed
                        if Flag==0:
                            break   # if cancel button is pressed, trigger the interrupt and break the loop
                        a = 0  #Dummy
                    LCD.clear()
                    
                    if Flag==0:
                        LCD.write(0,0,'Thnx Come Again!')
                        LCD.write(0,1,fundsMSG) #print balance
                        time.sleep(3)
                        LCD.clear()
                        continue  # navigate back to the beginning of the while loop
                    
                    LCD.write(0,0,'Dispensing') # Display disepsning
                    if(keyf == '1A'):   #If keypad input is 1A, 
                        if(drinks[0] == 0):     #Check if drink is 0 quantity, display out of stock
                            print('Out of stock')
                            LCD.write(0,0,'Out of stock')
                            invalid = 1     #trigger invalid flag
                        else:
                            LCD.write(0,1,'Coke..')     # else, display dispense coke
                            print('Dispensing Coke..')
                            drinks[0] -= 1      # decrement coke quantity
                            
                    elif(keyf == '2B'):
                        if(drinks[1] == 0):
                            print('Out of stock')
                            LCD.write(0,0,'Out of stock')
                            invalid = 1
                        else: 
                            LCD.write(0,1,'7UP..')
                            print('Dispensing 7UP..')
                            drinks[1] -= 1  # decrement 7up quantity
                    elif(keyf == '3C'):
                        if(drinks[2] == 0):
                            print('Out of stock')
                            LCD.write(0,0,'Out of stock')
                            invalid = 1
                        else:    
                            LCD.write(0,1,'Fanta..')
                            print('Dispensing Fanta..')
                            drinks[2] -= 1  # decrement fanta quantity
                    elif(keyf == '4D'):
                        if(drinks[3] == 0):
                            print('Out of stock')
                            LCD.write(0,0,'Out of stock')
                            invalid = 1
                        else:
                            LCD.write(0,1,'Mountain Dew..')
                            print('Dispensing Mountain Dew..')
                            drinks[3] -= 1      # decrement dew quantity
                    else:
                        LCD.write(0,0, 'Invalid Selection')     #IF invalid keypad input, display invalid selection
                        LCD.write(0,1, 'Pls Try Again')
                        print('Invalid Selection')
                        invalid = 1     #trigger invalid flag
                    if(invalid == 0):   # if invalid flag is not triggered, begin
                    
                        Buzzer.ChangeDutyCycle(50)  # Start Buzzer while dispensing soda 
                        flash() # Flashes the red LED while dispensing
                        Buzzer.ChangeDutyCycle(0)   # Stop Buzzer after compeletion
                        camera()    # Trigger camera to capture a picture of the customer
                        balance -= 2    #Decrement balance by 2 AED.
                        fundsMSG = "Balance: AED %f " %balance  
                        print('Thanks come again!')
                        print(fundsMSG)
                        LCD.write(0,0,'Thnx come again!')       #Display new available balance
                        LCD.write(0,1,fundsMSG)
                        Flag = 0    # set interrupt flag to 0
                    time.sleep(4)   #sleep for 4 secs
                    GPIO.output(BLUELED, GPIO.LOW)          # Turn off BLUE LED.      
                    LCD.clear()     #Clear LCD
                    

                elif (code == "4600386996"): # Maintenance/Restock RFID Tag
                    GPIO.output(YELLOWLED, GPIO.HIGH)       # Trigger Yellow LED for maintaince
                    if(repair == 1):    #check if repair flag is triggered
                        print('Fixing Fridge..')    # Print fixing fridge
                        LCD.write(0,0,'Fixing fridge..')
                        tempMSG = "Temp: %f C" %temp
                        print(tempMSG)
                        LCD.write(0,1,tempMSG)  # Display current temp
                        while(temp>15):
                            temp = tempSensor(1)    #continously read temp from sensor until temp < 15
                            time.sleep(0.25)
                        LCD.clear()
                        print('Fixing Complete!')
                        LCD.write(0,0,'Fixing Complete!')
                        tempMSG = "Temp: %f C" %temp
                        LCD.write(0,1,tempMSG)  # Display new temp after fix,
                        print(tempMSG)
                        repair = 0
                        time.sleep(4)   #sleep for 4 secs
                        LCD.clear()     # clear LCD

                    print('''
                    Coke [{}]           
                    7UP [{}]            
                    Fanta [{}]          
                    Mountain Dew [{}]   
                    '''.format(drinks[0], drinks[1], drinks[2], drinks[3]))     # Print available  drink quantities
                    for i in range (0,4):
                        if(drinks[i] < 2):  # Check if any quantity of drinks is less than 2
                            restock = 1 #Trigger restock flag if so.
                    if(restock == 1):   # if trigger flag is triggered, begin restocking
                        quantityMSG = "C:%d 7:%d F:%d D:%d" %(drinks[0], drinks[1], drinks[2], drinks[3])
                        print('Restocking..')
                        LCD.write(0,0,'Restocking..')
                        LCD.write(0,1, quantityMSG)
                        Flag = 0
                        Buzzer.ChangeDutyCycle(50)  # Start Buzzer while Restocking soda 
                        flash() # Flashes the red LED while Restocking
                        Buzzer.ChangeDutyCycle(0)   # Stop Buzzer after compeleting restocking
                        #quantity = math.floor(quantityFunc(0))
                        drinks = [8, 8, 8, 8]  # Coke, 7up, Fanta, Dew
                        print('Complete!')
                        print('''
                        Coke [{}]           
                        7UP [{}]            
                        Fanta [{}]          
                        Mountain Dew [{}]   
                        '''.format(drinks[0], drinks[1], drinks[2], drinks[3]))     # print new quantities
                        quantityMSG = "C:%d 7:%d F:%d D:%d" %(drinks[0], drinks[1], drinks[2], drinks[3])
                        LCD.clear()
                        LCD.write(0,0,'Complete!')
                        LCD.write(0,1, quantityMSG) #Display new quantities
                        restock = 0     # Set restock flag back to 0
                        time.sleep(5)       # sleep for 5 secs
                    if(restock == 0 and repair == 0):       # if stock is high and temperature is below threshold, print no maintaince needed.
                        print("All looks good! No maintainance needed")
                        LCD.clear()
                        LCD.write(0,0,'All looks good!')
                        LCD.write(0,1,'No need service!')
                        time.sleep(4)
                    GPIO.output(YELLOWLED, GPIO.LOW)    #  trigger yellow LED Off for completion of maintainance
                    LCD.clear()     # clear lcd
                elif (code == "010FB3CB43"):        # Flask Server Code
                    print("Running Flask Server..")
                    LCD.clear()     # Clear LCD
                    LCD.write(0,0,'Running Flask')
                    LCD.write(0,1,'Server..')       # Display running Flask Server..

                    
                    if __name__ == '__main__': 
                        app.run(host='0.0.0.0', port=5040)      # Start Flask Server.
            start = 1       # Trigger start flag to 1.
            
            
    else:
        start = 0
        tempMSG = "Temp: %d C" %temp        
        quantityMSG = "C:%d 7:%d F:%d D:%d" %(drinks[0], drinks[1], drinks[2], drinks[3])
        LCD.write(0,0,tempMSG)      # continously display temp on LCD while system is idle
        LCD.write(0,1,quantityMSG)  # continously display quantity on LCD while system is idle           
        
    GPIO.output(BLUELED, GPIO.LOW)              # Trigger BLUE LED to low while system is idle
    GPIO.output(YELLOWLED, GPIO.LOW)            # Trigger Yellow LED to low while system is idle


'''
big card 5300C8121A
white circle 4600386996
black circle 010FB3C21B

'''