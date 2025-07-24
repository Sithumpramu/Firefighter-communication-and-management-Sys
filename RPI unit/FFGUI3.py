import tkinter as tk
from tkinter import ttk
import serial
import json
import threading
import webbrowser
import RPi.GPIO as GPIO
import time
import subprocess

# === Serial Setup ===
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# === GPIO Setup ===
LED_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# === Thresholds ===
TEMP_THRESHOLD = 25.0
HUMIDITY_THRESHOLD = 20.0

# === Track latest values from each unit ===
unit1_data = {"lat": 0.0, "lon": 0.0, "temp": 0.0, "flame": 1}
unit2_data = {"lat": 0.0, "lon": 0.0, "temp": 0.0, "flame": 1}

# === GUI Setup ===
root = tk.Tk()
root.title("Firefighter Monitoring GUI")
root.geometry("800x600")

main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=10, fill='both', expand=True)

left_frame = tk.Frame(main_frame)
left_frame.pack(side='left', padx=20, pady=10, anchor='n')

right_frame = tk.Frame(main_frame)
right_frame.pack(side='right', padx=20, pady=10, anchor='n')

# --- Firefighter Unit 1 Variables ---
temp1_var = tk.StringVar()
humidity1_var = tk.StringVar()
flame1_var = tk.StringVar()
lat1_var = tk.StringVar()
lon1_var = tk.StringVar()
panic1_var = tk.StringVar()

# --- Firefighter Unit 2 Variables ---
temp2_var = tk.StringVar()
humidity2_var = tk.StringVar()
flame2_var = tk.StringVar()
lat2_var = tk.StringVar()
lon2_var = tk.StringVar()
panic2_var = tk.StringVar()

# --- Disconnection Indicators ---
last_received = {1: time.time(), 2: time.time()}
disconnected_label_1 = tk.Label(left_frame, text="", fg="red")
disconnected_label_2 = tk.Label(right_frame, text="", fg="red")

# --- Panic Labels ---
panic_label_1 = tk.Label(left_frame, textvariable=panic1_var, fg="blue", font=("Helvetica", 10, "bold"))
panic_label_2 = tk.Label(right_frame, textvariable=panic2_var, fg="blue", font=("Helvetica", 10, "bold"))

# === Functions ===
# Updates location.json with current positions and data
def update_location_file():
    def is_danger(unit_data, humidity_str):
        try:
            temp = float(unit_data["temp"])
            flame = int(unit_data["flame"])
            humidity = float(humidity_str.split()[0])
            return (temp >= TEMP_THRESHOLD or humidity <= HUMIDITY_THRESHOLD or flame == 0)
        except:
            return False

    data = {
        "unit1": {
            "lat": unit1_data["lat"],
            "lon": unit1_data["lon"],
            "temp": unit1_data["temp"],
            "flame": unit1_data["flame"],
            "panic": unit1_data.get("panic", 0),
            "danger": is_danger(unit1_data, humidity1_var.get())
        },
        "unit2": {
            "lat": unit2_data["lat"],
            "lon": unit2_data["lon"],
            "temp": unit2_data["temp"],
            "flame": unit2_data["flame"],
            "panic": unit2_data.get("panic", 0),
            "danger": is_danger(unit2_data, humidity2_var.get())
        }
    }
    with open("location.json", "w") as f:
        json.dump(data, f)
        
def open_map(lat, lon):
    if lat and lon:
        url = f"https://www.google.com/maps?q={lat},{lon}"
        try:
            subprocess.Popen([
                'chromium-browser',
                '--disable-gpu',
                '--disable-software-rasterizer',
                url
            ])
        except FileNotFoundError:
            print("Chromium browser not found.")

def send_blink_command(unit_id): # Sends a manual blink command to the specified unit via LoRa
    try:
        command = json.dumps({"id": unit_id, "command": "blink"})
        for _ in range(2):#sending 2 times to ensure firefighter unit catch it. 
            ser.write((command + '\n').encode())
            ser.flush()
            time.sleep(0.5)
        print("Sent command:", command)
    except Exception as e:
        print("Error sending command:", e)

