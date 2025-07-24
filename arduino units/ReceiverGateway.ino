// === Receiver Arduino Sketch (Connected to RPi via Serial) ===
#include <SPI.h>
#include <LoRa.h>
#include <ArduinoJson.h>

// Pin definitions
#define LORA_SS 10
#define LORA_RST 9
#define LORA_DIO0 2

// Buffer for serial commands from RPi
String serialBuffer = "";
bool commandReady = false;

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 5000); // Wait for serial or timeout after 5 seconds
  
  // Setup LoRa
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(433E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  
  Serial.println("LoRa Receiver Ready");
}

void loop() {
  // --- PART 1: Check for LoRa packets from firefighter units ---
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String incoming = "";
    while (LoRa.available()) {
      incoming += (char)LoRa.read();
    }

    Serial.println(incoming); // Forward to RPi

  // === Send ACK back to unit ===
    StaticJsonDocument<128> doc;
    DeserializationError err = deserializeJson(doc, incoming);
    if (!err && doc["id"]) {
      int senderId = doc["id"];
      String ack = "ACK:" + String(senderId);
      LoRa.beginPacket();
      LoRa.print(ack);
      LoRa.endPacket();
      Serial.println("ACK sent to unit " + String(senderId));
    }
  }

  
  // --- PART 2: Check for commands from RPi via Serial ---
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    // Check for end of command (newline)
    if (c == '\n') {
      commandReady = true;
    } else {
      // Add character to buffer
      serialBuffer += c;
    }
  }
  
  // Process command if one is ready
  if (commandReady) {
    processCommand(serialBuffer);
    serialBuffer = ""; // Clear the buffer
    commandReady = false;
  }
}

void processCommand(String command) {
//  Serial.print("Command received from RPi: ");
//  Serial.println(command);

  // Extract the ID from command JSON (basic way)
  int idIndex = command.indexOf("\"id\":");
  int commandIndex = command.indexOf("\"command\"");

  if (idIndex != -1 && commandIndex != -1) {
    int id = command.substring(idIndex + 5).toInt();  // Extract ID value

    // Only forward if ID is valid (e.g., 1 or 2)
    if (id == 1 || id == 2) {
      Serial.println("Forwarding command via LoRa...");

      LoRa.beginPacket();
      LoRa.print(command);  // Send full JSON
      LoRa.endPacket();

      Serial.println("Command forwarded");
    } else {
      Serial.println("Invalid ID in command. Ignoring.");
    }
  } else {
    Serial.println("Malformed command. Ignoring.");
  }
}
