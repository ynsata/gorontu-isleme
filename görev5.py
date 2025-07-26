from ultralytics import YOLO
import cv2
import socket
import time
import json

#  Raspberry Pi IP ve port bilgileri
pi_ip = "192.168.137.10"
pi_port = 12345

#  TCP bağlantısı
def baglan():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.connect((pi_ip, pi_port))
        print(f" Raspberry Pi'ye bağlanıldı: {pi_ip}:{pi_port}")
        return s
    except Exception as e:
        print(f" Raspberry Pi'ye bağlanılamadı: {e}")
        return None

sock = baglan()
son_gonderim = time.time()
gonderim_araligi = 1  # 1 saniyede bir gönder

model = YOLO('runs/detect/train2/weights/best.pt')

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print(" Kamera açıldı. Çıkmak için 'q' tuşuna bas.")

aktif_hedef_id = None
atis_yapildi = False
MERKEZ_TOLERANS = 50  # Merkezden ±50px

while True:
    ret, frame = cap.read()
    if not ret:
        print(" Kameradan görüntü alınamadı.")
        break

    frame_center_x = int(frame.shape[1] / 2)
    frame_center_y = int(frame.shape[0] / 2)

    results = model.track(
        source=frame,
        tracker="botsort.yaml",
        persist=True,
        conf=0.5,
        imgsz=1280,
        verbose=False
    )

    mavi_balonlar = []
    ids = []

    for track in results[0].boxes:
        if track.id is None:
            continue

        cls_id = int(track.cls[0])
        class_name = model.names[cls_id].lower()

        if class_name != "mavi":
            continue  #  Yalnızca mavi balonları işleriz

        track_id = int(track.id[0])
        x1, y1, x2, y2 = track.xyxy[0].tolist()
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        confidence = track.conf[0].item()

        print(f" MAVİ Balon - ID:{track_id}, Güven: {confidence:.2f}, Konum: ({cx}, {cy})")
        ids.append(track_id)
        mavi_balonlar.append({
            "track_id": track_id,
            "class_name": class_name,
            "confidence": round(confidence, 2),
            "x": cx,
            "y": cy
        })

        # Görüntüde kutu çiz
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
        label = f"MAVI ID:{track_id} {confidence:.2f}"
        cv2.putText(frame, label, (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    if mavi_balonlar:
        ids.sort()
        if aktif_hedef_id not in ids:
            aktif_hedef_id = ids[0]  # En küçük ID'li mavi balon
            print(f" Yeni hedef kilitlendi: ID {aktif_hedef_id}")

        hedef = next((d for d in mavi_balonlar if d["track_id"] == aktif_hedef_id), None)

        if hedef:
            dx = abs(hedef["x"] - frame_center_x)
            dy = abs(hedef["y"] - frame_center_y)

            if dx <= MERKEZ_TOLERANS and dy <= MERKEZ_TOLERANS:
                print(f" Hedef merkezde (dx:{dx}, dy:{dy})")
                if not atis_yapildi:
                    try:
                        sock.sendall(b"ATIS\n")
                        print(" ATIS komutu gönderildi")
                        atis_yapildi = True
                    except Exception as e:
                        print(f" ATIS komutu gönderilemedi: {e}")
            else:
                atis_yapildi = False  # Hedef merkezden çıkarsa tekrar izin ver
    else:
        aktif_hedef_id = None
        atis_yapildi = False
        print(" Sahnede MAVI balon yok.")

    cv2.imshow('Mavi Balon Takibi', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if sock:
    sock.close()
    print(" Raspberry Pi bağlantısı kapatıldı.")
