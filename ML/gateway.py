import serial
import requests
import time
import sys

SERIAL_PORT = 'COM10'  
BAUD_RATE = 115200

SERVER_URL = 'http://127.0.0.1:5000/readings'

print(f"--- GATEWAY STARTING ---")
print(f"Connecting to {SERIAL_PORT} at {BAUD_RATE} baud...")

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"SUCCESS: Connected to {SERIAL_PORT}!")
except Exception as e:
    print(f"\nCRITICAL ERROR: Could not open {SERIAL_PORT}.")
    print(f"Error details: {e}")
    print("\nCHECK THESE 3 THINGS:")
    print("1. Is the board plugged in?")
    print("2. Did you set the right COM number in line 8?")
    print("3. Is another program (like STM32CubeIDE Terminal) using the port? Close it.")
    sys.exit()

batch_data = []
is_recording = False

print("\nWaiting for incoming data stream...")
print("(If you see weird symbols like @@@, your Baud Rate is wrong)")

while True:
    try:
        if ser.in_waiting > 0:
            raw_line = ser.readline()
            
            try:
                
                text_line = raw_line.decode('utf-8').strip()
                
                if text_line:
                    print(f"[BOARD SAYS]: {text_line}") 

                if text_line == "START_BATCH":
                    batch_data = []
                    is_recording = True
                    print("--> Starting new batch collection...")
                
                elif text_line == "END_BATCH":
                    is_recording = False
                    print(f"--> Batch Complete. Collected {len(batch_data)} readings.")
                    
                    if len(batch_data) > 0:
                        try:
                            print(f"--> Uploading to Server...")
                            response = requests.post(SERVER_URL, json={'readings': batch_data})
                            print(f"[SERVER REPLY]: {response.json()}")
                        except Exception as e:
                            print(f"[SERVER ERROR]: Is 'server.py' running? {e}")
                            
                elif is_recording:
                    
                    parts = text_line.split(',')
                    if len(parts) == 6:
                        reading = {
                            'ax': float(parts[0]), 'ay': float(parts[1]), 'az': float(parts[2]),
                            'gx': float(parts[3]), 'gy': float(parts[4]), 'gz': float(parts[5])
                        }
                        batch_data.append(reading)
                    else:

                        if "START" not in text_line and "END" not in text_line:
                            print(f"   (Warning: Invalid data line format: {text_line})")

            except UnicodeDecodeError:
                print(f"[GARBAGE DATA]: {raw_line}") 

    except KeyboardInterrupt:
        print("\nStopping Gateway...")
        ser.close()
        break
    except Exception as e:
        print(f"Error in main loop: {e}")