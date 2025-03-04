#!/usr/bin/env python3
import time

#==============file paths================
TEMP_SENSOR = "/sys/class/thermal/thermal_zone1/temp"
TARGET_PWM = "/sys/devices/tegra-cache/subsystem/devices/pwm-fan/hwmon/hwmon4/pwm1"

#=======Reads temperature from the sensor file and returns it in °C.=======
def read_temperature(): 

    try:
        with open(TEMP_SENSOR, "r") as f:
            temp_str = f.read().strip()
        
        return int(temp_str) / 1000.0 # Convert to °C (the sensor gives temperature in millidegrees)
    except Exception as e:
        print("Error reading temperature:", e)
        return None
#=======Capture PWM value to the fan control routine.=======
def set_fan_speed(pwm_value):
    
    try:
        with open(TARGET_PWM, "w") as f:
            f.write(str(pwm_value))
    except Exception as e:
        print("Error setting fan speed:", e)
        
#=======fan mode and PWM value based on the temperature.=======
def determine_fan_settings(temperature): 
    if temperature < 40:
        mode = 0
        pwm = 80
    elif 40 <= temperature < 60:
        mode = 1
        pwm = 150
    else:
        mode = 2
        pwm = 255
    return mode, pwm

def main():
    while True:
        temperature = read_temperature()
        if temperature is None:
            time.sleep(10)
            continue

        mode, pwm = determine_fan_settings(temperature)
        print(f"Current temp: {temperature:.2f}°C, Fan mode: {mode}, PWM: {pwm}")

        set_fan_speed(pwm)
        time.sleep(10)  # Adjust the interval as needed

if __name__ == "__main__":
    main()
