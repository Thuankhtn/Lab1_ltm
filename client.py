import socket
import time
import os

# Cấu hình Client
SERVER_IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 1024

# Tạo UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def request_file_list():
    """ Yêu cầu danh sách file từ Server """
    client_socket.sendto("LIST_FILES".encode(), (SERVER_IP, PORT))
    data, _ = client_socket.recvfrom(BUFFER_SIZE)
    print("Danh sách file có sẵn:", data.decode())

def request_file_chunk(filename, offset, size):
    """ Yêu cầu tải một phần file từ Server """
    request = f"REQUEST_FILE:{filename}:{offset}:{size}"
    client_socket.sendto(request.encode(), (SERVER_IP, PORT))

    data, _ = client_socket.recvfrom(BUFFER_SIZE + size)
    return data

def download_file(filename, file_size):
    """ Tải file từ Server """
    print(f"Đang tải {filename} ({file_size} bytes)...")

    with open(filename, "wb") as output_file:
        for offset in range(0, file_size, BUFFER_SIZE):
            attempts = 0
            received = False

            while not received and attempts < 5:
                chunk = request_file_chunk(filename, offset, BUFFER_SIZE)

                if chunk.startswith(b"FILE_CHUNK"):
                    parts = chunk.split(b":", 4)
                    recv_offset = int(parts[2].decode())
                    file_data = parts[4]

                    output_file.seek(recv_offset)
                    output_file.write(file_data)

                    # Gửi ACK
                    ack = f"ACK:{filename}:{recv_offset}"
                    client_socket.sendto(ack.encode(), (SERVER_IP, PORT))
                    received = True

                attempts += 1
                time.sleep(0.1)  # Tránh spam request

            if not received:
                print(f"Lỗi: Không thể tải chunk {offset}")

            # Hiển thị tiến độ tải
            progress = (offset / file_size) * 100
            print(f"Tiến độ: {progress:.2f}%", end="\r", flush=True)

    print(f"\nTải hoàn tất: {filename}")

if __name__ == "__main__":
    request_file_list()
    download_file("File1.zip",1024*1024)
