import gc
import time

from utils.mfrc522_big import MFRC522
gc.collect()


MIFAREReader = MFRC522()

# loop keeps checking for cards and tags. If one is near it will catch the UID and authenticate it
while True:
    # Scan for cards
    (status, TagType) = MIFAREReader.MFRC522_Request(0x26)
    # If a card is found
    if status == MIFAREReader.MI_OK:
        print("NFC card detected")

    # Get the UID of the card
    (status, uid) = MIFAREReader.MFRC522_Anticoll()

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:
        print("Card read UID: " + str(hex(uid[0])) + "," + str(hex(uid[1])) + "," + str(hex(uid[2])) + "," + str(
            hex(uid[3])))

        # This is the default key for authentication
        key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        # Select the scanned tag
        MIFAREReader.MFRC522_SelectTag(uid)
        # Dump the data
        MIFAREReader.MFRC522_DumpClassic1K(key, uid)
        # Stop
        MIFAREReader.MFRC522_StopCrypto1()

    time.sleep_ms(1000)
