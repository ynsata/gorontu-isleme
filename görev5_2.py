from ultralytics import YOLO
import cv2
import socket
import time

# 📡 Raspberry Pi IP ve port
pi_ip = "192.168.137.10"
pi_port = 12345

# 🔌 TCP bağlantısı
def baglan():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.connect((pi_ip, pi_port))
        print(f"✅ Raspberry Pi'ye bağlanıldı: {pi_ip}:{pi_port}")
        return s
    except Exception as e:
        print(f"❌ Raspberry Pi'ye bağlanılamadı: {e}")
        return None

sock = baglan()
son_gonderim = time.time()
gonderim_araligi = 1  # saniyede 1 kez gönder

# 🧠 YOLOv12 modeli yükle
model = YOLO('epoch_46.pt')

# 📷 Kamera ayarları
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("🚀 Kamera açıldı. Çıkmak için 'q' tuşuna bas.")

aktif_hedef_id = None
atis_yapildi = False
MERKEZ_TOLERANS = 50  # Merkezden ±50px

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Kameradan görüntü alınamadı.")
        break

    frame_center_x = int(frame.shape[1] / 2)
    frame_center_y = int(frame.shape[0] / 2)

    # 🏃‍♂️ YOLOv12 + BOTSORT takip
    results = model.track(
        source=frame,
        tracker="botsort.yaml",
        persist=True,
        conf=0.5,
        imgsz=1280,
        device='cuda',  # 🖥️ GPU kullan
        half=True,      # fp16 (RTX 4060 için)
        verbose=False
    )

    mavi_balonlar = []
    ids = []

    for r in results:
        if not r.boxes or r.boxes.id is None:
            continue

        boxes = r.boxes.xyxy.cpu().numpy()
        ids_list = r.boxes.id.cpu().numpy().astype(int)
        classes = r.boxes.cls.cpu().numpy().astype(int)
        confs = r.boxes.conf.cpu().numpy()

        for box, track_id, cls_id, conf in zip(boxes, ids_list, classes, confs):
            x1, y1, x2, y2 = map(int, box)
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            class_name = model.names[cls_id].lower()

            if class_name != "dost":
                continue  # Yalnızca mavi balonları işleriz

            print(f"🔵 MAVI Balon - ID:{track_id}, Güven: {conf:.2f}, Konum: ({cx}, {cy})")
            ids.append(track_id)
            mavi_balonlar.append({
                "track_id": track_id,
                "class_name": class_name,
                "confidence": round(conf, 2),
                "x": cx,
                "y": cy
            })

            # 🎯 Görüntüde kutu çiz
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            label = f"MAVI ID:{track_id} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    if mavi_balonlar:
        ids.sort()
        if aktif_hedef_id not in ids:
            aktif_hedef_id = ids[0]  # En küçük ID'li mavi balon
            print(f"🎯 Yeni hedef kilitlendi: ID {aktif_hedef_id}")

        hedef = next((d for d in mavi_balonlar if d["track_id"] == aktif_hedef_id), None)

        if hedef:
            dx = abs(hedef["x"] - frame_center_x)
            dy = abs(hedef["y"] - frame_center_y)

            if dx <= MERKEZ_TOLERANS and dy <= MERKEZ_TOLERANS:
                print(f"🎯 Hedef merkezde (dx:{dx}, dy:{dy})")
                if not atis_yapildi:
                    try:
                        sock.sendall(b"ATIS\n")
                        print("💥 ATIS komutu gönderildi")
                        atis_yapildi = True
                    except Exception as e:
                        print(f"❌ ATIS komutu gönderilemedi: {e}")
            else:
                atis_yapildi = False  # Hedef merkezden çıkarsa tekrar izin ver
    else:
        aktif_hedef_id = None
        atis_yapildi = False
        print("⏳ Sahnede MAVI balon yok.")

    cv2.imshow('Mavi Balon Takibi - YOLOv12', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if sock:
    sock.close()
    print("🔌 Raspberry Pi bağlantısı kapatıldı.")
