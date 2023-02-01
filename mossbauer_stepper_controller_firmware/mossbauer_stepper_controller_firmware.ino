
int AW_PIN = 9; //green wire
int CCW_PIN = 10; //white wire
int PLS_PIN = 11; //red wire, is not currently used in code
int RS2_PIN = 12; //blue wire
char serialchar = '\0';

void setup() {
  // put your setup code here, to run once
  Serial.begin(1000000);
  Serial.println("Successful Connection with Motor Controller");
  pinMode(AW_PIN, OUTPUT);
  pinMode(CCW_PIN, OUTPUT);
  pinMode(PLS_PIN, OUTPUT); //not currently used
  pinMode(RS2_PIN, OUTPUT);
}

void loop() {
  if (Serial.available() > 0){
    serialchar = Serial.read();
    if (serialchar == 'a'){
      digitalWrite(RS2_PIN, HIGH);
    }
    if (serialchar == 'b'){
      digitalWrite(RS2_PIN, LOW);
    }
    if (serialchar == 'c'){
      digitalWrite(CCW_PIN, HIGH);
    }
    if (serialchar == 'd'){
      digitalWrite(CCW_PIN, LOW);
    }
    if (serialchar == 'e'){
      digitalWrite(AW_PIN, HIGH);
    }
    if (serialchar == 'f'){
      digitalWrite(AW_PIN, LOW);
    }
    if (serialchar == '?'){
      Serial.println("microcontroller has no answers");
    }
  }

}
