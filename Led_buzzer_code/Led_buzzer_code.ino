#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <FirebaseESP32.h>

// WiFi credentials
const char* ssid = "HMI";
const char* password = "12345678";

// Firebase configuration
FirebaseConfig config;
FirebaseAuth auth;
FirebaseData firebaseData;

// LCD setup: I2C address (0x27), 16 columns, 2 rows
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Define LED and Buzzer pins
#define BUZZER_PIN 27  
#define LED_PIN1 25   // Water - White
#define LED_PIN2 26   // Food - Blue
#define LED_PIN3 32   // Medicine - Green
#define LED_PIN4 13   // Emergency - Red
#define LED_PIN5 33   // Sanitation - Yellow (Updated)

void setup() {
  Serial.begin(115200);

  // Initialize LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Starting...");

  // Set pin modes for LEDs and buzzer
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN1, OUTPUT);
  pinMode(LED_PIN2, OUTPUT);
  pinMode(LED_PIN3, OUTPUT);
  pinMode(LED_PIN4, OUTPUT);
  pinMode(LED_PIN5, OUTPUT);

  // Ensure all outputs are initially off
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN1, LOW);
  digitalWrite(LED_PIN2, LOW);
  digitalWrite(LED_PIN3, LOW);
  digitalWrite(LED_PIN4, LOW);
  digitalWrite(LED_PIN5, LOW);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nWiFi Connected ✅");

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WiFi Connected");

  // Set Firebase configuration
  config.host = "hmi1-99e38-default-rtdb.asia-southeast1.firebasedatabase.app";
  config.signer.tokens.legacy_token = "8pI4cyLRZUtMvmOj6qbbs8ta301iSmVis0iQfWDB";

  // Initialize Firebase
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  lcd.clear();
}

void loop() {
  // Read detected gesture from Firebase
  if (Firebase.getString(firebaseData, "/detected_gesture")) {
    if (firebaseData.dataType() == "string") {
      String detectedGesture = firebaseData.stringData();
      Serial.println("Detected Gesture: " + detectedGesture);

      // Turn off all LEDs and buzzer initially
      digitalWrite(BUZZER_PIN, LOW);
      digitalWrite(LED_PIN1, LOW);
      digitalWrite(LED_PIN2, LOW);
      digitalWrite(LED_PIN3, LOW);
      digitalWrite(LED_PIN4, LOW);
      digitalWrite(LED_PIN5, LOW);

      // Display detected gesture on LCD
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("G:" + detectedGesture);

      // Control LEDs and buzzer based on detected gesture
      if (detectedGesture == "Water") {
        
        digitalWrite(LED_PIN4, HIGH);   // Emergency LED (Red)
      } else if (detectedGesture == "Medicine") {
        digitalWrite(LED_PIN5, HIGH);   // Sanitation LED (Yellow)
      } else if (detectedGesture == "Emergency") {
        digitalWrite(LED_PIN2, HIGH);   // Food LED (Blue)
        digitalWrite(BUZZER_PIN, HIGH);
      } else if (detectedGesture == "Sanitation") {
        digitalWrite(LED_PIN1, HIGH); 
          // Water LED (White)
        
        
      } else if (detectedGesture == "Food") {
        digitalWrite(LED_PIN3, HIGH);   // Medicine LED (Green)
      } else {
        Serial.println("Unknown Gesture: " + detectedGesture);
      }
    }
  } else {
    Serial.println("❌ Failed to retrieve data: " + firebaseData.errorReason());
    lcd.setCursor(0, 1);
    lcd.print("Firebase Error");
  }

  delay(1000);  // Check Firebase every second
}

