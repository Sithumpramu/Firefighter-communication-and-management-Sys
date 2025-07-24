#include <DHT.h>
#include <SPI.h>
#include <LoRa.h>
#include <TinyGPS++.h>
#include <ArduinoJson.h>

#define THIS_UNIT_ID 2

// === LoRa Pins ===
#define LORA_SS 10
#define LORA_RST 9
#define LORA_DIO0 2

// === GPS ===
TinyGPSPlus gps;
#define GPS_SERIAL Serial1
float lastValidLat = 0.0;
float lastValidLon = 0.0;

// === DHT Sensor ===
#define DHT_PIN 5
#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);

// === Flame Sensor ===
#define FLAME_DIGITAL_PIN 4
#define FLAME_ANALOG_PIN A0
#define FLAME_ANALOG_THRESHOLD 900 // Threshold to detect flame from analog sensor

// === LED ===
#define LED_PIN 3
#define PANIC_PIN 6

// === Timer and Flags ===
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 5000; // Data sending interval

bool autoBlink = false;
bool manualBlink = false;
unsigned long autoBlinkStart = 0;
unsigned long manualBlinkStart = 0;
int autoBlinkState = LOW;
int manualBlinkState = LOW;
int autoBlinkCount = 0;
int manualBlinkCount = 0;

// Function declaration for sending with acknowledgment
bool sendWithAck(String data, int retries = 3, int timeout = 2000);

void setup() {
  Serial.begin(9600);
  GPS_SERIAL.begin(9600);

  pinMode(PANIC_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  pinMode(FLAME_DIGITAL_PIN, INPUT);
  pinMode(FLAME_ANALOG_PIN, INPUT);
  digitalWrite(LED_PIN, LOW);

  dht.begin();

  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(433E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }

  Serial.println("LoRa Sender/Receiver Ready");
  LoRa.receive();
}

void loop() {
  handleLoRaCommand();   // Listen for incoming LoRa commands
  handleBlinkLogic();    // Process any blinking LED sequences

  // Periodically send sensor data
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();
    sendSensorData();
  }
  // Read GPS data continuously
  while (GPS_SERIAL.available()) {
    gps.encode(GPS_SERIAL.read());
  }
}

void handleLoRaCommand() {
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String incoming = "";
    while (LoRa.available()) incoming += (char)LoRa.read();
    Serial.println("Received command: " + incoming);

    StaticJsonDocument<128> doc;
    if (deserializeJson(doc, incoming) == DeserializationError::Ok) {
      int targetId = doc["id"];
      const char* cmd = doc["command"];
      if (targetId == THIS_UNIT_ID && strcmp(cmd, "blink") == 0) {
        Serial.println("Manual blink triggered!");
        manualBlink = true;
        manualBlinkStart = millis();
        manualBlinkCount = 0;
      }
    } else {
      Serial.println("JSON parse error in command");
    }
  }
}

void sendSensorData() {
  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();
  if (isnan(temp)) { Serial.println("Temp error"); temp = -999; }
  if (isnan(humidity)) { Serial.println("Hum error"); humidity = -999; }

  int flameAnalog = analogRead(FLAME_ANALOG_PIN);
  int flameDigital = digitalRead(FLAME_DIGITAL_PIN);
  int flameDetected = (flameDigital == LOW || flameAnalog < FLAME_ANALOG_THRESHOLD) ? 0 : 1;

// Trigger automatic blinking when serious thresholds exceeded
  if (!manualBlink && (temp > 50 || humidity < 20)) {
    if (!autoBlink) {
      autoBlink = true;
      autoBlinkStart = millis();
      autoBlinkCount = 0;
      Serial.println("Auto blink triggered due to environment!");
    }
  }
  //gps with gps fallback logic
  float lat = gps.location.isValid() ? gps.location.lat() : -37.8476;;
  float lon = gps.location.isValid() ? gps.location.lng() : 145.1140;
  if (gps.location.isValid()) {
    lastValidLat = lat;
    lastValidLon = lon;
  } else {
    Serial.println("GPS fallback to last known location.");
  }
  int panic = digitalRead(PANIC_PIN) == LOW ? 1 : 0;

  // Create JSON-formatted data packet
  String data = "{\"id\":" + String(THIS_UNIT_ID) +
                ",\"temp\":" + String(temp, 1) +
                ",\"humidity\":" + String(humidity) +
                ",\"flame\":" + String(flameDetected) +
                ",\"panic\":" + String(panic) + 
                ",\"lat\":" + String(lat, 6) +
                ",\"lon\":" + String(lon, 6) + "}";

  sendWithAck(data);  //Use ACK retry logic
  LoRa.receive(); //return to recieve mode
}

// === Retry Logic for Sending Data and Waiting for ACK ===
bool sendWithAck(String data, int retries, int timeout) {
  for (int i = 0; i < retries; i++) {
    LoRa.beginPacket();
    LoRa.print(data);
    LoRa.endPacket();
    Serial.println("Sent: " + data);

    unsigned long start = millis();
    while (millis() - start < timeout) {
      int packetSize = LoRa.parsePacket();
      if (packetSize) {
        String response = "";
        while (LoRa.available()) {
          response += (char)LoRa.read();
        }
        Serial.println("ACK check: " + response);
        if (response == "ACK:" + String(THIS_UNIT_ID)) {
          Serial.println("ACK received.");
          return true;
        }
      }
    }

    Serial.println("No ACK. Retrying...");
  }

  Serial.println("Failed after retries.");
  return false;
}

// === LED Blinking Logic ===
void handleBlinkLogic() {
  unsigned long now = millis();

  // Manual blink: fast, 6 blinks
  if (manualBlink) {
    if (now - manualBlinkStart >= 300) {
      manualBlinkState = !manualBlinkState;
      digitalWrite(LED_PIN, manualBlinkState);
      manualBlinkStart = now;
      if (manualBlinkState == LOW) manualBlinkCount++;
      if (manualBlinkCount >= 6) {
        manualBlink = false;
        digitalWrite(LED_PIN, LOW);
      }
    }
  }
 // Auto blink: slow, 1 blink
  if (!manualBlink && autoBlink) {
    if (now - autoBlinkStart >= 600) {
      autoBlinkState = !autoBlinkState;
      digitalWrite(LED_PIN, autoBlinkState);
      autoBlinkStart = now;
      if (autoBlinkState == LOW) autoBlinkCount++;
      if (autoBlinkCount >= 1) {
        autoBlink = false;
        digitalWrite(LED_PIN, LOW);
      }
    }
  }
}
