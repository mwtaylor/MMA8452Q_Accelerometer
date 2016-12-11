from smbus import SMBus
from datetime import datetime
from enum import Enum


_REGISTER_STATUS = 0x00
_REGISTER_STATUS_FLAG_ANY_AXIS_DATA_OVERWRITTEN = 7
_REGISTER_STATUS_FLAG_Z_AXIS_DATA_OVERWRITTEN = 6
_REGISTER_STATUS_FLAG_Y_AXIS_DATA_OVERWRITTEN = 5
_REGISTER_STATUS_FLAG_X_AXIS_DATA_OVERWRITTEN = 4
_REGISTER_STATUS_FLAG_ANY_AXIS_DATA_READY = 3
_REGISTER_STATUS_FLAG_Z_AXIS_DATA_READY = 2
_REGISTER_STATUS_FLAG_Y_AXIS_DATA_READY = 1
_REGISTER_STATUS_FLAG_X_AXIS_DATA_READY = 0

_REGISTER_X_ACCELERATION = 0x01
_REGISTER_Y_ACCELERATION = 0x03
_REGISTER_Z_ACCELERATION = 0x05

_REGISTER_SYSTEM_MODE = 0x0B
_REGISTER_SYSTEM_MODE_MASK = 0b00000011
_REGISTER_SYSTEM_MODE_VALUE_STANDBY = 0b00
_REGISTER_SYSTEM_MODE_VALUE_WAKE = 0b01
_REGISTER_SYSTEM_MODE_VALUE_SLEEP = 0b10

_REGISTER_WHO_AM_I = 0x0D
_REGISTER_WHO_AM_I_VALUE_EXPECTED = 0x2A

_REGISTER_DATA_CONFIGURATION = 0x0E
_REGISTER_DATA_CONFIGURATION_FLAG_HIGH_PASS_FILTER_ENABLED = 4
_REGISTER_DATA_CONFIGURATION__FULL_SCALE_RANGE_MASK = 0b00000011
_REGISTER_DATA_CONFIGURATION__FULL_SCALE_RANGE_VALUE_2 = 0b00
_REGISTER_DATA_CONFIGURATION__FULL_SCALE_RANGE_VALUE_4 = 0b01
_REGISTER_DATA_CONFIGURATION__FULL_SCALE_RANGE_VALUE_8 = 0b10

_REGISTER_HIGH_PASS_FILTER_CONFIGURATION = 0x0F
_REGISTER_HIGH_PASS_FILTER_CONFIGURATION_FLAG_PULSE_PROCESSING_BYPASS = 5
_REGISTER_HIGH_PASS_FILTER_CONFIGURATION_FLAG_PULSE_PROCESSING_LOW_PASS_ENABLE = 4
_REGISTER_HIGH_PASS_FILTER_CONFIGURATION__HIGH_PASS_CUTOFF_MASK = 0b00000011
_REGISTER_HIGH_PASS_FILTER_CONFIGURATION__HIGH_PASS_CUTOFF_VALUE_HIGHEST = 0b00
_REGISTER_HIGH_PASS_FILTER_CONFIGURATION__HIGH_PASS_CUTOFF_VALUE_HIGH = 0b01
_REGISTER_HIGH_PASS_FILTER_CONFIGURATION__HIGH_PASS_CUTOFF_VALUE_LOW = 0b10
_REGISTER_HIGH_PASS_FILTER_CONFIGURATION__HIGH_PASS_CUTOFF_VALUE_LOWEST = 0b11

_REGISTER_CONTROL_1 = 0x2A
_REGISTER_CONTROL_1__DATA_RATE_MASK = 0b00111000
_REGISTER_CONTROL_1__DATA_RATE_VALUE_800_HZ = 0b000
_REGISTER_CONTROL_1__DATA_RATE_VALUE_400_HZ = 0b001
_REGISTER_CONTROL_1__DATA_RATE_VALUE_200_HZ = 0b010
_REGISTER_CONTROL_1__DATA_RATE_VALUE_100_HZ = 0b011
_REGISTER_CONTROL_1__DATA_RATE_VALUE_50_HZ = 0b100
_REGISTER_CONTROL_1__DATA_RATE_VALUE_12_5_HZ = 0b101
_REGISTER_CONTROL_1__DATA_RATE_VALUE_6_25_HZ = 0b110
_REGISTER_CONTROL_1__DATA_RATE_VALUE_1_56_HZ = 0b111
_REGISTER_CONTROL_1_FLAG_REDUCED_NOISE_MODE = 2
_REGISTER_CONTROL_1_FLAG_FAST_READ_ENABLED = 1
_REGISTER_CONTROL_1_FLAG_ACTIVE = 0

