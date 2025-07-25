import numpy as np
from collections import deque
CONTROL_MAX = 10
INTEGRAL_MAX = 10


class PID:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.last_error = 0
        self.integral = 0
        self.derivs = deque(maxlen=5)

        self.last_time = None

    def calculate(self, setpoint, current, time_sec):
        dt = None
        if self.last_time is None:
            self.last_time = time_sec
        else:
            dt = time_sec - self.last_time

        # Hedef ile mevcut arasındaki hata
        error = setpoint - current

        # Hedefe yeterince yakınsa servo oynatmaya gerek yok

        # Entegral terimini sınırlayarak taşmayı önle
        if dt is None:
            self.last_error = error
            return self.Kp * error

        self.integral += error * dt
        self.integral = np.clip(self.integral, -INTEGRAL_MAX, INTEGRAL_MAX)

        # Hatanın değişim oranı (türev bileşeni)
        derivative = (error - self.last_error) / dt
        self.derivs.append(derivative)
        derivative = np.mean(self.derivs)
        self.last_error = error

        # PID formülü ile çıkış hesapla
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        output = np.clip(output, -CONTROL_MAX, CONTROL_MAX)
        # Servo hareketini sınırla (tepkiyi yumuşat)
        return output

    def reset(self):
        self.last_error = 0
        self.integral = 0
        self.last_time = None
