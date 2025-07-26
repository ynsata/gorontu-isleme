from ultralytics import YOLO
import cv2
from time import time
from collections import deque
import multiprocessing as mp
import threading as th

class DetectionProcess(mp.Process):
    def __init__(self,running,message_queue:mp.Queue,image_queue:mp.Queue):
        super().__init__()
        self.running = running
        self.message_queue = message_queue
        self.image_queue = image_queue

    def image_thread(self):

        while self.running.get():
            pass

    def run(self):

        while self.running.get():
            pass



frame_times = deque(maxlen=20)
model = YOLO("epoch_46.pt")


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1280)
# cap = cv2.flip(cap, -1)     # 180 derece döndür
# cap = cv2.flip(cap, 1)      # Y ekseninde aynala

print(" Kamera başlatıldı. Çıkmak için 'q' tuşuna bas.")

while True:
    start = time()
    ret, frame = cap.read()
    if not ret:
        print(" Kameradan görüntü alınamadı!")
        break

    
    results = model.predict(
        source=frame,
        device='cuda',  
        imgsz=1280,      # Daha küçük boyut FPS artırır
        conf=0.7,       
        half=True,      
        verbose=False
    )

    
    annotated_frame = results[0].plot()

    
    cv2.imshow("YOLO Model Testi", annotated_frame)

    #  Çıkış: 'q' tuşu
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    dt = time()-start
    frame_times.append(dt)

    print("FPS: ",1/(sum(frame_times)/len(frame_times)))

#  Kaynakları serbest bırak
cap.release()
cv2.destroyAllWindows()
