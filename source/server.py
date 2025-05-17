import socket
import os
import time
import threading

# Cấu hình Server
SERVER_IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 32678
MAX_SAFE_DATA = 64000  # Dữ liệu tối đa để tránh lỗi UDP

def load_file_list():
    file_list = {}
    try:
        with open("input.txt", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 2:
                    continue  # bỏ qua dòng không đúng định dạng
                filename = parts[0]
                size_str = parts[1]

                if size_str.endswith("GB"):
                    size_gb = float(size_str.replace("GB", ""))
                    file_list[filename] = int(size_gb * 1024 * 1024 * 1024)
                elif size_str.endswith("MB"):
                    size_mb = float(size_str.replace("MB", ""))
                    file_list[filename] = int(size_mb * 1024 * 1024)
                elif size_str.endswith("KB"):
                    size_kb = float(size_str.replace("KB", ""))
                    file_list[filename] = int(size_kb * 1024)
                else:
                    print(f"⚠ Đơn vị kích thước không hợp lệ: {size_str} trong dòng {line.strip()}")
    except FileNotFoundError:
        print("⚠ Không tìm thấy input.txt")
    return file_list

def format_size(bytes):
    if bytes >= 1024 ** 3:
        return f"{bytes / (1024 ** 3):.2f} GB"
    elif bytes >= 1024 ** 2:
        return f"{bytes / (1024 ** 2):.2f} MB"
    elif bytes >= 1024:
        return f"{bytes / 1024:.2f} KB"
    else:
        return f"{bytes} bytes"

def watch_file_list():
    global file_list
    last_update = None
    while True:
        try:
            current_update = os.path.getmtime("input.txt")
            if last_update is None or current_update > last_update:
                file_list = load_file_list()
                last_update = current_update
                print("📂 Danh sách file đã được cập nhật:")
                for fname, size in file_list.items():
                    print(f"  - {fname:20} {format_size(size)}")
                print()
        except FileNotFoundError:
            print("⚠ Không tìm thấy input.txt!\n")
        time.sleep(5)

def send_file_list(client_addr):
    if not file_list:
        server_socket.sendto("ERROR: No files available".encode(), client_addr)
        print("Lỗi: Không có file nào để gửi")
        return
    file_list_msg = "FILE_LIST:\n" + "\n".join(
        [f"{fname} ({format_size(size)})" for fname, size in file_list.items()]
    )
    server_socket.sendto(file_list_msg.encode(), client_addr)
    print(f"📤 Đã gửi danh sách file tới {client_addr}:\n{file_list_msg}")

def send_file_chunk(filename, offset, size, client_addr):
    if not os.path.isfile(filename):
        server_socket.sendto(b"ERROR: File not found", client_addr)
        print(f"❌ Lỗi: {filename} không tồn tại!")
        return

    size = min(size, MAX_SAFE_DATA)

    with open(filename, "rb") as file:
        file.seek(offset)
        chunk = file.read(size)

    if not chunk:
        print(f"❌ Chunk rỗng – không đọc được dữ liệu tại offset {offset}")
        return

    header = f"FILE_CHUNK:{filename}:{offset}:{size}:"
    packet = header.encode() + chunk

    if len(packet) > 65507:
        print(f"❌ Gói tin quá lớn ({len(packet)} bytes), không gửi.")
        return

    print(f"📤 Chuẩn bị gửi offset {offset} ({len(chunk)} bytes) tới {client_addr}")

    try:
        for attempt in range(5):
            server_socket.sendto(packet, client_addr)
            print(f"📤 Gửi chunk offset {offset} (lần {attempt+1})")

            # ✅ Bắt đầu chờ đúng ACK
            ack_received = False
            start_time = time.time()

            while time.time() - start_time < 1.5:
                try:
                    ack_data, _ = server_socket.recvfrom(BUFFER_SIZE)
                    ack_str = ack_data.decode()
                    if f"ACK:{filename}:{offset}" in ack_str:
                        print(f"✅ Nhận đúng ACK cho offset {offset}")
                        ack_received = True
                        break
                    else:
                        print(f"⚠ Nhận ACK không khớp: {ack_str}")
                except socket.timeout:
                    break

            if ack_received:
                return  # chunk gửi thành công

        print(f"❌ Gửi chunk offset {offset} thất bại sau 5 lần.")

    except Exception as e:
        print(f"❌ Lỗi khi gửi chunk offset {offset} đến {client_addr}: {e}")

def handle_client_request():
    while True:
        try:
            data, client_addr = server_socket.recvfrom(BUFFER_SIZE)
            request = data.decode()
            print(f"📨 Nhận yêu cầu từ {client_addr}: {request}")

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
                    print(f"❌ Request sai định dạng: {request}")
                    continue
                _, filename, offset, size = parts
                send_file_chunk(filename, int(offset), int(size), client_addr)

        except socket.timeout:
            continue
        except Exception as e:
            print(f"❌ Lỗi không xác định: {e}")
            continue

# Khởi động server
file_list = load_file_list()
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_IP, PORT))
server_socket.settimeout(5.0)

# Theo dõi input.txt liên tục
threading.Thread(target=watch_file_list, daemon=True).start()
print(f"🚀 Server đang chạy tại {SERVER_IP}:{PORT}")
handle_client_request()
