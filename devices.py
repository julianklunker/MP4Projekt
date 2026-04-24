from serial.tools.list_ports import grep

devices = {
        "bot1": "10564870",
        "bot2": "10473660",
        "encoder": "7513131383235160C180"
}

def find_com_ports():
    com_ports = []
    for dev, ser in devices.items():
        ports = grep(ser)
        for port in ports:
            com_ports.append(port.device)
            print(f"Port for {dev} is: {port.device}")
    return tuple(com_ports)
