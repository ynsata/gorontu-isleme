import socket
import time
import json

PI_IP = "192.168.137.10"
PORT = 12345

def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((PI_IP, PORT))
        print("[CLIENT] Bağlantı sağlandı")

        sock.sendall("MOD:OTONOM".encode())
        time.sleep(1)

        y_degerleri = list(range(400, 800, 30)) + list(range(800, 400, -30))
        x_sabit = 400

        start_time = time.time()
        while time.time() - start_time < 15:
            for y in y_degerleri:
                data_dict = {"x": x_sabit, "y": y}
                data_json = json.dumps(data_dict)
                sock.sendall(data_json.encode())
                print(f"[CLIENT] Gönderildi: {data_json}")
                time.sleep(0.3)

        print("[CLIENT] Test tamamlandı.")
        sock.close()

    except Exception as e:
        print(f"[CLIENT] Hata: {e}")

if __name__ == "__main__":
    main()
