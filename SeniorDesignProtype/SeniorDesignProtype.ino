// *
//  * --------------------------------------------------------------------------------------------------------------------
//  * Example sketch/program showing how to read data from a PICC to serial.
//  * --------------------------------------------------------------------------------------------------------------------
//  * This is a MFRC522 library example; for further details and other examples see: https://github.com/miguelbalboa/rfid
//  * 
//  * Example sketch/program showing how to read data from a PICC (that is: a RFID Tag or Card) using a MFRC522 based RFID
//  * Reader on the Arduino SPI interface.
//  * 
//  * When the Arduino and the MFRC522 module are connected (see the pin layout below), load this sketch into Arduino IDE
//  * then verify/compile and upload it. To see the output: use Tools, Serial Monitor of the IDE (hit Ctrl+Shft+M). When
//  * you present a PICC (that is: a RFID Tag or Card) at reading distance of the MFRC522 Reader/PCD, the serial output
//  * will show the ID/UID, type and any data blocks it can read. Note: you may see "Timeout in communication" messages
//  * when removing the PICC from reading distance too early.
//  * 
//  * If your reader supports it, this sketch/program will read all the PICCs presented (that is: multiple tag reading).
//  * So if you stack two or more PICCs on top of each other and present them to the reader, it will first output all
//  * details of the first and then the next PICC. Note that this may take some time as all data blocks are dumped, so
//  * keep the PICCs at reading distance until complete.
//  * 
//  * @license Released into the public domain.
//  * 
//  * Typical pin layout used:
//  * -----------------------------------------------------------------------------------------
//  *             MFRC522      Arduino       Arduino   Arduino    Arduino          Arduino
//  *             Reader/PCD   Uno/101       Mega      Nano v3    Leonardo/Micro   Pro Micro
//  * Signal      Pin          Pin           Pin       Pin        Pin              Pin
//  * -----------------------------------------------------------------------------------------
//  * RST/Reset   RST          9             5         D9         RESET/ICSP-5     RST
//  * SPI SS      SDA(SS)      10            53        D10        10               10
//  * SPI MOSI    MOSI         11 / ICSP-4   51        D11        ICSP-4           16
//  * SPI MISO    MISO         12 / ICSP-1   50        D12        ICSP-1           14
//  * SPI SCK     SCK          13 / ICSP-3   52        D13        ICSP-3           15
//  *
//  * More pin layouts for other boards can be found here: https://github.com/miguelbalboa/rfid#pin-layout
//  */

#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include "config.h"
#include "FS.h"
#include <LittleFS.h>
#include <ArduinoJson.h>
//#include <EMailSender.h>
#include <PubSubClient.h>

/// Wifi Details ///
const char* ssid = "Pixel spot";    /// Testing hotspot ///
const char* password = "hola1234";  /// Testing password ///

/// MQTT Broker Connection Details ///
const char* mqtt_server = "3543d9fb30d14c219fc52460abfcbdb5.s1.eu.hivemq.cloud";
const char* mqtt_username = "DesignAdmin";
const char* mqtt_password = "Attendance4321/";
const int mqtt_port = 8883;

/// Secure WiFi Connectivity Initialization ///
WiFiClientSecure espClient;

///  MQTT Client Intitialisation Using WiFi Connection ///
PubSubClient client(espClient);

unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE (50)
char msg[MSG_BUFFER_SIZE];


