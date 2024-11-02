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

#define RST_PIN         D0          // Configurable, see typical pin layout above
#define SS_PIN          D8         // Configurable, see typical pin layout above





MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance
byte accessUID[][4] = {{0X13, 0x9C, 0x34, 0x16},
                       {0xF3, 0xA3, 0x45, 0x1A},
                       {0x24, 0x96, 0x2E, 0x30},
                       //{0x96, 0xB3, 0x2A, 0x30}
                       };
const int numOfIds = sizeof(accessUID)/sizeof(accessUID[0]);



void setup() {
	Serial.begin(9600);		// Initialize serial communications with the PC
	while (!Serial);		// Do nothing if no serial port is opened (added for Arduinos based on ATMEGA32U4)
	SPI.begin();			// Init SPI bus
	mfrc522.PCD_Init();		// Init MFRC522
	delay(4);				// Optional delay. Some board do need more time after init to be ready, see Readme
	mfrc522.PCD_DumpVersionToSerial();	// Show details of PCD - MFRC522 Card Reader details
	Serial.println(F("Scan PICC to see UID, SAK, type, and data blocks..."));
}

void loop() {
	// Reset the loop if no new card present on the sensor/reader. This saves the entire process when idle.
	if ( ! mfrc522.PICC_IsNewCardPresent()) {
		return;
	}

	// Select one of the cards
	if ( ! mfrc522.PICC_ReadCardSerial()) {
		return;
	}

	// Dump debug info about the card; PICC_HaltA() is automatically called
 //  if(mfrc522.uid.uidByte[0] == accessUID[][0] && mfrc522.uid.uidByte[][1] == accessUID[][1] && mfrc522.uid.uidByte[][2] == accessUID[][2] && mfrc522.uid.uidByte[][3] == accessUID[][3]){
// if(inDataBase(mfrc522.uid.uidByte, mfrc522.uid.size)){
//        Serial.println("Access Granted");
//    } else{
//       Serial.println("Access Denied");
//    }
   bool accessGranted = false;
   for(int row = 0; row < numOfIds; row++){
    accessGranted = true;
    for(byte byte = 0; byte < mfrc522.uid.size; byte++){
      if(mfrc522.uid.uidByte[byte] != accessUID[row][byte]){
        accessGranted = false;
        break;
      }
    }
    if(accessGranted){
      Serial.println("Access Granted"); break;
    }
   }
   if(!accessGranted){
    Serial.println("Access Denied");}

  mfrc522.PICC_HaltA();

}

//bool inDataBase(byte *uid, byte uidSize){
 // for (int parser = 0; parser < numOfIds; parser++){
   // bool match = true;
    //for(byte parser2 = 0; parser2 < uidSize; parser2){
      //match = false;
      //break;
    //}
    //if(match){
      //return true;
    //}
  //}
  //return false;
//}
