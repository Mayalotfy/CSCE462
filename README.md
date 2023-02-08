# Lab 1: Traffic Light Controller

## Description
This program controls the traffic lights at a busy intersection between a crosswalk and a street.
The system works like this:
- The pedestrian pushes a button to initiate a cross.
- The street light blinks blue for 3 seconds and then turns to red.
- The crosswalk light turns green, and a timer begins counting down from 9.
    - Once it reaches 4, the light blinks blue for 4 seconds, before turning red at 0.
- The street light turns green, and remains that way for at least 20 seconds.
    - During this time, a pedestrian can push the button to queue a cross once the cooldown period is up.

## Usage
`$ python traffic_light.py` or `$ traffic_light.py`

## Files
- **traffic_light.py**: uses GPIO to control the input and output, with either polling or interrupts

## Hardware
- 2 RGB LEDs (common cathode)
    - street light attached to GPIO pins 13, 19, and 26 for red, green, and blue respectively
    - crosswalk light attached to GPIO pins 16, 20, and 21
    - resistors connecting each cathode to ground
- 1 Push Button Switch
    - attached to 3.3V power with a resistor on one side
    - attached to GPIO pin 12 on the other
        - this pin attached to ground with a high-resistance pull-down resistor
- 1 Seven Segment Display (common cathode)
    - see code for pin attachment
    - connect cathode to ground with resistor