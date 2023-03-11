
int AW_PIN = 9; //green wire
int CCW_PIN = 10; //white wire
int PLS_PIN = 11; //red wire, is not currently used in code
int RS2_PIN = 12; //blue wire
char serialchar = '\0';

int FLAG0_PIN = 2;
int FLAG1_PIN = 3;

int flag0_state = LOW;
int flag1_state = LOW;

void setup() {
  // put your setup code here, to run once
  Serial.begin(1000000);
  Serial.println("Successful Connection with Motor Controller");
  pinMode(AW_PIN, OUTPUT);
  pinMode(CCW_PIN, OUTPUT);
  pinMode(PLS_PIN, OUTPUT); //not currently used
  pinMode(RS2_PIN, OUTPUT);
  pinMode(FLAG0_PIN, INPUT);
  pinMode(FLAG1_PIN, INPUT);
}

void loop() {
  flag0_state = digitalRead(FLAG0_PIN);
  flag1_state = digitalRead(FLAG1_PIN);

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
      if ((flag0_state == LOW) && (flag1_state == LOW)){
        Serial.println("w");
      }
      else if ((flag0_state == HIGH) && (flag1_state == LOW)){
        Serial.println("x");
      }
      else if ((flag0_state == LOW) && (flag1_state == HIGH)){
        Serial.println("y");
      }
      else if ((flag0_state == HIGH) && (flag1_state == HIGH)){
        Serial.println("z");
      }
      else{
        Serial.println("flag read failure");
      }
    }
  }

}
