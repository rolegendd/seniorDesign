/*
 * --------------------------------------------------------------------------------------------------------------------
 * Example sketch/program showing how to read data from a PICC to serial.
 * --------------------------------------------------------------------------------------------------------------------
 * This is a MFRC522 library example; for further details and other examples see: https://github.com/miguelbalboa/rfid
 * 
 * Example sketch/program showing how to read data from a PICC (that is: a RFID Tag or Card) using a MFRC522 based RFID
 * Reader on the Arduino SPI interface.
 * 
 * When the Arduino and the MFRC522 module are connected (see the pin layout below), load this sketch into Arduino IDE
 * then verify/compile and upload it. To see the output: use Tools, Serial Monitor of the IDE (hit Ctrl+Shft+M). When
 * you present a PICC (that is: a RFID Tag or Card) at reading distance of the MFRC522 Reader/PCD, the serial output
 * will show the ID/UID, type and any data blocks it can read. Note: you may see "Timeout in communication" messages
 * when removing the PICC from reading distance too early.
 * 
 * If your reader supports it, this sketch/program will read all the PICCs presented (that is: multiple tag reading).
 * So if you stack two or more PICCs on top of each other and present them to the reader, it will first output all
 * details of the first and then the next PICC. Note that this may take some time as all data blocks are dumped, so
 * keep the PICCs at reading distance until complete.
 * 
 * @license Released into the public domain.
 * 
 * Typical pin layout used:
 * -----------------------------------------------------------------------------------------
 *             MFRC522      Arduino       Arduino   Arduino    Arduino          Arduino
 *             Reader/PCD   Uno/101       Mega      Nano v3    Leonardo/Micro   Pro Micro
 * Signal      Pin          Pin           Pin       Pin        Pin              Pin
 * -----------------------------------------------------------------------------------------
 * RST/Reset   RST          9             5         D9         RESET/ICSP-5     RST
 * SPI SS      SDA(SS)      10            53        D10        10               10
 * SPI MOSI    MOSI         11 / ICSP-4   51        D11        ICSP-4           16
 * SPI MISO    MISO         12 / ICSP-1   50        D12        ICSP-1           14
 * SPI SCK     SCK          13 / ICSP-3   52        D13        ICSP-3           15
 *
 * More pin layouts for other boards can be found here: https://github.com/miguelbalboa/rfid#pin-layout
 */

#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
#include "config.h"

const char* ssid = "hot"; /// Testing hotspot ///
const char* password = "1234"; /// Testing password ///


#define RST_PIN         D0          // Configurable, see typical pin layout above
#define SS_PIN          D8         // Configurable, see typical pin layout above


/// Adafruit IO ///
#define AIO_Sever       "io.adafruit.com"
#define AIO_SEVERPORT   1883
/// Adafruit Account info ///
#define AIO_USERNAME  "SeniorDesignProject3"
#define AIO_KEY       ""

WiFiClient client;
/// MQTT Setup ///
Adafruit_MQTT_Client mqtt(&client, AIO_Sever, AIO_SEVERPORT, AIO_USERNAME, AIO_KEY);
Adafruit_MQTT_Publish Attendance = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/Attendance");


MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance//

/// Represents cards in the system/database /// 
byte accessUID[][4] = {{0X13, 0x9C, 0x34, 0x16},
                       {0xF3, 0xA3, 0x45, 0x1A},
                       {0x24, 0x96, 0x2E, 0x30},
                       //{0x96, 0xB3, 0x2A, 0x30}
                       };

/// The way to get the amount of items in an array in C/C++ in order to use in a loop. ///
const int numOfIds = sizeof(accessUID)/sizeof(accessUID[0]);



void setup() {
	Serial.begin(115200);		// Initialize serial communications with the PC
	while (!Serial);		// Do nothing if no serial port is opened (added for Arduinos based on ATMEGA32U4)
	SPI.begin();			// Init SPI bus
	mfrc522.PCD_Init();		// Init MFRC522
	delay(4);				// Optional delay. Some board do need more time after init to be ready, see Readme
	mfrc522.PCD_DumpVersionToSerial();	// Show details of PCD - MFRC522 Card Reader details
	

  WiFi.begin(ssid,password);

  while(WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }

  Serial.print("NodeMCU IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.println(F("Present card/tag..."));

  /// Connect to the server ///
  connect();


  
}

void loop() {

  /// Ping Server ///

  if(! mqtt.ping(3)){

    // reconnect to sever ///
    if(! mqtt.connected())
      connect();
    
  }

  

	// Reset the loop if no new card present on the sensor/reader. This saves the entire process when idle.
	if ( ! mfrc522.PICC_IsNewCardPresent()) {
		return;
	}

	// Select one of the cards
	if ( ! mfrc522.PICC_ReadCardSerial()) {
		return;
	}

/// This portion of the code checks to see if the RFID is within the system accessUID ///	
   bool accessGranted = false;
   for(int row = 0; row < numOfIds; row++){                   /// Checks by each row ///
    accessGranted = true;                 
    for(byte byte = 0; byte < mfrc522.uid.size; byte++){     /// Checks byte by byte ///
      if(mfrc522.uid.uidByte[byte] != accessUID[row][byte]){ /// If a byte is not correct then it is not in the system, 
        accessGranted = false;                               /// then breaks out of the inner loop. ///
        break;
      }
    }
    if(accessGranted){                                       /// evaluates the status of accessGranted and prints accordingly ///
      Serial.print("ID Detected: "); 
      printIDhex(mfrc522.uid.uidByte, mfrc522.uid.size);
      Serial.println();
      break;
    }
   }
   if(!accessGranted){
    Serial.println("Access Denied");}

  mfrc522.PICC_HaltA();

}

void printIDhex(byte *buffer, byte bufferSize){
  for(byte parse = 0; parse < bufferSize; parse++){
    Serial.print(buffer[parse] < 0x10 ? " 0" : " ");
    Serial.print(buffer[parse], HEX);
  }
}

// connect to adafruit io via MQTT
void connect() {
  Serial.print(F("Connecting to Adafruit IO... "));
  int8_t ret;
  while ((ret = mqtt.connect()) != 0) {
    switch (ret) {
      case 1: Serial.println(F("Wrong protocol")); break;
      case 2: Serial.println(F("ID rejected")); break;
      case 3: Serial.println(F("Server unavail")); break;
      case 4: Serial.println(F("Bad user/pass")); break;
      case 5: Serial.println(F("Not authed")); break;
      case 6: Serial.println(F("Failed to subscribe")); break;
      default: Serial.println(F("Connection failed")); break;
    }

    if(ret >= 0)
      mqtt.disconnect();

    Serial.println(F("Retrying connection..."));
    delay(10000);
  }
  Serial.println(F("Adafruit IO Connected!"));
}