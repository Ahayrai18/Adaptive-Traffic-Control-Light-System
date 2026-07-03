#include <WiFi.h>
#include <FirebaseESP32.h>
#include <ArduinoJson.h>

#define WIFI_SSID     "nama_wifi_kamu"
#define WIFI_PASSWORD "password_wifi_kamu"
#define FIREBASE_HOST "atcs-project-default-rtdb.firebaseio.com"
#define FIREBASE_AUTH "web_api_key_kamu"

const int PIN_N[3] = { 4,  2, 15};  
const int PIN_E[3] = {27, 14, 12};  
const int PIN_S[3] = {33, 32, 25};  
const int PIN_W[3] = {19, 18,  5};  

#define IDX_RED    0
#define IDX_YELLOW 1
#define IDX_GREEN  2

FirebaseData   fbdo;
FirebaseConfig fbConfig;
FirebaseAuth   fbAuth;

String lastReceived = "";
unsigned long lastFirebaseUpdate = 0;
String currentState = "N:RED,E:RED,S:RED,W:RED";

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < 3; i++) {
    pinMode(PIN_N[i], OUTPUT);
    pinMode(PIN_E[i], OUTPUT);
    pinMode(PIN_S[i], OUTPUT);
    pinMode(PIN_W[i], OUTPUT);
  }

  setLight(PIN_N, "RED");
  setLight(PIN_E, "RED");
  setLight(PIN_S, "RED");
  setLight(PIN_W, "RED");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected: " + WiFi.localIP().toString());

  fbConfig.host = FIREBASE_HOST;
  fbConfig.signer.tokens.legacy_token = FIREBASE_AUTH;
  Firebase.begin(&fbConfig, &fbAuth);
  Firebase.reconnectWiFi(true);

  Serial.println("ATCS_READY");
}

void loop() {
  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');
    msg.trim();

    if (msg.length() > 0 && msg != lastReceived) {
      lastReceived = msg;
      currentState = msg;
      parseAndApply(msg);
      Serial.println("OK:" + msg);

      uploadToFirebase(msg);
    }
  }

  if (millis() - lastFirebaseUpdate > 5000) {
    lastFirebaseUpdate = millis();
    uploadToFirebase(currentState);
  }
}

void parseAndApply(String data) {
  int start = 0;
  while (start < (int)data.length()) {
    int comma = data.indexOf(',', start);
    String token = (comma == -1) ? data.substring(start) : data.substring(start, comma);

    int colon = token.indexOf(':');
    if (colon > 0) {
      String dir   = token.substring(0, colon);
      String color = token.substring(colon + 1);
      dir.toUpperCase();
      color.toUpperCase();

      if      (dir == "N") setLight(PIN_N, color);
      else if (dir == "E") setLight(PIN_E, color);
      else if (dir == "S") setLight(PIN_S, color);
      else if (dir == "W") setLight(PIN_W, color);
    }

    if (comma == -1) break;
    start = comma + 1;
  }
}

void uploadToFirebase(String stateStr) {
  if (WiFi.status() != WL_CONNECTED) return;

  Firebase.setString(fbdo, "/atcs/raw_state", stateStr);

  String dirs[4] = {"N", "E", "S", "W"};
  String paths[4] = {"/atcs/north/", "/atcs/east/", "/atcs/south/", "/atcs/west/"};

  int start = 0;
  int idx = 0;
  while (start < (int)stateStr.length() && idx < 4) {
    int comma = stateStr.indexOf(',', start);
    String token = (comma == -1) ? stateStr.substring(start) : stateStr.substring(start, comma);

    int colon = token.indexOf(':');
    if (colon > 0) {
      String color = token.substring(colon + 1);
      Firebase.setString(fbdo, paths[idx] + "color", color);
      Firebase.setString(fbdo, paths[idx] + "updated_at",
                         String(millis()));
    }

    if (comma == -1) break;
    start = comma + 1;
    idx++;
  }

  Firebase.setInt(fbdo, "/atcs/timestamp", millis());
}

void setLight(const int pins[3], String color) {
  digitalWrite(pins[IDX_RED],    LOW);
  digitalWrite(pins[IDX_YELLOW], LOW);
  digitalWrite(pins[IDX_GREEN],  LOW);

  if      (color == "RED")    digitalWrite(pins[IDX_RED],    HIGH);
  else if (color == "YELLOW") digitalWrite(pins[IDX_YELLOW], HIGH);
  else if (color == "GREEN")  digitalWrite(pins[IDX_GREEN],  HIGH);
}