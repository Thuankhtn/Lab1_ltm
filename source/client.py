import socket
import time
import os

# Cấu hình Client
SERVER_IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 64000
MAX_ATTEMPTS = 5    # Số lần thử lại nếu mất gói
# Tạo UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
def get_file_size(client_socket, filename, server_addr):
    """ Yêu cầu Server gửi kích thước file trước khi tải """
    request = f"GET_FILE_SIZE:{filename}"
    client_socket.sendto(request.encode(), server_addr)

    try:
        client_socket.settimeout(3.0)  # Timeout 3 giây để tránh treo
        data, _ = client_socket.recvfrom(1024)
        if data.startswith(b"FILE_SIZE:"):
            return int(data.decode().split(":")[1])  # Trả về kích thước file (bytes)
        else:
            print(f" Lỗi: Phản hồi không hợp lệ từ Server ({data.decode()})")
            return None
    except socket.timeout:
        print(" Lỗi: Không nhận được phản hồi từ Server")
        return None

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

def download_file(client_socket, server_filename, local_filename, file_size, server_addr):
    """ Tải file từ Server nhưng lưu với tên khác trên Client """
    print(f" Đang tải {server_filename} ({file_size / (1024 * 1024):.2f} MB) về {local_filename}...")
    start_time = time.time()
    with open(local_filename, "wb") as output_file:
        for offset in range(0, file_size, BUFFER_SIZE):
            request = f"REQUEST_FILE:{server_filename}:{offset}:{BUFFER_SIZE}"
            client_socket.sendto(request.encode(), server_addr)

            try:
                chunk, _ = client_socket.recvfrom(BUFFER_SIZE + 256)

                if not chunk.startswith(b"FILE_CHUNK"):
                    raise ValueError(f" Lỗi: Chunk {offset} không hợp lệ")

                parts = chunk.split(b":", 4)
                recv_offset = int(parts[2].decode())
                file_data = parts[4]

                output_file.seek(recv_offset)
                output_file.write(file_data)

                # Gửi ACK xác nhận
                ack = f"ACK:{server_filename}:{recv_offset}"
                client_socket.sendto(ack.encode(), server_addr)

            except Exception as e:
                print(f" Lỗi khi nhận chunk {offset}: {e}")

            progress = min((offset + BUFFER_SIZE) / file_size * 100, 100)
            print(f" Tiến độ: {progress:.2f}%", end="\r", flush=True)

    total_time = time.time() - start_time
    speed = file_size / (1024 * 1024) / total_time
    print(f"\n Tải hoàn tất: {local_filename} trong {total_time:.2f} giây (~{speed:.2f} MB/s)")

if __name__ == "__main__":
    request_file_list()
    # Yêu cầu Server gửi kích thước file
    file_size = get_file_size(client_socket, "1GB.bin", (SERVER_IP,PORT))
    if file_size:
        download_file(client_socket,"1GB.bin","Copy_1GB.bin",file_size,(SERVER_IP,PORT))
    else:
        print(" Không thể tải file vì không nhận được kích thước.")
    client_socket.close()

import socket
import time
import os

# Cấu hình Client
SERVER_IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 64000
MAX_ATTEMPTS = 5    # Số lần thử lại nếu mất gói
# Tạo UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
def get_file_size(client_socket, filename, server_addr):
    """ Yêu cầu Server gửi kích thước file trước khi tải """
    request = f"GET_FILE_SIZE:{filename}"
    client_socket.sendto(request.encode(), server_addr)

    try:
        client_socket.settimeout(3.0)  # Timeout 3 giây để tránh treo
        data, _ = client_socket.recvfrom(1024)
        if data.startswith(b"FILE_SIZE:"):
            return int(data.decode().split(":")[1])  # Trả về kích thước file (bytes)
        else:
            print(f" Lỗi: Phản hồi không hợp lệ từ Server ({data.decode()})")
            return None
    except socket.timeout:
        print(" Lỗi: Không nhận được phản hồi từ Server")
        return None

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

def download_file(client_socket, server_filename, local_filename, file_size, server_addr):
    """ Tải file từ Server nhưng lưu với tên khác trên Client """
    print(f"📥 Đang tải {server_filename} ({file_size / (1024 * 1024):.2f} MB) về {local_filename}...")
    start_time = time.time()
    with open(local_filename, "wb") as output_file:
        for offset in range(0, file_size, BUFFER_SIZE):
            request = f"REQUEST_FILE:{server_filename}:{offset}:{BUFFER_SIZE}"
            client_socket.sendto(request.encode(), server_addr)

            try:
                chunk, _ = client_socket.recvfrom(BUFFER_SIZE + 256)

                if not chunk.startswith(b"FILE_CHUNK"):
                    raise ValueError(f" Lỗi: Chunk {offset} không hợp lệ")

                parts = chunk.split(b":", 4)
                recv_offset = int(parts[2].decode())
                file_data = parts[4]

                output_file.seek(recv_offset)
                output_file.write(file_data)

                # Gửi ACK xác nhận
                ack = f"ACK:{server_filename}:{recv_offset}"
                client_socket.sendto(ack.encode(), server_addr)

            except Exception as e:
                print(f" Lỗi khi nhận chunk {offset}: {e}")

            progress = min((offset + BUFFER_SIZE) / file_size * 100, 100)
            print(f" Tiến độ: {progress:.2f}%", end="\r", flush=True)

    total_time = time.time() - start_time
    speed = file_size / (1024 * 1024) / total_time
    print(f"\n Tải hoàn tất: {local_filename} trong {total_time:.2f} giây (~{speed:.2f} MB/s)")

if __name__ == "__main__":
    request_file_list()
    # Yêu cầu Server gửi kích thước file
    file_size = get_file_size(client_socket, "100MB.bin", (SERVER_IP,PORT))
    if file_size:
        download_file(client_socket,"100MB.bin","Copy_1GB.bin",file_size,(SERVER_IP,PORT))
    else:
        print(" Không thể tải file vì không nhận được kích thước.")
    client_socket.close()
