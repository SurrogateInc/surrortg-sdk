import pigpio


def connected_i2c_addresses():
    """Returns a list of connected i2c addresses as strings

    :raises RuntimeError: if cannot connect to pigpio
    :return: List of i2c addresses
    :rtype: list[string]
    """
    # Connect pigpio
    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("Could not connect to pigpio")

    # Try reading from all addresses
    # append to result if successful
    result = []
    for device in range(128):
        i2c_handle = pi.i2c_open(1, device)
        try:
            pi.i2c_read_byte(i2c_handle)
            result.append(hex(device))
        except pigpio.error:
            pass
        pi.i2c_close(i2c_handle)

    # Disconnect pigpio, return result
    pi.stop()
    return result


def i2c_connected(address):
    """Checks if there is a connected i2c device in some spesific address

    :param address: i2c address as a String, for example '0x29'
    :type address: string
    :return: True/False
    :rtype: bool
    """
    return address in connected_i2c_addresses()


if __name__ == "__main__":
    print(connected_i2c_addresses())
    print(i2c_connected("0x29"))
