from servo_driver import ServoMotor
import time

servo = ServoMotor(
    name="Dikey", 
    pin=6,
    min_angle=110,
    max_angle=170,
    min_pulse=1200,
    max_pulse=1800,
    start_angle=135
)

while True:
    servo.set_angle(120, smooth=True, step=1, delay=0.05)
    time.sleep(1)
    servo.set_angle(170, smooth=True, step=1, delay=0.05)
    time.sleep(1)
