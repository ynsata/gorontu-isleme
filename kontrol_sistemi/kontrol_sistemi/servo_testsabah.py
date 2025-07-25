from pid import PID
import lgpio
from time import sleep

# --- Ateşleme için lgpio kurulumu ---
ATES_PIN = 26
chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, ATES_PIN)

def atesle():
    print("[ATES] Ateşleme tetiklendi!")
    lgpio.gpio_write(chip, ATES_PIN, 1)
    sleep(0.5)
    lgpio.gpio_write(chip, ATES_PIN, 0)

# --- PID Ayarları ---
pid_yatay = PID(Kp=0.0250, Ki=0.0125, Kd=0.2)
pid_dikey = PID(Kp=0.03, Ki=0.01, Kd=0.18)

# --- PID eşikleri ---
ESIK_YATAY = 0.15
ESIK_DIKEY = 0.15

# --- Görüntü Boyutları ---
GORUNTU_GENISLIK = 800
GORUNTU_YUKSEKLIK = 800

# --- Konumdan Açıya Çevirme ---
def konumu_aciya_cevir_x(x):
    G = GORUNTU_GENISLIK
    ORTA = G / 2
    norm_x = (x - ORTA) / ORTA
    return 140 + (norm_x * 135)  # Merkez açıyı ayarladık (örneğin 140° fiziki merkezse)

def konumu_aciya_cevir_y(y):
    return 110 + ((y / GORUNTU_YUKSEKLIK) * 60)  # 110–170° aralığına çevir

# --- Otonom Mod: PID Kontrollü Servo Yönlendirme ---
def handle_servo_direction(servo_yatay, servo_dikey, x, y):
    # --- YATAY ---
    hedef_yatay = konumu_aciya_cevir_x(x)
    mevcut_yatay = servo_yatay.current_angle
    pid_output_yatay = pid_yatay.calculate(hedef_yatay, mevcut_yatay)
    print(f"[YATAY] hedef={hedef_yatay:.2f}, mevcut={mevcut_yatay:.2f}, pid={pid_output_yatay:.2f}")

    if abs(pid_output_yatay) > ESIK_YATAY:
        yeni_yatay = max(0, min(270, round(mevcut_yatay + pid_output_yatay)))
        if yeni_yatay != mevcut_yatay:
            servo_yatay.set_angle(yeni_yatay, smooth=True, step=1, delay=0.005)

    # --- DIKEY ---
    hedef_dikey = konumu_aciya_cevir_y(y)
    mevcud_dikey = servo_dikey.current_angle
    pid_output_dikey = pid_dikey.calculate(hedef_dikey, mevcud_dikey)
    print(f"[DIKEY] hedef={hedef_dikey:.2f}, mevcut={mevcud_dikey:.2f}, pid={pid_output_dikey:.2f}")

    if abs(pid_output_dikey) > ESIK_DIKEY:
        yeni_dikey = max(110, min(170, round(mevcud_dikey + pid_output_dikey)))
        if yeni_dikey != mevcud_dikey:
            servo_dikey.set_angle(yeni_dikey, smooth=True, step=1, delay=0.004)

# --- Manuel Mod: Komutlara Göre Servo + Ateşleme ---
def handle_manual_command(servo_yatay, servo_dikey, komut):
    adim = 5
    print(f"[MANUEL] Gelen komut: {komut}")

    if komut == "saga":
        hedef = servo_yatay.current_angle + adim
        servo_yatay.set_angle(min(servo_yatay.max_angle, hedef))
    elif komut == "sola":
        hedef = servo_yatay.current_angle - adim
        servo_yatay.set_angle(max(servo_yatay.min_angle, hedef))
    elif komut == "yukari":
        hedef = min(170, servo_dikey.current_angle + adim)
        servo_dikey.set_angle(hedef)
    elif komut == "asagi":
        hedef = max(110, servo_dikey.current_angle - adim)
        servo_dikey.set_angle(hedef)
    elif komut == "ATIS":
        print("[KOMUT] ATIS komutu alındı.")
        atesle()
    elif komut == "ACIL_DUR":
        print("[ACİL DUR] Tüm hareketler durduruldu.")
    elif komut == "ANGAJMAN":
        print("[ANGAJMAN] Angajman kabul edildi.")
    else:
        print(f"[MANUEL] Bilinmeyen komut: {komut}")
