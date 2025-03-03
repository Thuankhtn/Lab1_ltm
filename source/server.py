import socket
import os
import time
import threading

# Cấu hình Server
SERVER_IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 64000  # 64KB per packet
CHUNK_SIZE = 262144  # 256KB per chunk

def load_file_list():
    """ Đọc danh sách file từ input.txt và chuyển đổi kích thước từ MB sang bytes """
    file_list = {}
    try:
        with open("input.txt", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2 and parts[1].endswith("MB"):
                    filename = parts[0]
                    size_mb = int(parts[1].replace("MB", ""))  # Chuyển "10MB" → 10
                    file_list[filename] = size_mb * 1024 * 1024  # Chuyển MB → bytes
    except FileNotFoundError:
        print("⚠ Không tìm thấy input.txt!")

    return file_list


def watch_file_list():
    """ Quét lại file input.txt mỗi 5 giây để cập nhật danh sách file """
    global file_list
    last_update = None

    while True:
        try:
            # Kiểm tra thời gian chỉnh sửa file
            current_update = os.path.getmtime("input.txt")
            if last_update is None or current_update > last_update:
                file_list = load_file_list()
                last_update = current_update
                print("Danh sách file đã được cập nhật:", file_list)

        except FileNotFoundError:
            print(" Không tìm thấy input.txt!")

        time.sleep(5)  # Chờ 5 giây trước khi quét tiếp

# Gọi hàm quét file trong một luồng riêng biệt
threading.Thread(target=watch_file_list, daemon=True).start()

# Khi khởi động Server, tải danh sách file lần đầu
file_list = load_file_list()
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
        print(f"❌ Lỗi: {filename} không tồn tại!")
        return

    with open(filename, "rb") as file:
        file.seek(offset)
        chunk = file.read(size)

    # 📌 Kiểm tra dữ liệu đọc từ file
    print(f" Server đọc chunk {offset}: {len(chunk)} bytes từ {filename}")

    # Nếu không đọc được dữ liệu, báo lỗi ngay
    if len(chunk) == 0:
        print(f" Lỗi: Không đọc được dữ liệu từ {filename} tại offset {offset}")
        return  

    header = f"FILE_CHUNK:{filename}:{offset}:{size}:"
    packet = header.encode() + chunk

    # 📌 Kiểm tra nếu đây là chunk đầu tiên
    if offset == 0:
        print(f" Đã gửi chunk đầu tiên của {filename} tới {client_addr}")
 
    for attempt in range(5):  # Gửi tối đa 5 lần nếu mất gói
        server_socket.sendto(packet, client_addr)
        print(f"Đã gửi chunk {offset} của {filename}, lần {attempt + 1}")

        server_socket.settimeout(0.5)  # Chờ 500ms để nhận ACK
        try:
            ack, _ = server_socket.recvfrom(BUFFER_SIZE)
            if ack.decode().startswith(f"ACK:{filename}:{offset}"):
                print(f" Nhận ACK cho chunk {offset}, gửi thành công!")
                return  # Nếu nhận được ACK, thoát vòng lặp
        except socket.timeout:
            print(f"⚠ Lỗi: Không nhận được ACK lần {attempt + 1}, thử lại...")


def handle_client_request():
    """ Xử lý yêu cầu từ Client """
    while True:
        try:
            data, client_addr = server_socket.recvfrom(BUFFER_SIZE)
            request = data.decode()
            print(f" Nhận yêu cầu từ {client_addr}: {request}")
        except socket.timeout:
            print(" Không có dữ liệu nhận được, tiếp tục chờ...")
            continue

        if request.startswith("LIST_FILES"):
            send_file_list(client_addr)

        elif request.startswith("GET_FILE_SIZE"):
            filename = request.split(":")[1]
            if filename in file_list:
                file_size = file_list[filename]
                response = f"FILE_SIZE:{file_size}"
                server_socket.sendto(response.encode(), client_addr)
            else:
                server_socket.sendto("ERROR: File not found".encode(), client_addr)

        elif request.startswith("REQUEST_FILE"):
            parts = request.split(":")
            if len(parts) != 4:
                print(f" Lỗi: Request không hợp lệ từ {client_addr}: {request}")
                continue

            _, filename, offset, size = parts
            send_file_chunk(filename, int(offset), int(size), client_addr)
if __name__ == "__main__":
    handle_client_request()