_REGISTER_CONTROL_2 = 0x2B
_REGISTER_CONTROL_2_FLAG_RESET = 6
_REGISTER_CONTROL_2__POWER_SCHEME_VALUE_NORMAL = 0b00
_REGISTER_CONTROL_2__POWER_SCHEME_VALUE_LOW_NOISE_LOW_POWER = 0b01
_REGISTER_CONTROL_2__POWER_SCHEME_VALUE_HIGH_RESOLUTION = 0b10
_REGISTER_CONTROL_2__POWER_SCHEME_VALUE_LOW_POWER = 0b11
_REGISTER_CONTROL_2__POWER_SCHEME__SLEEP_MASK = 0b00011000
_REGISTER_CONTROL_2__POWER_SCHEME__ACTIVE_MASK = 0b00000011
_REGISTER_CONTROL_2_FLAG_AUTO_SLEEP_ENABLE = 2


class AccelerationRange(Enum):
    g2 = (2, _REGISTER_DATA_CONFIGURATION__FULL_SCALE_RANGE_VALUE_2)
    g4 = (4, _REGISTER_DATA_CONFIGURATION__FULL_SCALE_RANGE_VALUE_4)
    g8 = (8, _REGISTER_DATA_CONFIGURATION__FULL_SCALE_RANGE_VALUE_8)

    def __init__(self, acceleration_range: float, register_value: int):
        self._acceleration_range = acceleration_range
        self.register_value = register_value

    def step(self, bits: int):
        return (self._acceleration_range * 2) / (1 << bits)


class DataRate(Enum):
    hz800 = (800, _REGISTER_CONTROL_1__DATA_RATE_VALUE_800_HZ)
    hz400 = (400, _REGISTER_CONTROL_1__DATA_RATE_VALUE_400_HZ)
    hz200 = (200, _REGISTER_CONTROL_1__DATA_RATE_VALUE_200_HZ)
    hz100 = (100, _REGISTER_CONTROL_1__DATA_RATE_VALUE_100_HZ)
    hz50 = (50, _REGISTER_CONTROL_1__DATA_RATE_VALUE_50_HZ)
    hz12_5 = (12.5, _REGISTER_CONTROL_1__DATA_RATE_VALUE_12_5_HZ)
    hz6_25 = (6.25, _REGISTER_CONTROL_1__DATA_RATE_VALUE_6_25_HZ)
    hz1_56 = (1.56, _REGISTER_CONTROL_1__DATA_RATE_VALUE_1_56_HZ)

    def __init__(self, data_rate: float, register_value: int):
        self._data_rate = data_rate
        self.register_value = register_value

    def period(self):
        return 1 / self._data_rate


class AccelerationStatus:
    def __init__(self, overwritten: bool, x: int, y: int, z: int):
        self.overwritten = overwritten
        self.x = x
        self.y = y
        self.z = z


