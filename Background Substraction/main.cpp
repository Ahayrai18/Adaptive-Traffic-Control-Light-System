#include <Arduino.h>
#include <WiFi.h>
#include <Firebase_ESP_Client.h>

// Firebase configuration
#define FIREBASE_HOST ""
#define FIREBASE_AUTH ""

// WiFi configuration
#define WIFI_SSID "Wokwi-GUEST"
#define WIFI_PASSWORD ""

// Array to store traffic density for each street
int streets[4];

// Firebase objects
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

// Timing constant for data updates (in milliseconds)
const unsigned long UPDATE_INTERVAL = 1000; // 1 second
unsigned long lastUpdate = 0;

void setup()
{
  // Initialize serial communication
  Serial.begin(115200);

  // Connect to WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(300);
  }
  Serial.println();
  Serial.print("Connected with IP: ");
  Serial.println(WiFi.localIP());

  // Configure Firebase
  config.host = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;

  // Initialize Firebase
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  fbdo.setResponseSize(4096); // Set buffer size for response

  Serial.println("------------------------------------");
  Serial.println("Connected to Firebase");
}

void updateTrafficData()
{
  for (int i = 0; i < 4; i++)
  {
    String path = "/Gaza/crossroads/Saraia/" + String(i);
    if (Firebase.RTDB.getInt(&fbdo, path))
    {
      if (fbdo.dataType() == "int")
      {
        streets[i] = fbdo.intData();
        Serial.print("Street ");
        Serial.print(i);
        Serial.print(": ");
        Serial.println(streets[i]);
      }
      else
      {
        Serial.print("Error: Data at ");
        Serial.print(path);
        Serial.println(" is not an integer");
      }
    }
    else
    {
      Serial.print("Error reading street ");
      Serial.print(i);
      Serial.print(": ");
      Serial.println(fbdo.errorReason());
    }
  }
  Serial.println("------------------------------------");
}

void loop()
{
  unsigned long currentTime = millis();

  // Update traffic data periodically
  if (currentTime - lastUpdate >= UPDATE_INTERVAL)
  {
    updateTrafficData();
    lastUpdate = currentTime;
  }
}