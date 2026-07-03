const uint8_t PIN_RED[4]    = { 4,  27, 33, 19 };  
const uint8_t PIN_YELLOW[4] = { 2,  14, 32, 18 };  
const uint8_t PIN_GREEN[4]  = { 15, 12, 25,  5 };  

const unsigned long YELLOW_DUR    = 2500;   
const unsigned long CLEARANCE_DUR = 2000;   
const unsigned long SKIP_DUR      = 600;    
const unsigned long STARVATION_CAP = 60000; 

enum PhaseState { GREEN, YELLOW, CLEARANCE, SKIP };
PhaseState phaseState = CLEARANCE;
int phaseDir = 0;
unsigned long phaseTimer    = 0;
unsigned long phaseMaxTimer = 1;
unsigned long lastTick      = 0;

int counts[4] = {0, 0, 0, 0};           
unsigned long waitTime[4]    = {0,0,0,0};
unsigned long firstNonZero[4]= {0,0,0,0};
String inputBuffer = "";

unsigned long getGreenDuration(int c) {
  if (c == 0) return 0;
  if (c <= 2) return 5000;
  if (c <= 5) return 10000;
  if (c <= 9) return 15000;
  return 20000;
}

void setAllRed() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(PIN_RED[i],    HIGH);
    digitalWrite(PIN_YELLOW[i], LOW);
    digitalWrite(PIN_GREEN[i],  LOW);
  }
}

int pickNextDir() {
  int maxVal = 0;
  for (int i = 0; i < 4; i++) if (counts[i] > maxVal) maxVal = counts[i];

  int cand[4]; int nc = 0;
  for (int i = 0; i < 4; i++) if (counts[i] == maxVal) cand[nc++] = i;
  if (nc == 1) return cand[0];

  int bestIdx = -1;
  unsigned long bestTs = 0;
  for (int k = 0; k < nc; k++) {
    int i = cand[k];
    if (firstNonZero[i] > 0) {
      if (bestIdx == -1 || firstNonZero[i] < bestTs) {
        bestTs = firstNonZero[i];
        bestIdx = i;
      }
    }
  }
  if (bestIdx != -1) return bestIdx;

  bestIdx = cand[0];
  for (int k = 1; k < nc; k++) {
    if (waitTime[cand[k]] > waitTime[bestIdx]) bestIdx = cand[k];
  }
  return bestIdx;
}

void initPhase() {
  setAllRed();
  phaseDir = pickNextDir();
  waitTime[phaseDir]     = 0;
  firstNonZero[phaseDir] = 0;

  unsigned long dur = getGreenDuration(counts[phaseDir]);

  if (dur == 0) {
    phaseState    = SKIP;
    phaseTimer    = SKIP_DUR;
    phaseMaxTimer = SKIP_DUR;
  } else {
    phaseState    = GREEN;
    phaseTimer    = dur;
    phaseMaxTimer = dur;
    digitalWrite(PIN_RED[phaseDir],   LOW);
    digitalWrite(PIN_GREEN[phaseDir], HIGH);
  }

  Serial.print("PHASE ");
  Serial.print("NESW"[phaseDir]);
  Serial.print(" ");
  Serial.print(phaseState == GREEN ? "GREEN" : "SKIP");
  Serial.print(" dur="); Serial.print(phaseTimer);
  Serial.print(" cnt="); Serial.println(counts[phaseDir]);
}

void tickPhase(unsigned long dt) {
  phaseTimer = (phaseTimer > dt) ? phaseTimer - dt : 0;

  for (int i = 0; i < 4; i++) {
    bool isActive = (i == phaseDir && phaseState == GREEN);
    if (!isActive) {
      waitTime[i] += dt;
      if (waitTime[i] > STARVATION_CAP) waitTime[i] = STARVATION_CAP;
    }
    if (counts[i] > 0) {
      if (firstNonZero[i] == 0) firstNonZero[i] = millis();
    } else {
      firstNonZero[i] = 0;
    }
  }

  if (phaseTimer > 0) return;  

  switch (phaseState) {
    case SKIP:
      initPhase();
      break;

    case GREEN:
      digitalWrite(PIN_GREEN[phaseDir],  LOW);
      digitalWrite(PIN_YELLOW[phaseDir], HIGH);
      phaseState    = YELLOW;
      phaseTimer    = YELLOW_DUR;
      phaseMaxTimer = YELLOW_DUR;
      Serial.print("PHASE "); Serial.print("NESW"[phaseDir]);
      Serial.println(" YELLOW");
      break;

    case YELLOW:
      digitalWrite(PIN_YELLOW[phaseDir], LOW);
      digitalWrite(PIN_RED[phaseDir],    HIGH);
      phaseState    = CLEARANCE;
      phaseTimer    = CLEARANCE_DUR;
      phaseMaxTimer = CLEARANCE_DUR;
      Serial.println("PHASE ALL CLEARANCE");
      break;

    case CLEARANCE:
      initPhase();
      break;
  }
}

void parseCounts(const String& line) {
  const char dirs[4] = {'N','E','S','W'};
  for (int i = 0; i < 4; i++) {
    int idx = line.indexOf(dirs[i]);
    if (idx >= 0 && idx + 1 < (int)line.length()) {
      int val = line.substring(idx + 1).toInt();
      if (val >= 0 && val <= 14) counts[i] = val; 
    }
  }
}

void reportStatus() {
  static unsigned long lastReport = 0;
  unsigned long now = millis();
  if (now - lastReport < 300) return;
  lastReport = now;

  const char* stateStr =
    phaseState == GREEN     ? "GREEN"     :
    phaseState == YELLOW    ? "YELLOW"    :
    phaseState == CLEARANCE ? "CLEARANCE" : "SKIP";

  Serial.print("STATE ");
  Serial.print("NESW"[phaseDir]); Serial.print(" ");
  Serial.print(stateStr);
  Serial.print(" rem="); Serial.print(phaseTimer);
  Serial.print(" cnt="); Serial.print(counts[phaseDir]);
  Serial.print(" N="); Serial.print(counts[0]);
  Serial.print(" E="); Serial.print(counts[1]);
  Serial.print(" S="); Serial.print(counts[2]);
  Serial.print(" W="); Serial.println(counts[3]);
}

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < 4; i++) {
    pinMode(PIN_RED[i],    OUTPUT);
    pinMode(PIN_YELLOW[i], OUTPUT);
    pinMode(PIN_GREEN[i],  OUTPUT);
  }

  setAllRed();
  delay(500);  

  Serial.println("ATCS READY");
  lastTick = millis();
  initPhase();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (inputBuffer.length() > 0) {
        parseCounts(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
    }
  }

  unsigned long now = millis();
  unsigned long dt  = now - lastTick;
  lastTick = now;
  tickPhase(dt);

  reportStatus();
}