const int PIN_N[3] = { 4,   2,  15};  // Utara
const int PIN_E[3] = {27,  14,  12};  // Timur
const int PIN_S[3] = {33,  32,  25};  // Selatan
const int PIN_W[3] = {19,  18,   5};  // Barat

#define IDX_RED    0
#define IDX_YELLOW 1
#define IDX_GREEN  2


String lastReceived = "";

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
  Serial.println("ATCS_READY");
}

void loop() {

  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');
    msg.trim();

    if (msg.length() > 0 && msg != lastReceived) {
      lastReceived = msg;
      parseAndApply(msg);
      Serial.println("OK:" + msg);
    }
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

void setLight(const int pins[3], String color) {
  digitalWrite(pins[IDX_RED],    LOW);
  digitalWrite(pins[IDX_YELLOW], LOW);
  digitalWrite(pins[IDX_GREEN],  LOW);

  if      (color == "RED")    digitalWrite(pins[IDX_RED],    HIGH);
  else if (color == "YELLOW") digitalWrite(pins[IDX_YELLOW], HIGH);
  else if (color == "GREEN")  digitalWrite(pins[IDX_GREEN],  HIGH);
}