/// root certificate ///
static const char *root_ca PROGMEM = R"EOF(-----BEGIN CERTIFICATE-----
MIIFCzCCA/OgAwIBAgISBCtYGv7FR2wkunFzzlcW/S0UMA0GCSqGSIb3DQEBCwUA
MDMxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MQwwCgYDVQQD
EwNSMTEwHhcNMjQxMDI0MjM0NDE1WhcNMjUwMTIyMjM0NDE0WjAfMR0wGwYDVQQD
DBQqLnMxLmV1LmhpdmVtcS5jbG91ZDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCC
AQoCggEBAKVuz2sMPmxx2w/f81/YAEKTbNZMJPk2+ooLFg5hxXvReF+AwIT4XvZ+
MLhSKvFxmghJF+BB9WyhqrcJLGDCP4s6SOLWTYixEoTcaLUviqqn+06kYqDJ6E83
NGsc7T42DlPnzqcZZjPRed9rt4CP3RgeZlWyYZgiD8FoJG9gie8ytihF/FkGZT8T
N4Vkl2vQa3mfBWeeKrcuhcLPxqIWDz/30iYfLtEe5JYYScoCKTXcP9SUStjpR8pD
vfOWdvasOAuBy7yBbx01/4lcQt50hfbhTR/K14/D4rNkuuvU7ktSQnoxVXC8YDwG
zkny10DFt65mVYLNZcBQtOLHHOZGV30CAwEAAaOCAiswggInMA4GA1UdDwEB/wQE
AwIFoDAdBgNVHSUEFjAUBggrBgEFBQcDAQYIKwYBBQUHAwIwDAYDVR0TAQH/BAIw
ADAdBgNVHQ4EFgQUgsEjDU35+EWJKBsFxJ0lM0PXMi4wHwYDVR0jBBgwFoAUxc9G
pOr0w8B6bJXELbBeki8m47kwVwYIKwYBBQUHAQEESzBJMCIGCCsGAQUFBzABhhZo
dHRwOi8vcjExLm8ubGVuY3Iub3JnMCMGCCsGAQUFBzAChhdodHRwOi8vcjExLmku
bGVuY3Iub3JnLzAzBgNVHREELDAqghQqLnMxLmV1LmhpdmVtcS5jbG91ZIISczEu
ZXUuaGl2ZW1xLmNsb3VkMBMGA1UdIAQMMAowCAYGZ4EMAQIBMIIBAwYKKwYBBAHW
eQIEAgSB9ASB8QDvAHYAzxFW7tUufK/zh1vZaS6b6RpxZ0qwF+ysAdJbd87MOwgA
AAGSwSAw7AAABAMARzBFAiAwAiRSrhzlH221ZTJtp3j4/+gIDD94ERv5rj/1ibVF
WQIhALrBnoA3Eph3agnYXQDVv6vSFfTzFLk9pNRGMAH5GzkfAHUA5tIxY0B3jMEQ
QQbXcbnOwdJA9paEhvu6hzId/R43jlAAAAGSwSAwzwAABAMARjBEAiBYLoQtnHmj
pXSeGlMficdDWtNEYBrn1FE7y6vlHZlD6QIgZNqsjSiq1jlNbpo7nRHvWdW/hNtr
iUXMkxSOP9f7EMYwDQYJKoZIhvcNAQELBQADggEBADxje/Hu4QNC1MKeSLLDr/Bn
6jrX8sJL0yCTAMBeY644P4e9oJC2aN46ngywLW/I+Kjvv0Tz3k/42ROBJIRNqmxK
GBYoWraNCBksPQewbZLMi1mYhpraLxDzSSNewfxxBm8d6vzJMaGKQNktZNPgmQ+O
vqerlcHEWUVG4uN+LPwd4/f43e2ahkM3FDXBsCVXGDw2kvBgBPjOL4i9l3dm/jNJ
sVR15uXB7eu2NupOhw3WLBlkOeJvfAZtE+7KcBuGPsPJTC5R2CyYx9s+tQl96YDp
wJwYKWUXSk+J/O5T+bvOXxhg1uyXfVB6wrEd+lm6ZAfB577s6CokXkDs0UKc1Wo=
-----END CERTIFICATE-----)EOF";



//const char* dir = "/mydir";
//const char* path = "/myfile.txt";

const int buttonPin = D1;  // the number of the pushbutton pin

//EMailSender emailSend("project3seniordesign@gmail.com", "obtd ftpy lznf jqhg");

//EMailSender::EMailMessage message;

#define RST_PIN D0  // Configurable, see typical pin layout above
#define SS_PIN D8   // Configurable, see typical pin layout above


/// Scanner initiation
MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance//

/// Represents cards in the system/database ///
byte accessUID[][4] = {
  { 0X13, 0x9C, 0x34, 0x16 },
  { 0xF3, 0xA3, 0x45, 0x1A },
  { 0x24, 0x96, 0x2E, 0x30 },
  //{0x96, 0xB3, 0x2A, 0x30}
};

/// The way to get the amount of items in an array in C/C++ in order to use in a loop. ///
const int numOfIds = sizeof(accessUID) / sizeof(accessUID[0]);


