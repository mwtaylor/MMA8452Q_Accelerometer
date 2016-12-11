class SMBus:
    def __init__(self, i2c_device: int):
        print("Created SMBus for i2c device {}".format(i2c_device))

    @staticmethod
    def read_word_data(device_address: int, register: int):
        return 0

    @staticmethod
    def read_byte_data(device_address: int, register: int):
        if register == 0x0D:
            return 0x2A
        elif register == 0x00:
            return 0x09

        return 0

    @staticmethod
    def read_i2c_block_data(device_address: int, first_register: int, number_of_bytes: int):
        if first_register == 0x00 and number_of_bytes == 7:
            return [0x09, 0xFF, 0xF0, 0x00, 0x00, 0x00, 0x00]

        return [0] * number_of_bytes

    @staticmethod
    def write_byte_data(device_address: int, register: int, byte: int):
        print("Write {} at register {} on device {}".format(byte, register, device_address))
