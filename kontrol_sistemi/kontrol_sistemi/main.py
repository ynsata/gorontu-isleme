from tcp_server import receive_data
from servo_control import handle_servo_direction, handle_manual_command
from servo_driver import ServoMotor
import socket

# --- Servo Tanımları ---
servo_yatay = ServoMotor(
    name="Yatay", 
    pin=5, 
    min_angle=0, 
    max_angle=270, 
    min_pulse=500, 
    max_pulse=2500
)

servo_dikey = ServoMotor(
    name="Dikey", 
    pin=6, 
    min_angle=0, 
    max_angle=270,
    min_pulse=500, 
    max_pulse=2500,
    start_angle=130
)

# Başlangıç pozisyonları
servo_yatay.set_angle(135)
servo_dikey.set_angle(128)


# Başlangıç modu
aktif_mod = "OTONOM"

def main():
    global aktif_mod

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 12345))
    server_socket.listen(5)

    print("[MAIN] Sunucu başlatıldı: 0.0.0.0:12345 – Bağlantı bekleniyor...")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"[MAIN] Yeni bağlantı: {addr[0]}:{addr[1]}")

            try:
                while True:
                    data = receive_data(client_socket)

                    if data is None:
                        print("[MAIN] Client bağlantıyı kapattı.")
                        break

                    if isinstance(data, str):
                        komut = data.strip()
                        if komut == "MOD:MANUEL":
                            aktif_mod = "MANUEL"
                            print("[MODE] MANUEL moda geçildi.")
                        elif komut == "MOD:OTONOM":
                            aktif_mod = "OTONOM"
                            print("[MODE] OTONOM moda geçildi.")
                        elif aktif_mod == "MANUEL":
                            handle_manual_command(servo_yatay, servo_dikey, komut)
                        else:
                            print(f"[MAIN] Tanımsız string komut: {komut}")

                    elif isinstance(data, dict) and aktif_mod == "OTONOM":
                        x = data.get("x")
                        y = data.get("y")
                        time_sec = data.get("time_sec")
                        print(f"y = {y}")

                        if x is not None and y is not None:
                            print(f"[MAIN] OTONOM veri alındı: x={x}, y={y}")
                            handle_servo_direction(servo_yatay, servo_dikey, x, y,time_sec)
                        else:
                            print("[MAIN] Uyarı: 'x' veya 'y' verisi eksik.")

                    else:
                        print("[MAIN] Bilinmeyen veri türü veya mod uyumsuzluğu.")

            except Exception as e:
                print(f"[MAIN] Client hata: {e}")
            finally:
                client_socket.close()
                print(f"[MAIN] {addr[0]} bağlantısı kapatıldı.")

    except KeyboardInterrupt:
        print("\n[MAIN] Sistem elle durduruldu (CTRL+C).")
    except Exception as e:
        print(f"[MAIN] Sunucu hatası: {e}")
    finally:
        server_socket.close()
        print("[MAIN] Sunucu kapatıldı.")

if __name__ == "__main__":
    main()
