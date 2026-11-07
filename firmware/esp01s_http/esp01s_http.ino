// ESP-01S (ESP8266) HTTP node.  GET /read  -> JSON      GET /set?name=relay&value=1 -> OK
// ESP-01S only exposes GPIO0 and GPIO2 (plus TX/RX). Typical ESP-01S relay boards use GPIO0 (active LOW).
// The on-board blue LED is GPIO2 (active LOW). Boot needs GPIO0 and GPIO2 HIGH, so don't hold them LOW at power-up.
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char *WIFI_SSID = "YOUR_WIFI";
const char *WIFI_PASS = "YOUR_PASSWORD";

#define LED_PIN   2
#define RELAY_PIN 0
#define LED_ACTIVE_LOW   true
#define RELAY_ACTIVE_LOW true

ESP8266WebServer server(80);

void handleRead() {
  String j = "{\"rssi\":" + String(WiFi.RSSI()) +
             ",\"free_heap\":" + String(ESP.getFreeHeap()) +
             ",\"uptime_s\":" + String(millis() / 1000) + "}";
  server.send(200, "application/json", j);
}

void handleSet() {
  String name = server.arg("name");
  bool on = server.arg("value").toInt() != 0;
  if (name == "led") {
    digitalWrite(LED_PIN, on != LED_ACTIVE_LOW ? HIGH : LOW);
  } else if (name == "relay") {
    digitalWrite(RELAY_PIN, on != RELAY_ACTIVE_LOW ? HIGH : LOW);
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
  digitalWrite(LED_PIN, LED_ACTIVE_LOW ? HIGH : LOW);
  digitalWrite(RELAY_PIN, RELAY_ACTIVE_LOW ? HIGH : LOW);  // off at boot
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(300); Serial.print("."); }
  Serial.print("\nIP address: "); Serial.println(WiFi.localIP());
  server.on("/read", handleRead);
  server.on("/set", handleSet);
  server.begin();
}

void loop() { server.handleClient(); }
