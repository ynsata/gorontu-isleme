import socket
import json

def start_server(host='0.0.0.0', port=12345):
    """
    TCP sunucu başlatır ve istemciden gelen bağlantıyı kabul eder.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"[TCP] Sunucu başlatıldı: {host}:{port} – Bağlantı bekleniyor...")

    try:
        client_socket, addr = server_socket.accept()
        print(f"[TCP] Bağlantı kuruldu: {addr[0]}:{addr[1]}")
        return client_socket, server_socket
    except Exception as e:
        print(f"[TCP] Bağlantı hatası: {e}")
        server_socket.close()
        return None, None

def receive_data(client_socket):
    """
    TCP bağlantısından veri alır. Gelen veri JSON formatındaysa sözlük olarak,
    değilse düz string olarak döner.
    """
    try:
        data = client_socket.recv(1024)
        if not data:
            return None

        decoded = data.decode('utf-8').strip()

        # JSON olup olmadığını kontrol et
        if decoded.startswith("{") and decoded.endswith("}"):
            try:
                json_data = json.loads(decoded)
                if 'x' in json_data and 'y' in json_data:
                    return json_data
                else:
                    print("[TCP] Uyarı: JSON içinde 'x' veya 'y' eksik.")
                    return None
            except json.JSONDecodeError:
                print("[TCP] Hata: JSON çözümlenemedi.")
                return None
        else:
            # Düz komut olarak string döndür
            return decoded

    except Exception as e:
        print(f"[TCP] Veri alım hatası: {e}")
        return None