class AccelerometerMMA8452Q:
    def __init__(self, i2c_device: int, i2c_address: int):
        self._address = i2c_address
        self._i2c = SMBus(i2c_device)

        self._range = AccelerationRange.g2
        self._fast_read = False
        self._data_rate = DataRate.hz800

        self._active = False

    def reset(self):
        self._wait_for_reset(datetime.now())
        self._synchronize_configuration_registers()

    def setup(self, acceleration_range: AccelerationRange, fast_read: bool, data_rate: DataRate):
        self._range = acceleration_range
        self._fast_read = fast_read
        self._data_rate = data_rate

        self._set_configuration_registers()

    def setup_and_enable(self, acceleration_range: AccelerationRange, fast_read: bool, data_rate: DataRate):
        self._active = True
        self.setup(acceleration_range, fast_read, data_rate)

    def is_data_ready(self):
        return self._read_flag(_REGISTER_STATUS, _REGISTER_STATUS_FLAG_ANY_AXIS_DATA_READY)

    def read_x_acceleration(self):
        return self._read_acceleration(_REGISTER_X_ACCELERATION)

    def read_y_acceleration(self):
        return self._read_acceleration(_REGISTER_Y_ACCELERATION)

    def read_z_acceleration(self):
        return self._read_acceleration(_REGISTER_Z_ACCELERATION)

    def read_acceleration_and_status(self):
        if self._fast_read:
            [status, x_msb, y_msb, z_msb] = self._read_block(_REGISTER_STATUS, 4)
            x_acc = _convert_8_bit_acceleration(x_msb, self._range)
            y_acc = _convert_8_bit_acceleration(y_msb, self._range)
            z_acc = _convert_8_bit_acceleration(z_msb, self._range)
        else:
            [status, x_msb, x_lsb, y_msb, y_lsb, z_msb, z_lsb] = self._read_block(_REGISTER_STATUS, 7)
            x_acc = _convert_12_bit_acceleration(x_msb, x_lsb >> 4, self._range)
            y_acc = _convert_12_bit_acceleration(y_msb, y_lsb >> 4, self._range)
            z_acc = _convert_12_bit_acceleration(z_msb, z_lsb >> 4, self._range)

        overwritten = _is_flag_set(status, _REGISTER_STATUS_FLAG_ANY_AXIS_DATA_OVERWRITTEN)\

        if _is_flag_set(status, _REGISTER_STATUS_FLAG_X_AXIS_DATA_READY):
            x = x_acc
        else:
            x = None

        if _is_flag_set(status, _REGISTER_STATUS_FLAG_Y_AXIS_DATA_READY):
            y = y_acc
        else:
            y = None

        if _is_flag_set(status, _REGISTER_STATUS_FLAG_Z_AXIS_DATA_READY):
            z = z_acc
        else:
            z = None

        return AccelerationStatus(overwritten, x, y, z)

    def _wait_for_reset(self, reset_time: datetime):
        time_since_reset = datetime.now() - reset_time
        if time_since_reset.seconds > 30:
            raise Exception("Device took too long to reset")

        if self._read_flag(_REGISTER_CONTROL_2, _REGISTER_CONTROL_2_FLAG_RESET):
            self._wait_for_reset(reset_time)
        else:
            return

    def _synchronize_configuration_registers(self):
        data_configuration = self._read_byte(_REGISTER_DATA_CONFIGURATION)
        control1 = self._read_byte(_REGISTER_CONTROL_1)

        self._active = _is_flag_set(control1, _REGISTER_CONTROL_1_FLAG_ACTIVE)

        self._range = _get_value_from_register(data_configuration, _REGISTER_DATA_CONFIGURATION__FULL_SCALE_RANGE_MASK)
        self._fast_read = _is_flag_set(control1, _REGISTER_CONTROL_1_FLAG_FAST_READ_ENABLED)
        self._data_rate = _get_value_from_register(control1, _REGISTER_CONTROL_1__DATA_RATE_MASK)

    def _set_configuration_registers(self):
        data_configuration = 0
        control1 = 0

        if self._active:
            control1 = _set_flag(control1, _REGISTER_CONTROL_1_FLAG_ACTIVE)

        data_configuration = _set_value_in_register(
            data_configuration,
            _REGISTER_DATA_CONFIGURATION__FULL_SCALE_RANGE_MASK,
            self._range.register_value)

        if self._fast_read:
            control1 = _set_flag(control1, _REGISTER_CONTROL_1_FLAG_FAST_READ_ENABLED)

        control1 = _set_value_in_register(control1, _REGISTER_CONTROL_1__DATA_RATE_MASK, self._data_rate.register_value)

        self._write_byte(_REGISTER_DATA_CONFIGURATION, data_configuration)
        self._write_byte(_REGISTER_CONTROL_1, control1)

    def _read_acceleration(self, register: int):
        if self._fast_read:
            return _convert_8_bit_acceleration(self._read_byte(register), self._range)
        else:
            raw_data = self._read_word(register)
            msb = raw_data & 0x00FF
            lsb = raw_data & 0xF000 >> 12
            return _convert_12_bit_acceleration(msb, lsb, self._range)

    def _read_byte(self, register: int):
        return self._i2c.read_byte_data(self._address, register)

    def _read_word(self, register: int):
        return self._i2c.read_word_data(self._address, register)

    def _read_flag(self, register: int, bit_number: int):
        return _is_flag_set(self._read_byte(register), bit_number)

    def _read_block(self, first_register: int, number_of_bytes: int):
        return self._i2c.read_i2c_block_data(self._address, first_register, number_of_bytes)

    def _write_byte(self, register: int, value: int):
        return self._i2c.write_byte_data(self._address, register, value)


def _convert_8_bit_acceleration(msb: int, output_range: AccelerationRange):
    return _convert_to_signed(msb, 8) * output_range.step(8)


def _convert_12_bit_acceleration(msb: int, lsb: int, output_range: AccelerationRange):
    unsigned_acceleration = (msb << 4) + lsb
    return _convert_to_signed(unsigned_acceleration, 12) * output_range.step(12)


def _convert_to_signed(value: int, number_of_bits: int):
    max_value = 1 << number_of_bits
    if value & (max_value >> 1) == 0:
        return value
    else:
        return value - max_value


def _is_flag_clear(register_value: int, bit_number: int):
    mask = 1 << bit_number
    return (register_value & mask) == 0


def _is_flag_set(register_value: int, bit_number: int):
    return not _is_flag_clear(register_value, bit_number)


def _set_flag(original_register_value: int, bit_number: int) -> int:
    return original_register_value | (1 << bit_number)


def _get_value_from_register(register_value: int, mask: int):
    if mask == 0:
        return 0

    bits_to_shift_value = 0

    shifted_mask = mask
    while (shifted_mask & 0x01) == 0:
        shifted_mask >>= 1
        bits_to_shift_value += 1

    return (register_value & mask) >> bits_to_shift_value


def _set_value_in_register(original_register_value: int, mask: int, value: int):
    if mask == 0:
        return original_register_value

    bits_to_shift_value = 0

    shifted_mask = mask
    while (shifted_mask & 0x01) == 0:
        shifted_mask >>= 1
        bits_to_shift_value += 1

    return (original_register_value & ~mask) | ((value << bits_to_shift_value) & mask)
