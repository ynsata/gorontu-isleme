import lgpio
from time import sleep

# --- Ayarlar ---
PWM_GPIO = 6          # Servo bağlı GPIO pini
CHIP = 0              # gpiochip0
FREQ = 50             # 50Hz = 20ms periyot
DELAY = 0.08          # Her adım arası bekleme süresi
STEP = 1              # Kaç derecelik adımlarla hareket edilsin

# --- lgpio başlat ---
h = lgpio.gpiochip_open(CHIP)

def angle_to_pulse(angle):
    # 0° → 500 µs, 270° → 2500 µs
    pulse_us = 500 + (angle / 270) * 2000
    return pulse_us

def set_servo_angle(angle):
    pulse = angle_to_pulse(angle)
    duty_cycle = (pulse / 20000) * 100
    lgpio.tx_pwm(h, PWM_GPIO, FREQ, duty_cycle)
    print(f"[Servo] Açı: {angle}° → Duty: {duty_cycle:.2f}%")
    sleep(DELAY)

try:
    while True:
        # Aşağıdan yukarı (115° → 165°)
        for angle in range(135, 205, STEP):
            set_servo_angle(angle)

        # Yukarıdan aşağı (165° → 115°)
        for angle in range(205, 135, -STEP):
            set_servo_angle(angle)

        for angle in range(135, 115, -STEP):
            set_servo_angle(angle)

except KeyboardInterrupt:
    print("Durduruldu.")

finally:
    lgpio.tx_pwm(h, PWM_GPIO, 0, 0)
    lgpio.gpiochip_close(h)
    print("GPIO kapatıldı.")
