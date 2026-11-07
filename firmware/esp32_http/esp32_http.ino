// ESP32 HTTP node.  GET /read  -> JSON sensors     GET /set?name=led&value=1  -> OK
#include <WiFi.h>
#include <WebServer.h>

const char *WIFI_SSID = "YOUR_WIFI";
const char *WIFI_PASS = "YOUR_PASSWORD";

#define LED_PIN   2
#define RELAY_PIN 26
#define RELAY_ACTIVE_LOW false

WebServer server(80);

void handleRead() {
  String j = "{\"chip_temp_c\":" + String(temperatureRead(), 1) +
             ",\"adc34\":" + String(analogRead(34)) +
             ",\"rssi\":" + String(WiFi.RSSI()) +
             ",\"uptime_s\":" + String(millis() / 1000) + "}";
  server.send(200, "application/json", j);
}

void handleSet() {
  String name = server.arg("name");
  int value = server.arg("value").toInt();
  if (name == "led") {
    digitalWrite(LED_PIN, value ? HIGH : LOW);
  } else if (name == "relay") {
    digitalWrite(RELAY_PIN, (value != 0) != RELAY_ACTIVE_LOW ? HIGH : LOW);
  } else {
    server.send(400, "text/plain", "ERR unknown channel");
    return;
  }
  server.send(200, "text/plain", "OK");
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_ACTIVE_LOW ? HIGH : LOW);  // off at boot
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(300); Serial.print("."); }
  Serial.print("\nIP address: "); Serial.println(WiFi.localIP());  // put this in config.yaml
  server.on("/read", handleRead);
  server.on("/set", handleSet);
  server.begin();
}

void loop() { server.handleClient(); }
