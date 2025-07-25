from pid import PID
import lgpio
from time import sleep
import numpy as np

# --- Senaryo Modu Tanımı ---
senaryo_modu = "YETENEK10"

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
# pid_yatay = PID(Kp=0.035, Ki=0.019, Kd=0.45)
pid_yatay = PID(Kp=0.25, Ki=0.0, Kd=0)
pid_dikey = PID(Kp=1, Ki=0, Kd=0)

# --- PID eşikleri ---
ESIK_YATAY = 0.3
ESIK_DIKEY = 0.3

# --- Görüntü Boyutları ---
GORUNTU_GENISLIK = 640
GORUNTU_YUKSEKLIK = 480

# --- Dikey Servo için yazılımsal offset ---
OFFSET_DIKEY = 128  # Gerçekte 135° olan açı yazılımda 0° kabul edilecek

fov = [48, 27]
YATAY_OFFSET = 135
DIKEY_OFFSET = 128

def norm_px(px, res):
    x, y = px
    nx = x - res[0] / 2
    nx /= res[0] / 2

    ny = y - res[1] / 2
    ny /= res[1] / 2
    print(f"norm px: {nx},{ny}")
    return nx, ny


def px_to_angle(px, res, fov):
    x, y = norm_px(px,res)
    angle_x = -x * fov[0] / 2
    angle_y = -y * fov[1] / 2

    return (angle_x, angle_y)


# --- Otonom Mod: PID Kontrollü Servo Yönlendirme ---
def handle_servo_direction(servo_yatay, servo_dikey, x, y,time_sec):
    target_angles = px_to_angle((x, y), (GORUNTU_GENISLIK, GORUNTU_YUKSEKLIK), fov)

    hedef_yatay = target_angles[0]
    hedef_dikey = target_angles[1]

    hedef_dikey = np.clip(hedef_dikey,-1,1)
    
    mevcut_yatay = servo_yatay.current_angle
    # print(f"mevcut_Y = {mevcut_yatay}")
    pid_output_yatay = pid_yatay.calculate(hedef_yatay, 0,time_sec)
    # print(f"pid_y={pid_output_yatay}	")
    # if abs(pid_output_yatay) > ESIK_YATAY:
    yeni_yatay = max(0, min(270, round(mevcut_yatay + pid_output_yatay))) 
    print(f"{yeni_yatay=}",f"{hedef_yatay=}",f"{mevcut_yatay}")
        # print(f"yeni_yatay={yeni_yatay}")
        # if yeni_yatay != mevcut_yatay:
    servo_yatay.set_angle(int(round(yeni_yatay)), smooth=False, step=1, delay=0.005)
        #     # print(
        #         # f"[YATAY] mevcut={mevcut_yatay:.2f}, hedef={hedef_yatay:.2f}, çıktı={pid_output_yatay:.2f}, yeni={yeni_yatay}"
        #     # )
        # else:
        #     # print("[YATAY] Açı aynı, hareket yok.")
        #     pass
    # else:
        # print("[YATAY] PID çıktısı eşik altında, hareket yok.")
        # pass

    mevcud_dikey = servo_dikey.current_angle

    # print(f"hedef_dikey = {hedef_dikey}")
    # print(f"mevcud_dikey = {mevcud_dikey}")

    pid_output_dikey = pid_dikey.calculate(hedef_dikey, 0,time_sec)
    # print(f"pid_output_dikey = {pid_output_dikey}")
    dikey_komut = mevcud_dikey + pid_output_dikey
    # print("x: ",x,"y: ",y )
    # print(f"{dikey_komut=}\t{mevcud_dikey=}")
    # if abs(pid_output_dikey) > ESIK_DIKEY:
    yeni_dikey = max(110, min(170, dikey_komut))
    #     # print(f"yeni_dikey={yeni_dikey}")
    #     if yeni_dikey != mevcud_dikey:
    servo_dikey.set_angle(int(round(yeni_dikey)), smooth=False, step=1, delay=0.004)
    #         print(
    #             # f"[DİKEY] mevcud={mevcud_dikey:.2f}, hedef={hedef_dikey:.2f} (yazılımsal {pid_output_dikey:.2f}), çıktı={pid_output_dikey:.2f}, yeni={yeni_dikey}"
    #         )
    #     else:
    #         # print("[DİKEY] Açı aynı, hareket yok.")
    #         pass
    # else:
    #     # print("[DİKEY] PID çıktısı eşik altında, hareket yok.")
    #     pass
    


# --- Manuel Mod: Komutlara Göre Servo + Ateşleme ---
def handle_manual_command(servo_yatay, servo_dikey, komut):
    adim = 5
    print(f"[MANUEL] Gelen komut: {komut}")

    if komut == "saga":
        hedef = servo_yatay.current_angle + adim
        servo_yatay.set_angle(min(servo_yatay.max_angle, hedef))
        print(f"[YATAY] Sağa → {servo_yatay.current_angle}°")

    elif komut == "sola":
        hedef = servo_yatay.current_angle - adim
        servo_yatay.set_angle(max(servo_yatay.min_angle, hedef))
        print(f"[YATAY] Sola → {servo_yatay.current_angle}°")

    elif komut == "yukari":
        hedef = min(170, servo_dikey.current_angle + adim)
        servo_dikey.set_angle(hedef)
        yazilim_acisi = hedef - OFFSET_DIKEY
        print(
            f"[DİKEY] Yukarı → {servo_dikey.current_angle}° (yazılımsal: {yazilim_acisi:.2f}°)"
        )

    elif komut == "asagi":
        hedef = max(110, servo_dikey.current_angle - adim)
        servo_dikey.set_angle(hedef)
        yazilim_acisi = hedef - OFFSET_DIKEY
        print(
            f"[DİKEY] Aşağı → {servo_dikey.current_angle}° (yazılımsal: {yazilim_acisi:.2f}°)"
        )

    elif komut == "ATIS":
        print("[KOMUT] ATIS komutu alındı.")
        if senaryo_modu == "YETENEK9":
            print("[YETENEK9] Ateşleme pasif. Komut görmezden gelindi.")
            return
        elif senaryo_modu == "YETENEK10":
            aci = servo_yatay.current_angle
            if 120 < aci < 150:
                print(
                    f"[YETENEK10] Yasak açı bölgesi ({aci:.2f}°). Ateşleme engellendi."
                )
                return
            else:
                print(f"[YETENEK10] Serbest bölge ({aci:.2f}°). Ateşleme yapılıyor.")
                atesle()
        elif senaryo_modu == "YETENEK11":
            print("[YETENEK11] Otonom ateşleme gerçekleşiyor.")
            atesle()

    elif komut == "ACIL_DUR":
        print("[ACİL DUR] Tüm hareketler durduruldu.")

    elif komut == "ANGAJMAN":
        print("[ANGAJMAN] Angajman kabul edildi.")

    else:
        print(f"[MANUEL] Bilinmeyen komut: {komut}")
