import socket
import time
import os

# Cấu hình Client
SERVER_IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 256*1024
MAX_ATTEMPTS = 5    # Số lần thử lại nếu mất gói
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

def download_file(client_socket, filename, file_size, server_addr):
    """ Tải file từ Server theo từng chunk, tối ưu cho file lớn """
    print(f"📥 Đang tải {filename} ({file_size / (1024 * 1024):.2f} MB)...")

    start_time = time.time()  # ⏳ Ghi lại thời gian bắt đầu tải

    with open(filename, "wb") as output_file:
        for offset in range(0, file_size, BUFFER_SIZE):
            attempts = 0
            received = False

            while not received and attempts < MAX_ATTEMPTS:
                request = f"REQUEST_FILE:{filename}:{offset}:{BUFFER_SIZE}"
                client_socket.sendto(request.encode(), server_addr)

                try:
                    client_socket.settimeout(2.0)  # Timeout 2 giây
                    chunk, _ = client_socket.recvfrom(BUFFER_SIZE + 256)

                    if not chunk or not chunk.startswith(b"FILE_CHUNK"):
                        raise ValueError(f" Lỗi: Chunk {offset} không hợp lệ")

                    parts = chunk.split(b":", 4)
                    recv_offset = int(parts[2].decode())
                    file_data = parts[4]

                    output_file.seek(recv_offset)
                    output_file.write(file_data)

                    ack = f"ACK:{filename}:{recv_offset}"
                    client_socket.sendto(ack.encode(), server_addr)

                    received = True
                    if offset == 0:
                        print(f" Đã nhận chunk đầu tiên của {filename}")

                except (socket.timeout, ValueError):
                    attempts += 1
                    print(f" Chunk {offset} bị mất, thử lại ({attempts}/{MAX_ATTEMPTS})...")
                    time.sleep(0.2)

            if not received:
                print(f" Không thể tải chunk {offset} sau {MAX_ATTEMPTS} lần thử")

            progress = min((offset + BUFFER_SIZE) / file_size * 100, 100)
            print(f"⏳ Tiến độ: {progress:.2f}%", end="\r", flush=True)

    total_time = time.time() - start_time
    speed = file_size / (1024 * 1024) / total_time
    print(f"\n Tải hoàn tất: {filename} trong {total_time:.2f} giây (~{speed:.2f} MB/s)")

if __name__ == "__main__":
    request_file_list()
    download_file(client_socket,"File1.zip",1024 * 1024 * 1024,(SERVER_IP,PORT))
