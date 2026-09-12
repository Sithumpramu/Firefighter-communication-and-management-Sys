# Firefighter Communication and Management System

An asynchronous embedded IoT and telemetry platform engineered to monitor first-responder safety in hazardous environments. The system captures real-time environmental and positional metrics from wearable hardware nodes and transmits them across long-range, interference-resilient wireless channels to a centralized monitoring station.

---

## Architecture Overview

```
+-------------------------------------------------------------+
|                     Field Wearable Node                     |
|                                                             |
|  [ Temperature / Humidity ]                                 |
|  [ Flame Sensor           ] ---> [ Arduino Unit (C++) ]     |
|  [ GPS Receiver           ]              |                  |
+------------------------------------------|------------------+
                                           | (LoRa Telemetry)
                                           v
+-------------------------------------------------------------+
|                     Base Control Station                    |
|                                                             |
|   [ LoRa Receiver ] ---> [ Raspberry Pi Unit (Python) ]     |
|                                    |                        |
|                                    v                        |
|                [ Control GUI / Safety Map Visualizer ]      |
+-------------------------------------------------------------+
```

The system is separated into two operational layers:

1. **Field Sensor Nodes (`arduino units`):** Low-power Arduino microcontrollers interfacing with environmental and spatial sensors, handling edge validation and payload serialization.
2. **Central Monitoring Unit (`RPI unit`):** A Raspberry Pi receiver station executing Python background workers to parse incoming packet buffers, check threshold boundaries, and render telemetry updates on an operations interface.

---

## Key Features

* **Environmental Telemetry:** Continuous sampling of ambient temperature, humidity levels, and active flame presence.
* **Positional Tracking:** GPS coordinate tracking to maintain situational awareness of field personnel.
* **Resilient LoRa Transmission:** Long-Range (LoRa) radio communication featuring custom retry algorithms and packet acknowledgment structures to minimize dropped telemetry under extreme structural interference.
* **Control Room Interface:** Real-time Python GUI visualizing unit health and mapping telemetry directly onto interactive geospatial map coordinates with automated safety perimeter alerts.

---

## Tech Stack & Hardware Components

* **Languages:** C++, C, Python
* **Embedded Hardware:** Arduino Microcontrollers, Raspberry Pi
* **Radio & Networking:** LoRa Transceiver Modules, Serial/UART Interfaces, Custom Packet Protocols
* **Sensors:** Flame Detection Module, Temperature/Humidity Sensor, GPS Positioning Module
* **Software Tools:** Google Maps API, Tkinter/PyQt, Python Serial, PlatformIO / Arduino IDE

---

## Repository Structure

```
Firefighter-communication-and-management-Sys/
├── RPI unit/                  # Raspberry Pi central base station code
│   └── (telemetry parsing, GUI listener, mapping scripts)
├── arduino units/             # Microcontroller sensor node firmwares
│   └── (sensor acquisition, LoRa transmitter loops, packet formatting)
├── .gitattributes             # Repository language and line-ending attributes
└── README.md                  # System documentation
```

---

## Hardware Configuration & Wiring

### 1. Arduino Sensor Node (`arduino units`)
Connect the sensors to the Arduino via GPIO and Analog pins:
* **LoRa Module:** SPI pins (MISO, MOSI, SCK, NSS/CS), DIO0, RST
* **Temperature / Humidity Sensor:** Digital GPIO with pull-up resistor
* **Flame Sensor:** Digital Interrupt or Analog Pin
* **GPS Module:** Hardware or Software UART (RX/TX cross-connected)

### 2. Raspberry Pi Base Station (`RPI unit`)
* Wire the matching LoRa receiver module via SPI (`/dev/spidev0.0`) or via USB-to-UART bridge.
* Ensure SPI and Serial interfaces are enabled in `raspi-config`.

---

## Getting Started

### Prerequisites

* Arduino IDE or PlatformIO
* Python 3.9+ installed on the base station
* Required Python packages:
  ```bash
  pip install pyserial requests
  ```

### Flashing the Sensor Nodes

1. Navigate to the `arduino units` directory.
2. Open the source files in the Arduino IDE or PlatformIO.
3. Select your microcontroller board model and appropriate COM port.
4. Verify pin configurations match your physical wiring.
5. Compile and upload the firmware to the wearable unit.

### Running the Base Station

1. Clone the repository onto the Raspberry Pi:
   ```bash
   git clone [https://github.com/Sithumpramu/Firefighter-communication-and-management-Sys.git](https://github.com/Sithumpramu/Firefighter-communication-and-management-Sys.git)
   cd Firefighter-communication-and-management-Sys/"RPI unit"
   ```
2. Configure your Google Maps API key and serial port settings in the configuration script.
3. Launch the central monitor application:
   ```bash
   python main.py
   ```

---

## Author

* **Sithum Pramuditha** – [GitHub Profile](https://github.com/Sithumpramu) · [LinkedIn](https://www.linkedin.com/in/sithum-pramuditha/)
```
