from time import time,sleep
import numpy as np
import socket
from tcp_server import receive_data
import lgpio


import threading as th
from pid import PID
from copy import deepcopy

pid_x = PID(0.5,0,0)
pid_y = PID(0.5,0,0)

FOV = np.array([45,27])
RESOLUTION = np.array([640,480])

def px_to_angle(px):
    px_norm = px-RESOLUTION/2
    px_norm/=RESOLUTION/2

    px_norm[1]*=-1

    angles = px_norm*FOV

    return angles


class RecvThread(th.Thread):
    def __init__(self):
        super().__init__()

        self.running = True

        self.manual_x=0
        self.manual_y=0
        self.manual_shoot = False

        self.x_pid_out = None
        self.y_pid_out = None
        self._lock = th.Lock()
        
    def process_manual_cmd(self,command):
        self.manual_x = 0
        self.manual_y = 0
        self.manual_shoot = False
        match command:
            
            case "saga":
                self.manual_x=1
            case "sola":
                self.manual_x=-1
            case "asagi":
                self.manual_y=-1
            case "yukari":
                self.manual_y=1
            case "ATIS":
                self.manual_shoot = True

    def get_pid_out(self):
        with self._lock:
            x_out = deepcopy(self.x_pid_out)
            y_out = deepcopy(self.y_pid_out)
            return (x_out,y_out) 

    def run(self):
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
                                self.process_manual_cmd(komut)
                            else:
                                print(f"[MAIN] Tanımsız string komut: {komut}")

                        elif isinstance(data, dict) and aktif_mod == "OTONOM":
                            self.manual_x = 0
                            self.manual_y = 0
                            self.manual_shoot = False

                            x = data.get("x")
                            y = data.get("y")
                            time_sec = data.get("time_sec")
                            print(f"y = {y}")
                            px = np.array([x,y])

                            if x is not None and y is not None:
                                print(f"[MAIN] OTONOM veri alındı: x={x}, y={y}")
                                angle_errors = px_to_angle(px)
                                with self._lock:
                                    self.x_pid_out = pid_x.calculate(angle_errors[0],0,time_sec)
                                    self.y_pid_out = pid_y.calculate(angle_errors[1],0,time_sec)
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

running = True
receiver = RecvThread()
receiver.start()

PIN_X = 5
PIN_Y = 6

PWM_MIN = 500
PWM_MAX = 2500

X_OFFSET = 135
Y_OFFSET = 128

X_DIR = 1
Y_DIR = 1

X_SLEW_RATE = 5
Y_SLEW_RATE = 5


chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, PIN_X, 0)
lgpio.gpio_claim_output(chip, PIN_Y, 0)

X_LAST = 135
Y_LAST = 128

try:
    while running:
        start = time()





        dt = time()-start
        if dt<0.02:
            sleep(0.02-dt)
except KeyboardInterrupt:
    running = False
    receiver.running=False