def open_live_map():
    def start_server():
        subprocess.Popen(["python3", "-m", "http.server", "8000"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    
    def open_browser():
        time.sleep(2)
        subprocess.Popen([
            "chromium-browser",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "http://localhost:8000/map.html"
        ])
    
    threading.Thread(target=start_server, daemon=True).start()
    threading.Thread(target=open_browser, daemon=True).start()

# === Serial Reading Thread ===
def read_serial():
    while True:
        try:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                print("Received:", line)
                data = json.loads(line)
                unit_id = data.get("id")
                
                if unit_id == 1:
                    last_received[1] = time.time()
                    unit1_data.update({
                        "lat": float(data['lat']),
                        "lon": float(data['lon']),
                        "temp": float(data['temp']),
                        "flame": int(data['flame'])
                    })
                    temp = float(data['temp'])
                    humidity = float(data['humidity'])
                    # Check for error codes and convert to human-readable status in GUI
                    if temp == -999:
                        temp1_var.set("Sensor error")
                    else:
                        temp1_var.set(f"{temp} °C")
                    
                    if humidity == -999:
                        humidity1_var.set("Sensor error")
                    else:
                        humidity1_var.set(f"{humidity} %")
                 
                 
                    temp1_label.config(fg="red" if temp >= TEMP_THRESHOLD else "black")
                    humidity1_label.config(fg="red" if humidity <= HUMIDITY_THRESHOLD else "black")
                    
                    lat1_var.set(str(data['lat']))
                    lon1_var.set(str(data['lon']))
                    flame1_var.set("Sensor error" if data["flame"] == -1 else "Yes" if data["flame"] == 0 else "No")
                    panic1_var.set("PANIC!" if data.get("panic", 0) == 1 else "")
                
                elif unit_id == 2:
                    last_received[2] = time.time()
                    unit2_data.update({
                        "lat": float(data['lat']),
                        "lon": float(data['lon']),
                        "temp": float(data['temp']),
                        "flame": int(data['flame'])
                    })
                    temp = float(data['temp'])
                    humidity = float(data['humidity'])
                    
                    if temp == -999:
                        temp2_var.set("Sensor error")
                    else:
                        temp2_var.set(f"{temp} °C")
                    
                    if humidity == -999:
                        humidity2_var.set("Sensor error")
                    else:
                        humidity2_var.set(f"{humidity} %")

                    temp2_label.config(fg="red" if temp >= TEMP_THRESHOLD else "black")
                    humidity2_label.config(fg="red" if humidity <= HUMIDITY_THRESHOLD else "black")
                    
                    lat2_var.set(str(data['lat']))
                    lon2_var.set(str(data['lon']))
                    flame2_var.set("Sensor error" if data["flame"] == -1 else "Yes" if data["flame"] == 0 else "No")
                    panic2_var.set("PANIC!" if data.get("panic", 0) == 1 else "")
                
                update_location_file()
        except Exception as e:
            print("Parsing error:", e)

threading.Thread(target=read_serial, daemon=True).start()

# === Disconnection Checker ===
# Checks last received time for each unit, flags if no data for >10s
def check_disconnection():
    now = time.time()
    if now - last_received[1] > 10:
        disconnected_label_1.config(text="DISCONNECTED")
    else:
        disconnected_label_1.config(text="")
    
    if now - last_received[2] > 10:
        disconnected_label_2.config(text="DISCONNECTED")
    else:
        disconnected_label_2.config(text="")
    
    root.after(2000, check_disconnection)

check_disconnection()

# === Unit 1 Display ===
tk.Label(left_frame, text="Firefighter Unit 1", font=("Helvetica", 12, "bold")).pack()
tk.Label(left_frame, text="Temperature:").pack()
temp1_label = tk.Label(left_frame, textvariable=temp1_var)
temp1_label.pack()
tk.Label(left_frame, text="Humidity:").pack()
humidity1_label = tk.Label(left_frame, textvariable=humidity1_var)
humidity1_label.pack()
tk.Label(left_frame, text="Flame Detected:").pack()
tk.Label(left_frame, textvariable=flame1_var).pack()
tk.Label(left_frame, text="Latitude:").pack()
tk.Label(left_frame, textvariable=lat1_var).pack()
tk.Label(left_frame, text="Longitude:").pack()
tk.Label(left_frame, textvariable=lon1_var).pack()
disconnected_label_1.pack()
panic_label_1.pack()
tk.Button(left_frame, text="Show Location", command=lambda: open_map(lat1_var.get(), lon1_var.get())).pack(pady=5)
tk.Button(left_frame, text="Warn Firefighter 1 (Blink LED)", command=lambda: send_blink_command(1)).pack(pady=5)

# === Unit 2 Display ===
tk.Label(right_frame, text="Firefighter Unit 2", font=("Helvetica", 12, "bold")).pack()
tk.Label(right_frame, text="Temperature:").pack()
temp2_label = tk.Label(right_frame, textvariable=temp2_var)
temp2_label.pack()
tk.Label(right_frame, text="Humidity:").pack()
humidity2_label = tk.Label(right_frame, textvariable=humidity2_var)
humidity2_label.pack()
tk.Label(right_frame, text="Flame Detected:").pack()
tk.Label(right_frame, textvariable=flame2_var).pack()
tk.Label(right_frame, text="Latitude:").pack()
tk.Label(right_frame, textvariable=lat2_var).pack()
tk.Label(right_frame, text="Longitude:").pack()
tk.Label(right_frame, textvariable=lon2_var).pack()
disconnected_label_2.pack()
panic_label_2.pack()
tk.Button(right_frame, text="Show Location", command=lambda: open_map(lat2_var.get(), lon2_var.get())).pack(pady=5)
tk.Button(right_frame, text="Warn Firefighter 2 (Blink LED)", command=lambda: send_blink_command(2)).pack(pady=5)

# === Centered Live Map Button ===
tk.Button(root, text="Open Live Map", command=lambda: open_live_map()).pack(pady=20)

# === Graceful Exit ===
def on_close():
    GPIO.cleanup()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
