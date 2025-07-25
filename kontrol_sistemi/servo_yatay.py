import lgpio
from time import sleep

# Servo ayarları
SERVO_PIN = 5           # Yatay servo pini (gerekirse değiştir)
MIN_ANGLE = 0
MAX_ANGLE = 270
MIN_PULSE = 500         # µs
MAX_PULSE = 2500        # µs

# LGPIO setup
chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, SERVO_PIN, 0)

def aciyi_pwme_cevir(angle):
    angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
    normalized = (angle - MIN_ANGLE) / (MAX_ANGLE - MIN_ANGLE)
    pulse = MIN_PULSE + (normalized * (MAX_PULSE - MIN_PULSE))
    duty_cycle = (pulse / 20000) * 100
    return duty_cycle

def servo_git(angle, bekle=0.5):
    dc = aciyi_pwme_cevir(angle)
    lgpio.tx_pwm(chip, SERVO_PIN, 50, dc)
    print(f"Servo {angle}° konumuna gidiyor... (DC: {dc:.2f}%)")
    sleep(bekle)
    lgpio.tx_pwm(chip, SERVO_PIN, 0, 0)

def servo_kapat():
    lgpio.tx_pwm(chip, SERVO_PIN, 0, 0)
    lgpio.gpiochip_close(chip)
    print("Servo kapatıldı.")

# Ana kontrol
if __name__ == "__main__":
    try:
        # Orta nokta
        servo_git(135, bekle=0.6)

        # Sağa dön (örnek: 200 derece)
        servo_git(200, bekle=0.6)

        # Sola dön (örnek: 70 derece)
        servo_git(70, bekle=0.6)

        # Tekrar orta
        servo_git(135, bekle=0.6)

    except KeyboardInterrupt:
        print("Kullanıcı durdurdu.")
    finally:
        servo_kapat()

