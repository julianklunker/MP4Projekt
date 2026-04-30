from serial.tools.list_ports import grep
from serial.tools import list_ports

devices = {
        "bot1": "10564870",
        "bot2": "10473490",
        "encoder": "7513131383235160C180"
}

def find_com_ports():
    #print all available com ports and their info
    print("Available COM ports:")
    for port in list_ports.comports():
        print(f"  {port.device}: {port.description}, sn={port.serial_number}, vid={port.vid}, pid={port.pid}")

    com_ports = {}
    for dev, ser in devices.items():
        ports = grep(ser)
        for port in ports:
            com_ports.update({dev:port.device})
            print(f"Port for {dev} is: {port.device}")
    return com_ports
