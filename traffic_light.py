#!/usr/bin/python


###################################
# CSCE 462 -- Lab 1
# "traffic_light.py"
# Authors: Sam Prewett, Maya Lotfy
# (c) 2023 -- All rights reserved
###################################


import RPi.GPIO as GPIO
import time
import threading


GPIO.setmode(GPIO.BOARD)

LED2_R =  33   # GPIO 13
LED2_G =  35   # GPIO 19
LED2_B =  37   # GPIO 26

LED1_R =  36   # GPIO 16
LED1_G =  38   # GPIO 20
LED1_B =  40   # GPIO 21

SSD    = [18,  # GPIO 24 - A
          22,  # GPIO 25 - B
          15,  # GPIO 22 - C
          13,  # GPIO 27 - D
          11,  # GPIO 17 - E
          16,  # GPIO 23 - F
          12]  # GPIO 18 - G

BTN    =  32   # GPIO 12

GPIO.setwarnings(False)
GPIO.setup([BTN], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Button has pull-down resistor (i.e., attach GPIO 12 to ground with resistor)
GPIO.setup([LED2_R, LED2_G, LED2_B, LED1_R, LED1_G, LED1_B] + SSD, GPIO.OUT, initial=GPIO.LOW)  # Set up outputs, begin with all off
GPIO.output(LED2_G, GPIO.HIGH)  # Set traffic light 2 (for cars) to green
GPIO.output(LED1_R, GPIO.HIGH)  # Set traffic light 1 (crosswalk) to red

crosswalk = threading.Lock()  # mutex for crosswalk being enabled
can_press_button = threading.Lock()  # mutex for whether button is already pressed

btn_pressed = False  # state of the button (for debouncing)
last_press = 0  # time (ms, since epoch) of last button press
COOLDOWN = 50  # time (ms) required between button presses

RED_TIME = 2  # time (s) when both lights should be red (might change to 0)
DIGITS = [[1, 1, 1, 1, 1, 1, 0],  # 0 - 7-segment display states for each digit & segment (A-G)
          [0, 1, 1, 0, 0, 0, 0],  # 1
          [1, 1, 0, 1, 1, 0, 1],  # 2
          [1, 1, 1, 1, 0, 0, 1],  # 3
          [0, 1, 1, 0, 0, 1, 1],  # 4
          [1, 0, 1, 1, 0, 1, 1],  # 5
          [1, 0, 1, 1, 1, 1, 1],  # 6
          [1, 1, 1, 0, 0, 0, 0],  # 7
          [1, 1, 1, 1, 1, 1, 1],  # 8
          [1, 1, 1, 1, 0, 1, 1]]  # 9

def set_number(n = None):
    """
    Displays the given digit on the 7-segment display.
    If None or no argument is given, the display is turned off.
    NOTE: Should only be used within the context of the output-controlling thread.
    """
    if n is None:
        for pin in SSD:  # Turn off all 7-segment display outputs
            GPIO.output(pin, GPIO.LOW)
    else:
        for pin, value in zip(SSD, DIGITS[n]):  # Iterates over an array of tuples: (output pin, state)
            GPIO.output(pin, GPIO.HIGH if value != 0 else GPIO.LOW)

def crosswalk_thread():
    """
    Thread function for when the crosswalk button has been pressed.
    """
    if can_press_button.locked():
        # print("[DEBUG] Already pressed.")
        return  # Exit thread if button is already pressed
    can_press_button.acquire()  # Prevent multiple button presses by locking mutex
    if crosswalk.locked():  # If we can press button BUT we're in the cooldown period, wait for it to end.
        print("Wait.")
    crosswalk.acquire()  # Make other threads wait for cycle & cooldown period to end
    # print("[DEBUG] Crosswalk activated!")
    time.sleep(1)
    GPIO.output(LED2_G, GPIO.LOW)  # Turn off green light
    for i in range(3):  # Blink blue light 3 times
        GPIO.output(LED2_B, GPIO.HIGH)
        print("\033[34mBlink!\033[0m")
        time.sleep(0.5)
        GPIO.output(LED2_B, GPIO.LOW)
        time.sleep(0.5)
    GPIO.output(LED2_R, GPIO.HIGH)  # Turn on red light
    print("\033[31mRed!\033[0m")
    time.sleep(RED_TIME)
    GPIO.output(LED1_R, GPIO.LOW)  # Turn off crosswalk red light
    GPIO.output(LED1_G, GPIO.HIGH)  # Turn on crosswalk green light
    print("\033[32mYou can cross!\033[0m")
    for i in range(9, 0, -1):  # Count down from 9 to 1
        set_number(i)  # Display countdown
        if i > 4:  # If the light should still be green...
            print(f"\033[32m{i}\033[0m")
            time.sleep(1)  # Wait 1 second
        else:  # Otherwise...
            if i == 4:
                GPIO.output(LED1_G, GPIO.LOW)  # Turn the green light off
            GPIO.output(LED1_B, GPIO.HIGH)  # Blink the blue light
            print(f"\033[34m{i}\033[0m")
            time.sleep(0.5)
            GPIO.output(LED1_B, GPIO.LOW)
            time.sleep(0.5)
    set_number(0)  # Display 0
    GPIO.output(LED1_R, GPIO.HIGH)  # Turn on the red light
    print("\033[31mDon't cross.\033[0m")
    time.sleep(RED_TIME)  # Waits some time (RED_TIME) before letting the cars go again
    set_number()  # Turn off display
    GPIO.output(LED2_R, GPIO.LOW)  # Turn off red light
    GPIO.output(LED2_G, GPIO.HIGH)  # Turn on green light
    print("\033[32mYou can drive again!\033[0m")
    # print("[DEBUG] Button can be pressed again.")
    can_press_button.release()  # Allow others to press the button again
    time.sleep(20)  # 20-second cooldown period
    # print("[DEBUG] Crosswalk is ready.")
    crosswalk.release()  # Allow another crosswalk cycle to begin

def poll_thread():
    """Thread function that polls for state changes in BTN."""
    btn_state = GPIO.LOW
    while True:
        if GPIO.input(BTN) != btn_state:  # If state has changed...
            btn_state = not btn_state
            button_press(BTN)  # Debounce and call thread if appropriate
        time.sleep(0.01)  # Wait 10ms

def button_press(button):
    """Handles a change in the state of BTN by debouncing and starting the crosswalk cycle if appropriate."""
    global last_press, btn_pressed  # Have to declare, or it thinks these are local variables
    current_time = time.time_ns() // 1e6  # Get current time in ms
    if current_time - last_press >= COOLDOWN:  # If COOLDOWN ms have passed, probably a true state change (not a bounce)...
        last_press = current_time
        # time.sleep(COOLDOWN / 1e3)
        btn_pressed = not btn_pressed  # Toggle button press state (since this should only be called on a state change)
        if btn_pressed:  # If it's down, try to initiate the crosswalk cycle
            # print("[DEBUG] Button pressed!")
            t = threading.Thread(target=crosswalk_thread)
            t.daemon = True
            t.start()
        else:
            # print("[DEBUG] Button released!")
            pass  # Only here for debug purposes

def shutdown():
    """Turns off all outputs and exits the program."""
    for pin in [LED2_R, LED2_G, LED2_B, LED1_R, LED1_G, LED1_B] + SSD:
        GPIO.output(pin, GPIO.LOW)  # Set all outputs to low
    print("Goodbye!")
    exit(0)  # Successful completion


selection = None
print("\033[1mWhich implementation do you want to run?\033[0m")  # Get user input for implementation choice
print("\033[1m1.\033[0m \tPolling")
print("\033[1m2.\033[0m \tInterrupts")
print("\033[1m3.\033[0m \tExit Program")
while selection is None:
    inp = input("\033[1m>\033[0m ")
    try:
        selection = int(inp)
        if not 1 <= selection <= 3:  # Make sure selection is within range
            selection = None
            raise ValueError()
    except ValueError:  # In case input is not an integer
        print("\033[1;31mError: please enter a valid option (1, 2, or 3).\033[0m")

if selection == 1:  # If "polling" is selected, begin polling
    pt = threading.Thread(target=poll_thread)
    pt.daemon = True
    pt.start()
elif selection == 2:  # If "interrupts" is selected, add an event callback button state change
    GPIO.add_event_detect(BTN, GPIO.BOTH, button_press)  # We do both rising and falling for debouncing purposes
else:  # Otherwise, gracefully end
    shutdown()

input("\n\033[1mPress [Enter] to stop...\033[0m\n\n")  # Wait for stdin interrupt to end program
shutdown()  # Ensure all outputs are off