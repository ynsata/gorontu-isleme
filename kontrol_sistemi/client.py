import socket
import time
import random

# --- Raspberry Pi'nin IP adresi ve portu ---
PI_IP = "192.168.137.10"   # Pi'nin sabit IP'si (gerekiyorsa değiştir)
PORT = 12345

def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((PI_IP, PORT))
        print("[CLIENT] Bağlantı kuruldu.")

        # --- MODU OTONOM YAP ---
        sock.sendall("MOD:OTONOM".encode())
        time.sleep(1)

        # --- 10 saniye boyunca x ve y gönder ---
        start_time = time.time()
        while time.time() - start_time < 10:
            # 0–1280 arası x ve y üret
            x = random.randint(0, 1280)
            y = random.randint(0, 1280)

            data = f'{{"x": {x}, "y": {y}}}'
            sock.sendall(data.encode())

            print(f"[CLIENT] Gönderildi: x={x}, y={y}")
            time.sleep(0.3)  # 0.3 saniye arayla veri gönder

        print("[CLIENT] Veri gönderimi tamamlandı.")
        sock.close()

    except Exception as e:
        print(f"[CLIENT] Hata: {e}")

if __name__ == "__main__":
    main()
