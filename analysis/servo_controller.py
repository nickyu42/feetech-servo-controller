import time
from machine import Pin, PWM, SPI

cs = Pin(5, mode=Pin.OUT, value=1)
spi = SPI(0, baudrate=1_000_000, sck=Pin(6), mosi=Pin(7), miso=Pin(4), firstbit=SPI.MSB)

motor_a = PWM(Pin(16, mode=Pin.OPEN_DRAIN, value=1))
motor_b = PWM(Pin(17, mode=Pin.OPEN_DRAIN, value=1))

motor_a.duty_u16(0)
motor_b.duty_u16(0)


def decode_angle(data):
    raw_data = (data[0] << 6) | (data[1] >> 2)
    angle_norm = (raw_data / 8192) - 1
    angle_degr = angle_norm * 360
    
    status_bits = (data[1] & 0b11) | (data[2] >> 6)
    crc = data[2] & 0b111111
    
    status_str = 'loss_track ' if status_bits & 0b1000 else '- '
    status_str += 'push ' if status_bits & 0b100 else 'no_push '
    
    if status_bits & 0b11 == 0:
        status_str += 'normal'
    elif status_bits & 0b11 == 1:
        status_str += 'strong'
    elif status_bits & 0b11 == 2:
        status_str += 'weak'
    else:
        status_str += '-'
    
    return angle_degr, status_bits, status_str, crc


def get_angle():
    cs.off()
    data = spi.read(3)
    cs.on()
    
    angle, _, _, _ = decode_angle(data)
    return angle


def set_move_ccw(gain):
    motor_a.duty_u16(gain)
    motor_b.duty_u16(0)
    

def set_move_cw(gain):
    motor_a.duty_u16(0)
    motor_b.duty_u16(gain)
    

def set_no_move():
    motor_a.duty_u16(0)
    motor_b.duty_u16(0)
    

# Move to start
while get_angle() > 0.5:
    set_move_ccw(20_000)
    
set_no_move()

time.sleep_ms(500)

deadline = time.ticks_add(time.ticks_ms(), 30 * 1000)

revs = 0
prev_angle = 0

# Max duty cycle
#set_move_ccw(65500)
    
while True:
    if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
        break
    
    angle = get_angle()
    
    if angle < prev_angle:
        revs += 1
    
    prev_angle = angle
    
    time.sleep_us(100)
    
print(revs)
