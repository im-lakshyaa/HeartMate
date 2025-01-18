import asyncio
from bleak import BleakClient, BleakScanner
from datetime import datetime
import struct

# Replace this with the address of your BLE device
device_address = "7E:7D:A3:FC:06:C9"

# UUIDs for your characteristics
bpm_characteristic_uuid = "2A2A"  # Replace with your actual BPM characteristic UUID
spo2_characteristic_uuid = "2A2C"  # Replace with your actual SpO2 characteristic UUID
emergency_characteristic_uuid = "2A2D"  # Replace with your actual emergency characteristic UUID
time_characteristic_uuid = "2A2B"  # Replace with your actual time characteristic UUID
confirm_characteristic_uuid = "2A59"  # Replace with your actual confirmation characteristic UUID
temp_characteristic_uuid = "2A6E"  # Replace with your actual temperature characteristic UUID
battery_percentage_characteristic_uuid = "2A19"  # Replace with your actual battery percentage characteristic UUID
max_ir_characteristic_uuid = "2A2E"  # Replace with your actual Max IR characteristic UUID
min_ir_characteristic_uuid = "2A2F"  # Replace with your actual Min IR characteristic UUID

# Variables to store Max and Min IR values
stored_max_ir = 0.0
stored_min_ir = 0.0

async def send_time(client):
    """Send the current time to the BLE device."""
    current_time = datetime.now().strftime("%H:%M:%S")  # Get current time in HH:MM:SS format
    time_bytes = current_time.encode()  # Convert time to bytes for BLE transmission
    await client.write_gatt_char(time_characteristic_uuid, time_bytes)
    print("Sent time:", current_time)

async def send_max_min_ir(client):
    """Send the stored Max and Min IR values to the BLE device."""
    await client.write_gatt_char(max_ir_characteristic_uuid, struct.pack('f', stored_max_ir))
    await client.write_gatt_char(min_ir_characteristic_uuid, struct.pack('f', stored_min_ir))
    print("Sent Max IR:", stored_max_ir)
    print("Sent Min IR:", stored_min_ir)

async def handle_notifications(client):
    """Handle notifications from the BLE device."""
    while True:
        try:
            # Wait for notifications
            await asyncio.sleep(1)  # Adjust as necessary
        except Exception as e:
            print("Error in notification handling:", e)

async def connect_and_receive(device):
    """Handle connection to the BLE device and manage notifications."""
    global stored_max_ir, stored_min_ir  # Use global variables to store Max and Min IR values
    while True:  # Keep trying to connect
        try:
            async with BleakClient(device) as client:
                print("Connected to device.")
                
                # Wait for service discovery
                await client.get_services()
                print("Services discovered.")

                # Start handling notifications
                asyncio.create_task(handle_notifications(client))

                while True:
                    # Read BPM
                    bpm = await client.read_gatt_char(bpm_characteristic_uuid)
                    bpm_value = struct.unpack('f', bpm)[0]  # Assuming BPM is sent as a float
                    print("BPM received:", bpm_value)

                    # Read SpO2
                    spo2 = await client.read_gatt_char(spo2_characteristic_uuid)
                    spo2_value = struct.unpack('f', spo2)[0]  # Assuming SpO2 is sent as a float
                    print("SpO2 received:", spo2_value)

                    # Read emergency status
                    emergency = await client.read_gatt_char(emergency_characteristic_uuid)
                    emergency_value = struct.unpack('B', emergency)[0]  # Assuming emergency is sent as a byte
                    print("Emergency status received:", emergency_value)

                    # Read temperature
                    temperature = await client.read_gatt_char(temp_characteristic_uuid)
                    temperature_value = struct.unpack('f', temperature)[0]  # Assuming temperature is sent as a float
                    print("Temperature received:", temperature_value)

                    # Read battery percentage
                    battery_percentage = await client.read_gatt_char(battery_percentage_characteristic_uuid)
                    print("Raw battery percentage data:", battery_percentage)  # Debugging line
                    if len(battery_percentage) == 4:
                        battery_percentage_value = struct.unpack('I', battery_percentage)[0]  # Assuming battery percentage is sent as a 32-bit integer
                        print("Battery Percentage received:", battery_percentage_value)
                    else:
                        print("Unexpected battery percentage data length:", len(battery_percentage))

                    # Read Max IR
                    max_ir = await client.read_gatt_char(max_ir_characteristic_uuid)
                    stored_max_ir = struct.unpack('f', max_ir)[0]  # Assuming Max IR is sent as a float
                    print("Max IR received:", stored_max_ir)

                    # Read Min IR
                    min_ir = await client.read_gatt_char(min_ir_characteristic_uuid)
                    stored_min_ir = struct.unpack('f', min_ir)[0]  # Assuming Min IR is sent as a float
                    print("Min IR received:", stored_min_ir)

                    # Send time and consent message
                    await send_time(client)
                    consent_message = struct.pack('B', 1)  # Assuming consent is sent as a byte
                    await client.write_gatt_char(confirm_characteristic_uuid, consent_message)

                    await asyncio.sleep(1)  # Adjust as necessary to control the polling rate

        except Exception as e:
            print("Connection lost or error occurred:", e)
            print("Attempting to reconnect...")
            await asyncio.sleep(2)  # Wait before trying to reconnect

async def find_device():
    """Scan for the BLE device by address."""
    print("Searching for devices...")
    devices = await BleakScanner.discover()
    for device in devices:
        if device.address == device_address:
            print(f"Found device: {device.name} ({device.address})")
            return device
    print("Device not found.")
    return None

async def main():
    """Main loop to keep finding and connecting to the BLE device."""
    while True:
        device = await find_device()
        if device:
            await connect_and_receive(device)
            # Send stored Max and Min IR values on reconnect
            async with BleakClient(device) as client:
                await send_max_min_ir(client)
        else:
            print("Retrying device discovery...")
            await asyncio.sleep(5)  # Wait before retrying device discovery

if __name__ == "__main__":
    asyncio.run(main())   