import socket
import os
import time

# Cấu hình Server
SERVER_IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 1024
CHUNK_SIZE = 262144  # 256KB per chunk

# Danh sách file có sẵn trên Server
file_list = {
    "File1.zip": 1024*1024,
    "File2.zip": 1024
}

# Tạo UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_IP, PORT))
server_socket.settimeout(5.0)  # Tránh Server bị treo nếu không có dữ liệu

print(f"Server đang chạy trên {SERVER_IP}:{PORT}")

def send_file_list(client_addr):
    """ Gửi danh sách file về Client """
    if not file_list:
        server_socket.sendto("ERROR: No files available".encode(), client_addr)
        print("Lỗi: Không có file nào để gửi")
        return

    file_list_msg = "FILE_LIST:" + ";".join([f"{fname}:{size}\n" for fname, size in file_list.items()])
    server_socket.sendto(file_list_msg.encode(), client_addr)
    print(f"Đã gửi danh sách file tới {client_addr}")

def send_file_chunk(filename, offset, size, client_addr):
    """ Gửi một phần của file cho Client """
    if not os.path.isfile(filename):  # Kiểm tra file có tồn tại không
        error_msg = "ERROR: File not found"
        server_socket.sendto(error_msg.encode(), client_addr)
        print(f"Lỗi: {filename} không tồn tại")
        return

    with open(filename, "rb") as file:
        file.seek(offset)
        chunk = file.read(size)

    header = f"FILE_CHUNK:{filename}:{offset}:{size}:"
    packet = header.encode() + chunk

    for attempt in range(5):  # Gửi tối đa 5 lần nếu mất gói
        server_socket.sendto(packet, client_addr)
        print(f"Đã gửi chunk {offset} của {filename}, lần {attempt + 1}")

        server_socket.settimeout(0.5)  # Chờ 500ms để nhận ACK
        try:
            ack, _ = server_socket.recvfrom(BUFFER_SIZE)
            if ack.decode().startswith(f"ACK:{filename}:{offset}"):
                print(f"Nhận ACK cho chunk {offset}, gửi thành công!")
                return  # Nếu nhận được ACK, thoát vòng lặp
        except socket.timeout:
            print(f"Lỗi: Không nhận được ACK lần {attempt + 1}, thử lại...")

def handle_client_request():
    """ Xử lý yêu cầu từ Client """
    while True:
        try:
            data, client_addr = server_socket.recvfrom(BUFFER_SIZE)
            request = data.decode()
            print(f"Nhận yêu cầu từ {client_addr}: {request}")
        except socket.timeout:
            print("Không có dữ liệu nhận được, tiếp tục chờ...")
            continue

        if request.startswith("LIST_FILES"):
            send_file_list(client_addr)
        elif request.startswith("REQUEST_FILE"):
            parts = request.split(":")
            if len(parts) != 4:
                print(f"Lỗi: Request không hợp lệ từ {client_addr}: {request}")
                continue  # Bỏ qua request sai

            _, filename, offset, size = parts
            send_file_chunk(filename, int(offset), int(size), client_addr)

if __name__ == "__main__":
    handle_client_request()
