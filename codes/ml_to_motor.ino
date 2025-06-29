#include <Servo.h>

Servo motor;
char lastCmd = '0';

void setup() {
  Serial.begin(115200);
  motor.attach(9);
  motor.write(90);              // stop
  Serial.println("Servo Ready");
}

void loop() {
  // 1) Read any new command
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '0' || c == '1') {
      lastCmd = c;
    }
  }

  // 2) Continuously enforce it
  if (lastCmd == '1') {
    motor.write(170);           // CW spin (speed ∝ 120–90 = 30)
  } else {
    motor.write(90);            // stop
  }

  delay(20);
}

// const int pwmPin   = 11;   // ZK‑5AD IN3 (PWM)
// const int coastPin = 9;    // ZK‑5AD IN4 (keep LOW for coast)

// char lastCmd = '0';

// void setup() {
//   Serial.begin(115200);
//   pinMode(pwmPin,   OUTPUT);
//   pinMode(coastPin, OUTPUT);

//   // start stopped (coast)
//   digitalWrite(coastPin, LOW);
//   analogWrite(pwmPin, 0);
//   Serial.println("DC Motor Ready");
// }

// void loop() {
//   if (Serial.available() > 0) {
//     char c = Serial.read();
//     if (c == '1' || c == '0') lastCmd = c;
//   }

//   if (lastCmd == '1') {
//     digitalWrite(coastPin, LOW);   // ensure IN4=0 (coast mode)
//     analogWrite(pwmPin, 255);      // full speed
//   } else {
//     analogWrite(pwmPin, 0);        // PWM=0 → stop/coast
//     digitalWrite(coastPin, LOW);   // maintain coast
//   }

//   delay(20);
// }

