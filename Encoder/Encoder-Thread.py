import time
from velocitygooner import VelocitySensor # pyright: ignore[reportMissingImports]

def main():
    # 1. Initialize the sensor
    sensor = VelocitySensor(port='COM12', baudrate=115200)
    
    # 2. Start the background thread
    sensor.start()

    try:
        # 3. Your main program loop
        while True:
            time.sleep(1) # print data every 1 second, adjust as needed
            
            # 4. Ask the sensor for the latest data whenever you need it
            current, average = sensor.get_data() #current velocity and average velocity / current not needed (varies a lot), average is more stable.
            
            print(f"{average:.2f}")

    except KeyboardInterrupt:
        print("\nGoobye my sweet baby gooner!")
    finally:
        # 5. Tell the background thread to safely stop and close the serial port
        sensor.stop()
        
        # Wait for the background thread to fully close before exiting main
        sensor.join() 

if __name__ == "__main__":
    main()