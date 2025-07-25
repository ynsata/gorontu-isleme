import lgpio
from time import sleep

class ServoMotor:
    def __init__(self, name, pin,offset,is_reverse, min_angle=0, max_angle=270, min_pulse=500, max_pulse=2500, start_angle=None):
        self.name = name
        self.pin = pin
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.range_span = self.max_angle - self.min_angle

        self.frequency = 50
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse

        self.chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self.chip, self.pin, 0)

        self.offset = offset
        self.is_reverse = is_reverse

        # Yeni başlangıç açısı parametresi
        if start_angle is None:
            start_angle = (min_angle + max_angle) // 2

        start_angle = max(self.min_angle, min(self.max_angle, start_angle))
        self.current_angle = start_angle
        self.set_angle(start_angle, smooth=False)
        # print(f"[{self.name}] Servo başlatıldı: {self.current_angle}°")

    def _convert_to_pulse(self, angle):
        angle = max(self.min_angle, min(self.max_angle, angle))
        normalized = (angle - self.min_angle) / self.range_span
        pulse_range = self.max_pulse - self.min_pulse
        return self.min_pulse + (normalized * pulse_range)

    def set_angle(self, angle, smooth=True, step=1, delay=0.005):
        angle = max(self.min_angle, min(self.max_angle, angle))

        if smooth:
            self._smooth_move(angle, step, delay)
        else:
            pulse = self._convert_to_pulse(angle)
            duty_cycle = (pulse / 20000) * 100
            # print(f"{angle=}",f"{pulse=}",f"{duty_cycle=}")

            lgpio.tx_pwm(self.chip, self.pin, self.frequency, duty_cycle)
            sleep(delay)
            # lgpio.tx_pwm(self.chip, self.pin, 0, 0)
            self.current_angle = angle

        # print(f"[{self.name}] Servo ayarlandı: {angle}°")

    def _smooth_move(self, target_angle, step, delay):
        current = self.current_angle

        if current < target_angle:
            angles = range(int(current), int(target_angle) + 1, step)
        else:
            angles = range(int(current), int(target_angle) - 1, -step)

        for angle in angles:
            limited_angle = max(self.min_angle, min(self.max_angle, angle))
            pulse = self._convert_to_pulse(limited_angle)
            duty_cycle = (pulse / 20000) * 100
            lgpio.tx_pwm(self.chip, self.pin, self.frequency, duty_cycle)
            self.current_angle = limited_angle
            sleep(delay)

        lgpio.tx_pwm(self.chip, self.pin, 0, 0)
        # print(f"[{self.name}] Servo hedefe ulaştı: {self.current_angle}°")

    def stop(self):
        lgpio.tx_pwm(self.chip, self.pin, 0, 0)
        lgpio.gpiochip_close(self.chip)
        # print(f"[{self.name}] Servo durduruldu")
