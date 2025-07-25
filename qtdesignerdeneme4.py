import sys
import cv2
import requests
import json
import socket
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from ultralytics import YOLO

from arayuzdeneme2 import Ui_MainWindow

import threading as th

class AnaPencere(QtWidgets.QMainWindow):
    def __init__(self):
        super(AnaPencere, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setStyleSheet("QMainWindow {background-image: url(arkaplan.png);}")

        self.PI_IP = "192.168.137.10"
        self.PORT = 12345

        self.model = YOLO('epoch_46.pt')

        self.sock = self.baglan()
        self.son_gonderim = time.time()
        

        self.kamera = cv2.VideoCapture(0)
        self.kamera.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        self.kamera.set(cv2.CAP_PROP_FRAME_HEIGHT, 800)

        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.goruntuyu_guncelle)
        # self.timer.start(110)

        self.servo_timer = QtCore.QTimer()
        self.servo_timer.timeout.connect(self.servo_komut_gonder)
        self.aktif_yon = None

        self.otonom_mod = False
        self.servo_yatay = 135
        self.servo_dikey = 135

        self.ui.pushButton_7.clicked.connect(self.atis_yap)
        self.ui.pushButton_3.pressed.connect(lambda: self.basili_tut("yukari"))
        self.ui.pushButton_3.released.connect(self.durdur)
        self.ui.pushButton_5.pressed.connect(lambda: self.basili_tut("asagi"))
        self.ui.pushButton_5.released.connect(self.durdur)
        self.ui.pushButton_4.pressed.connect(lambda: self.basili_tut("saga"))
        self.ui.pushButton_4.released.connect(self.durdur)
        self.ui.pushButton_6.pressed.connect(lambda: self.basili_tut("sola"))
        self.ui.pushButton_6.released.connect(self.durdur)
        self.ui.pushButton_9.clicked.connect(self.acil_durdur)
        self.ui.pushButton_8.clicked.connect(self.angajman_kabul)

        self.ui.pushButton.clicked.connect(self.manuelle_gecis)
        self.ui.pushButton_2.clicked.connect(self.otonom_gecis)


        self.cv_running = True
        self.cv_thread = th.Thread(target=self.cv_loop)
        self.cv_thread.start()
    
    def cv_loop(self):
        while self.cv_running:
            start = time.time()

            self.goruntuyu_guncelle()

            dt = time.time() - start 
             



    def baglan(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            s.connect((self.PI_IP, self.PORT))
            print(f"Raspberry Pi'ye bağlanıldı: {self.PI_IP}:{self.PORT}")
            return s
        except Exception as e:
            print(f"Raspberry Pi'ye bağlanılamadı: {e}")
            return None

    def manuelle_gecis(self):
        self.otonom_mod = False
        print("Manuel mod aktif")
        self.set_butonlar(True)
        if self.sock:
            try:
                self.sock.sendall(b"MOD:MANUEL\n")
            except:
                pass

    def otonom_gecis(self):
        self.otonom_mod = True
        print("Otonom mod aktif")
        self.set_butonlar(False)
        if self.sock:
            try:
                self.sock.sendall(b"MOD:OTONOM\n")
            except:
                pass

    def set_butonlar(self, aktif):
        self.ui.pushButton_3.setEnabled(aktif)
        self.ui.pushButton_4.setEnabled(aktif)
        self.ui.pushButton_5.setEnabled(aktif)
        self.ui.pushButton_6.setEnabled(aktif)
        self.ui.pushButton_7.setEnabled(aktif)

    def acilari_ekrana_cevir(self, yatay, dikey, ekran_genislik, ekran_yukseklik):
        x = int((yatay / 270) * ekran_genislik)
        dikey = max(110, min(170, dikey))
        y = ekran_yukseklik - int((170 - dikey / 60) * ekran_yukseklik)
        return x, y

    def goruntuyu_guncelle(self):
        ret, frame = self.kamera.read()
        if not ret:
            return
        img_hw = frame.shape
        if self.otonom_mod:
            results = self.model.predict(source=frame, stream=True, imgsz=1280, conf=0.4, device="cuda",verbose=False)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    w=abs(x1-x2)
                    h=abs(y1-y2)

                    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)


                    print("tespit merkez:",cx,cy)
                    cls_id = int(box.cls[0])
                    
                    
                    confidence = box.conf[0].item()
                    class_name = self.model.names[cls_id].lower()

                    renk = (0, 0, 255) if class_name == "dusman" else (0, 255, 0)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), renk, 2)
                    cv2.putText(frame, f"{class_name} {confidence:.2f}", (int(x1), int(y1)-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, renk, 2)

                    if class_name == "dusman":
                        if self.sock:
                            try:
                                nx=cx-img_hw[1]
                                nx/=img_hw[1]
                                ny=cy-img_hw[0]
                                ny/=img_hw[0]
                                ny*=-1
                                veri_dict = {
                                    "class_name": class_name,
                                    "confidence": round(confidence, 2),
                                    "x": cx,
                                    "y": cy,
                                    "w": w,
                                    "h": h,
                                    "nx": round(nx, 3),
                                    "ny": round(ny, 3),
                                    #"servo_x": round(servo_x, 1),
                                    #"servo_y": round(servo_y, 1),
                                    "time_sec": time.time() 
                                }
                                veri_json = json.dumps(veri_dict) + "\n"
                                self.sock.sendall(veri_json.encode())
                                print(f"JSON gönderildi: {veri_json.strip()}")
                                self.son_gonderim = time.time()
                            except:
                                self.sock = self.baglan()
        else:
            ekran_genislik = frame.shape[1]
            ekran_yukseklik = frame.shape[0]
            hedef_x, hedef_y = self.acilari_ekrana_cevir(
                self.servo_yatay, self.servo_dikey, ekran_genislik, ekran_yukseklik)
            cv2.circle(frame, (hedef_x, hedef_y), 10, (0, 255, 0), 2)
            cv2.line(frame, (hedef_x - 7, hedef_y), (hedef_x + 15, hedef_y), (0, 255, 0), 1)
            cv2.line(frame, (hedef_x, hedef_y - 7), (hedef_x, hedef_y + 15), (0, 255, 0), 1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.ui.label_kamera.setPixmap(QPixmap.fromImage(q_image))

    def atis_yap(self):
        if self.sock:
            try:
                self.sock.sendall(b"ATIS\n")
            except:
                pass

    def basili_tut(self, yon):
        self.aktif_yon = yon
        # print(f"{self.aktif_yon=}")
        self.servo_timer.start(100)

    def durdur(self):
        self.servo_timer.stop()

    def servo_komut_gonder(self):
        if self.sock and self.aktif_yon:
            try:
                self.sock.sendall(f"{self.aktif_yon}\n".encode())
            except:
                pass

    def acil_durdur(self):
        if self.sock:
            try:
                self.sock.sendall(b"ACIL_DUR\n")
                QtCore.QTimer.singleShot(10000, self.kapat_sistem)
            except:
                pass

    def kapat_sistem(self):
        self.close()

    def angajman_kabul(self):
        if self.sock:
            try:
                self.sock.sendall(b"ANGAJMAN\n")
            except:
                pass

    def closeEvent(self, event):
        self.kamera.release()
        if self.sock:
            self.sock.close()

        self.cv_running = False
        print("Uygulama kapatıldı")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    pencere = AnaPencere()
    pencere.show()
    sys.exit(app.exec_())