void setup() {
  Serial.begin(115200);  // Initialize serial communications with the PC
  WiFi.begin(ssid, password);

  #ifdef ESP8266
    espClient.setInsecure();
  #else
    espClient.setCACert(root_ca); ///   enable this line and the "cert" code for secure connection ///
  #endif

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);


  // Start the file library ///

  // if (LittleFS.begin())
  //   Serial.print("File system is OK. . .");
  // else
  //   Serial.print("File system error. . .");

  // File file = LittleFS.open(path, "w");
  // //EMailSender::EMailMessage message;
  // message.subject = "Attendance 01/01/1970";
  // message.message = "Here is the list of cards scanned today:\r\n";
  // while (!Serial)
  //   ;                                 // Do nothing if no serial port is opened (added for Arduinos based on ATMEGA32U4)
  SPI.begin();                        // Init SPI bus
  mfrc522.PCD_Init();                 // Init MFRC522
  delay(4);                           // Optional delay. Some board do need more time after init to be ready, see Readme
  mfrc522.PCD_DumpVersionToSerial();  // Show details of PCD - MFRC522 Card Reader details

  pinMode(buttonPin, INPUT);



  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.print("NodeMCU IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  mfrc522.PICC_HaltA();
  // if (digitalRead(buttonPin) == 0) {
  //   EMailSender::Response resp = emailSend.send("project3seniordesign@gmail.com", message);

  //   Serial.println("Sending status: ");

  //   Serial.println(resp.status);
  //   Serial.println(resp.code);
  //   Serial.println(resp.desc);
  //   delay(5000);
  // }
/// Checking if client is connected ///
  if(!client.connected()){
    reconnect();
    client.loop();
  }
  


  // Reset the loop if no new card present on the sensor/reader. This saves the entire process when idle.
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
    //
  }

  // Select one of the cards
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  /// This portion of the code checks to see if the RFID is within the system accessUID ///
  bool accessGranted = false;
  for (int row = 0; row < numOfIds; row++) {  /// Checks by each row ///
    accessGranted = true;
    for (byte byte = 0; byte < mfrc522.uid.size; byte++) {      /// Checks byte by byte ///
      if (mfrc522.uid.uidByte[byte] != accessUID[row][byte]) {  /// If a byte is not correct then it is not in the system,
        accessGranted = false;                                  /// then breaks out of the inner loop. ///
        break;
      }
    }

    DynamicJsonDocument doc(1024);

   
    if (accessGranted) {  /// evaluates the status of accessGranted and prints accordingly ///
      Serial.print("ID Detected: ");
      //printIDhex(mfrc522.uid.uidByte, mfrc522.uid.size);
      char bufferString[16];
      sprintf(bufferString, "%02x %02x %02x %02x", mfrc522.uid.uidByte[0], mfrc522.uid.uidByte[1], mfrc522.uid.uidByte[2], mfrc522.uid.uidByte[3]);
      Serial.println(bufferString);
        doc["DeviceID"] = "Prototype";
        doc["Message"] = "ID Detected: ";
        doc["ID"] = bufferString;

        char mqtt_message[128];
      serializeJson(doc, mqtt_message);

       
      publishMessage("esp8266_data", mqtt_message, true);
      //publishMessage("esp8266_data", bufferString, true);

      //message.message += bufferString;

      // Serial.println(mfrc522.uid.uidByte[1]);
      // Serial.println(mfrc522.uid.uidByte[2]);
      // Serial.println(mfrc522.uid.uidByte[3]);
      Serial.println();
      break;
    }
  }
      DynamicJsonDocument doc1(1024);

  if (!accessGranted) {
    String message = "Card Detected, but not in database.";
    Serial.println("Card Detected, but not in database.");
     doc1["DeviceID"] = "Prototype";
     doc1["Message"] = "ID Detected: ";
     doc1["ID"] = message;

        char mqtt_message[128];
    serializeJson(doc1, mqtt_message);
    publishMessage("esp8266_data", mqtt_message, true);
  }

  mfrc522.PICC_HaltA();
}

void printIDhex(byte* buffer, byte bufferSize) {
  for (byte parse = 0; parse < bufferSize; parse++) {
    Serial.print(buffer[parse] < 0x10 ? " 0" : " ");
    Serial.print(buffer[parse], HEX);
  }
}
String getUidString(byte* buffer, byte bufferSize) {
  String uidString = "";
  for (byte i = 0; i < bufferSize; i++) {
    if (buffer[i] < 0x10) {
      uidString += "0";  // Add leading zero for single-digit hex values
    }
    uidString += String(buffer[i], HEX);
  }
  return uidString;
}


void reconnect(){
  /// Loop until we reconnect ///
  while (!client.connected()){
    Serial.println("Attempting MQTT connection. . .");
    String clientID = "ESP8266Client-"; /// Just created a random client ID
    clientID += String(random(0xffff), HEX);

    /// Attempt to connect  ///
    if(client.connect(clientID.c_str(), mqtt_username, mqtt_password)){
      Serial.println("connected. . ."); break;

      client.subscribe(" idk yet ");  /// subscribe to topics here ///
    } else{
      Serial.print("failed, rc= ");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");   /// Adding delay before retrying ///
      delay(5000);
    }
  }
}

/// Call back Method for receiving MQTT messages ///
void callback(char* topic, byte* payload, unsigned int length){
  String incomingMSG = "";
  for(int i = 0; i < length; i++){ incomingMSG += (char)payload[i]; }

  Serial.print("Message received . . . ["+String(topic)+"]"+incomingMSG);
  }

/// Method for Publishing MQTT messages ///
void publishMessage(const char* topic, String payload, boolean retained){
  if(client.publish(topic, payload.c_str(), true)){
    Serial.println("Message published["+String(topic)+"]: "+payload);
  }
}