/*
  Semáforo OGT - Servidor HTTP para control de LEDs y rutina
  Compatible con los endpoints usados por httpClient.py:
    - GET /led/{verde|amarillo|rojo}/on
    - GET /led/{verde|amarillo|rojo}/off
    - GET /rutina/{color}/{tiempo}/on   (tiempo en segundos, entero)
    - GET /rutina/off
    - GET /destruction                  (detener rutina y apagar)

  Implementa una rutina no bloqueante con millis():
    Verde encendido por su duración y luego parpadea 3 veces (500ms) como aviso,
    luego Amarillo por su duración, luego Rojo por su duración, y repite.
    Duración 0 salta la fase.
*/

#include <WiFi.h>
#include <WebServer.h>

// Configuración de red Wi-Fi
const char *ssid = "BUAP_Trabajadores";
const char *password = "BuaPW0rk.2017";

// Asignación de pines
#define PIN_LED_VERDE     21
#define PIN_LED_AMARILLO  22
#define PIN_LED_ROJO      23

// Crear un servidor web en el puerto 80
WebServer server(80);

// Estado de rutina
enum Phase { IDLE, GREEN_ON, GREEN_BLINK_ON, GREEN_BLINK_OFF, YELLOW_ON, RED_ON };
volatile bool rutinaActiva = false;
Phase faseActual = IDLE;
uint8_t conteoParpadeo = 0;
unsigned long faseInicioMs = 0;
unsigned long parpadeoInicioMs = 0;

// Duraciones en ms
uint32_t durVerdeMs = 0;
uint32_t durAmarilloMs = 0;
uint32_t durRojoMs = 0;

// Helpers
void allOff() {
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_ROJO, LOW);
}

void setLed(const String &color, bool on) {
  int pin = -1;
  if (color == "verde") pin = PIN_LED_VERDE;
  else if (color == "amarillo") pin = PIN_LED_AMARILLO;
  else if (color == "rojo") pin = PIN_LED_ROJO;
  if (pin != -1) digitalWrite(pin, on ? HIGH : LOW);
}

void startRoutineCycle() {
  // Arranca siempre desde verde
  faseActual = GREEN_ON;
  conteoParpadeo = 0;
  faseInicioMs = millis();
  parpadeoInicioMs = 0;
  // Estado inicial
  allOff();
  if (durVerdeMs > 0) {
    digitalWrite(PIN_LED_VERDE, HIGH);
  } else {
    // Saltar a amarillo si verde es 0
    faseActual = YELLOW_ON;
    faseInicioMs = millis();
    allOff();
    if (durAmarilloMs > 0) {
      digitalWrite(PIN_LED_AMARILLO, HIGH);
    } else {
      // Saltar a rojo si amarillo también es 0
      faseActual = RED_ON;
      faseInicioMs = millis();
      allOff();
      if (durRojoMs > 0) {
        digitalWrite(PIN_LED_ROJO, HIGH);
      } else {
        // Todo 0: no hacer nada visible
        faseActual = IDLE;
      }
    }
  }
}

void stopRoutine() {
  rutinaActiva = false;
  faseActual = IDLE;
  conteoParpadeo = 0;
  allOff();
}

