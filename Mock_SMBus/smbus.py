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
        else:
            return 0

    @staticmethod
    def write_byte_data(device_address: int, register: int, byte: int):
        print("Write {} at register {} on device {}".format(byte, register, device_address))
