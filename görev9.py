from ultralytics import YOLO
import cv2
import socket
import time
import json

# Raspberry Pi IP ve port bilgileri
pi_ip = "192.168.137.10"
pi_port = 12345

# TCP bağlantısı
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
gonderim_araligi = 0.5  # saniyede 2 kez gönder

model = YOLO('runs/detect/train2/weights/best.pt')
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print(" Kamera açıldı. Çıkmak için 'q' tuşuna bas.")

aktif_hedef_id = None  # Şu an takip edilen hedef ID
son_hedef_id = None    # Önceki hedef ID

while True:
    ret, frame = cap.read()
    if not ret:
        print(" Kameradan görüntü alınamadı.")
        break

    results = model.track(
        source=frame,
        tracker="botsort.yaml",
        persist=True,
        conf=0.5,
        imgsz=1280,
        verbose=False
    )

    dusmanlar = []
    ids = []
    for track in results[0].boxes:
        if track.id is None:
            continue

        cls_id = int(track.cls[0])
        class_name = model.names[cls_id].lower()

        track_id = int(track.id[0])
        x1, y1, x2, y2 = track.xyxy[0].tolist()
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        confidence = track.conf[0].item()

        #  Terminalde yazdır
        etiket = "[DÜŞMAN]" if class_name == "dusman" else "[DOST]"
        print(f"{etiket} ID:{track_id}, Güven: {confidence:.2f}, Konum: ({cx}, {cy})")

        if class_name == "dusman":
            ids.append(track_id)
            dusmanlar.append({
                "track_id": track_id,
                "class_name": class_name,
                "confidence": round(confidence, 2),
                "x": cx,
                "y": cy
            })

        # Görüntüye kutu çiz
        renk = (0, 0, 255) if class_name == "dusman" else (0, 255, 0)
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), renk, 2)
        label = f"{etiket} ID:{track_id} {confidence:.2f}"
        cv2.putText(frame, label, (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, renk, 2)

    if dusmanlar:
        ids.sort()
        if aktif_hedef_id not in ids:
            #  Hedef kaybolmuş, sıradaki hedefe geç
            if son_hedef_id is not None:
                sonraki_ids = [i for i in ids if i > son_hedef_id]
                if sonraki_ids:
                    aktif_hedef_id = min(sonraki_ids)
                    print(f" Yeni hedef seçildi: ID {aktif_hedef_id}")
                else:
                    # Sahnedeki en küçük ID’li düşmana dön
                    aktif_hedef_id = min(ids)
                    print(f" Sahnedeki en küçük ID seçildi: ID {aktif_hedef_id}")
            else:
                # İlk başta hedef yoksa en küçüğü seç
                aktif_hedef_id = min(ids)
                print(f" Hedef kilitlendi: ID {aktif_hedef_id}")
        son_hedef_id = aktif_hedef_id

        # Aktif hedef verisini bul
        hedef_veri = next((d for d in dusmanlar if d["track_id"] == aktif_hedef_id), None)

        # Raspberry Pi’ye gönder
        if hedef_veri and (time.time() - son_gonderim > gonderim_araligi):
            if sock:
                try:
                    veri_json = json.dumps(hedef_veri) + "\n"
                    sock.sendall(veri_json.encode())
                    print(f" JSON gönderildi: {veri_json.strip()}")
                    son_gonderim = time.time()
                except Exception as e:
                    print(f" Veri gönderilemedi: {e}, yeniden bağlanılıyor...")
                    sock.close()
                    sock = baglan()
    else:
        print(" Sahnede düşman yok. Bekleniyor...")
        aktif_hedef_id = None
        son_hedef_id = None

    cv2.imshow('görev9', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if sock:
    sock.close()
    print(" Raspberry Pi bağlantısı kapatıldı.")