void updateRoutine() {
  if (!rutinaActiva) return;
  unsigned long now = millis();

  switch (faseActual) {
    case GREEN_ON:
      if (durVerdeMs == 0) {
        // salto directo
        faseActual = YELLOW_ON;
        faseInicioMs = now;
        allOff();
        if (durAmarilloMs > 0) digitalWrite(PIN_LED_AMARILLO, HIGH);
        else { faseActual = RED_ON; faseInicioMs = now; if (durRojoMs > 0) { allOff(); digitalWrite(PIN_LED_ROJO, HIGH);} else { faseActual = IDLE; }}
        break;
      }
      if (now - faseInicioMs >= durVerdeMs) {
        // empezar parpadeo 3 veces
        conteoParpadeo = 0;
        parpadeoInicioMs = now;
        digitalWrite(PIN_LED_VERDE, HIGH);
        faseActual = GREEN_BLINK_ON;
      }
      break;

    case GREEN_BLINK_ON:
      if (now - parpadeoInicioMs >= 500) {
        digitalWrite(PIN_LED_VERDE, LOW);
        parpadeoInicioMs = now;
        faseActual = GREEN_BLINK_OFF;
      }
      break;

    case GREEN_BLINK_OFF:
      if (now - parpadeoInicioMs >= 500) {
        conteoParpadeo++;
        if (conteoParpadeo >= 3) {
          // avanzar a amarillo
          allOff();
          faseActual = YELLOW_ON;
          faseInicioMs = now;
          if (durAmarilloMs > 0) {
            digitalWrite(PIN_LED_AMARILLO, HIGH);
          } else {
            // saltar a rojo
            faseActual = RED_ON;
            faseInicioMs = now;
            if (durRojoMs > 0) {
              allOff();
              digitalWrite(PIN_LED_ROJO, HIGH);
            } else {
              // reiniciar ciclo si todo es 0
              startRoutineCycle();
            }
          }
        } else {
          // siguiente ciclo de parpadeo
          digitalWrite(PIN_LED_VERDE, HIGH);
          parpadeoInicioMs = now;
          faseActual = GREEN_BLINK_ON;
        }
      }
      break;

    case YELLOW_ON:
      if (durAmarilloMs == 0) {
        // saltar a rojo
        allOff();
        faseActual = RED_ON;
        faseInicioMs = now;
        if (durRojoMs > 0) digitalWrite(PIN_LED_ROJO, HIGH);
        else startRoutineCycle();
        break;
      }
      if (now - faseInicioMs >= durAmarilloMs) {
        allOff();
        faseActual = RED_ON;
        faseInicioMs = now;
        if (durRojoMs > 0) digitalWrite(PIN_LED_ROJO, HIGH);
        else startRoutineCycle();
      }
      break;

    case RED_ON:
      if (durRojoMs == 0) {
        startRoutineCycle();
        break;
      }
      if (now - faseInicioMs >= durRojoMs) {
        startRoutineCycle();
      }
      break;

    case IDLE:
    default:
      // nada
      break;
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_LED_AMARILLO, OUTPUT);
  pinMode(PIN_LED_ROJO, OUTPUT);
  allOff();

  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("¡Conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // LED endpoints (inlined)
  server.on("/", HTTP_GET, [](){
    String msg = "SemaforoOGT OK\n";
    msg += "IP: "; msg += WiFi.localIP().toString(); msg += "\n";
    server.send(200, "text/plain", msg);
  });

  server.on("/led/verde/on", HTTP_GET, [](){ setLed("verde", true); server.send(200, "text/plain", "LED verde Encendido"); });
  server.on("/led/verde/off", HTTP_GET, [](){ setLed("verde", false); server.send(200, "text/plain", "LED verde Apagado"); });
  server.on("/led/amarillo/on", HTTP_GET, [](){ setLed("amarillo", true); server.send(200, "text/plain", "LED amarillo Encendido"); });
  server.on("/led/amarillo/off", HTTP_GET, [](){ setLed("amarillo", false); server.send(200, "text/plain", "LED amarillo Apagado"); });
  server.on("/led/rojo/on", HTTP_GET, [](){ setLed("rojo", true); server.send(200, "text/plain", "LED rojo Encendido"); });
  server.on("/led/rojo/off", HTTP_GET, [](){ setLed("rojo", false); server.send(200, "text/plain", "LED rojo Apagado"); });

  // Rutina stop (inline)
  server.on("/rutina/off", HTTP_GET, [](){
    stopRoutine();
    server.send(200, "text/plain", "Rutina detenida");
  });

  // Dinámicos y otros
  server.onNotFound([](){
    String uri = server.uri();
    // /rutina/{color}/{tiempo}/on
    if (uri.startsWith("/rutina/")) {
      int start = 8; // después de '/rutina/'
      int idx1 = uri.indexOf('/', start);
      if (idx1 > 0) {
        String color = uri.substring(start, idx1);
        int idx2 = uri.indexOf('/', idx1 + 1);
        if (idx2 > 0) {
          String tiempoStr = uri.substring(idx1 + 1, idx2);
          String accion = uri.substring(idx2 + 1);
          if (accion == "on" && (color == "verde" || color == "amarillo" || color == "rojo")) {
            int tiempo = tiempoStr.toInt();
            if (tiempo < 0) tiempo = 0;
            uint32_t ms = (uint32_t)tiempo * 1000UL;
            if (color == "verde") durVerdeMs = ms;
            else if (color == "amarillo") durAmarilloMs = ms;
            else if (color == "rojo") durRojoMs = ms;
            rutinaActiva = true;
            startRoutineCycle();
            server.send(200, "text/plain", "Rutina set: " + color + "=" + String(tiempo) + "s");
            return;
          }
        }
      }
    }
    if (uri == "/destruction") {
      stopRoutine();
      allOff();
      server.send(200, "text/plain", "All off");
      return;
    }
    server.send(404, "text/plain", "Not Found");
  });

  server.begin();
  Serial.println("Servidor HTTP iniciado");
}

void loop() {
  server.handleClient();
  updateRoutine();
}
