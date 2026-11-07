// Serial node for Arduino (Uno/Nano) AND RP2040 (Raspberry Pi Pico, arduino-pico core).
// Protocol (115200 baud, newline terminated):
//   READ                -> {"a0":123,"a1":456,"uptime_s":12}
//   SET led 1|0         -> OK
//   SET relay 1|0       -> OK
//   SET pwm 0..255      -> OK
// Add your own sensors in handleRead() and outputs in handleSet().

#define RELAY_PIN 7     // change to your wiring
#define PWM_PIN   9     // PWM-capable pin (Uno: 9, Pico: 9 also works)
#define RELAY_ACTIVE_LOW false

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(PWM_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_ACTIVE_LOW ? HIGH : LOW);  // relay off at boot
}

void handleRead() {
  Serial.print("{\"a0\":");        Serial.print(analogRead(A0));
  Serial.print(",\"a1\":");        Serial.print(analogRead(A1));
  Serial.print(",\"uptime_s\":");  Serial.print(millis() / 1000);
  Serial.println("}");
}

void handleSet(const String &name, int value) {
  if (name == "led") {
    digitalWrite(LED_BUILTIN, value ? HIGH : LOW);
  } else if (name == "relay") {
    digitalWrite(RELAY_PIN, (value != 0) != RELAY_ACTIVE_LOW ? HIGH : LOW);
  } else if (name == "pwm") {
    analogWrite(PWM_PIN, constrain(value, 0, 255));
  } else {
    Serial.println("ERR unknown channel");
    return;
  }
  Serial.println("OK");
}

void loop() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line == "READ") {
    handleRead();
  } else if (line.startsWith("SET ")) {
    int sp = line.indexOf(' ', 4);
    if (sp < 0) { Serial.println("ERR usage"); return; }
    handleSet(line.substring(4, sp), line.substring(sp + 1).toInt());
  } else {
    Serial.println("ERR unknown command");
  }
}
