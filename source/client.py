import socket
import time
import os
import threading

# Cấu hình Client
SERVER_IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 32768 # Kích thước gói tin

MAX_ATTEMPTS = 10
   # Số lần thử lại nếu mất gói

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def get_file_size(client_socket, filename, server_addr):
    """Yêu cầu Server gửi kích thước file trước khi tải"""
    request = f"GET_FILE_SIZE:{filename}"
    client_socket.sendto(request.encode(), server_addr)

    try:
        client_socket.settimeout(1010.0)
        data, _ = client_socket.recvfrom(1024)
        if data.startswith(b"FILE_SIZE:"):
            return int(data.decode().split(":")[1])
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

def merge_parts(local_filename, expected_total_size):
    total = 0
    with open(local_filename, "wb") as output:
        for i in range(4):
            part_file = f"{local_filename}.part{i}"
            if not os.path.exists(part_file):
                print(f"⚠️ Không tìm thấy {part_file}, bỏ qua.")
                continue
            part_size = os.path.getsize(part_file)
            print(f"🧩 Ghép {part_file} - {part_size / (1024 * 1024):.2f} MB")
            total += part_size
            with open(part_file, "rb") as part:
                output.write(part.read())
            os.remove(part_file)
    print(f"📦 Tổng dung lượng file sau khi ghép: {total / (1024 * 1024):.2f} MB")

    if total != expected_total_size:
        print(f"❌ Dung lượng KHÔNG KHỚP! Mong đợi: {expected_total_size} bytes | Thực tế: {total} bytes")
    else:
        print("✅ Dung lượng file chính xác!")


def download_file_parallel(server_filename, local_filename, total_size):
    print(f"📥 Đang tải {server_filename} ({total_size / (1024*1024):.2f} MB) với 4 kết nối song song...")

    num_parts = 4
    chunk_size = total_size // num_parts
    threads = []
    progress = [0] * num_parts

    for i in range(num_parts):
        offset = i * chunk_size
        if i == num_parts - 1:
            size = total_size - offset
        else:
            size = chunk_size

        if size <= 0:
            size = total_size  # trường hợp file quá nhỏ

        t = threading.Thread(target=download_chunk, args=(i, server_filename, offset, size, local_filename, progress, total_size))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("\n✅ Tải hoàn tất. Đang ghép các phần...")
    merge_parts(local_filename, total_size)
    print(f"✅ File đã được lưu: {local_filename}")

def download_chunk(part_id, filename, offset, size, local_filename, progress, total_size):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    part_file = f"{local_filename}.part{part_id}"
    attempts = 0
    current_offset = offset

    # Mở file 1 lần bên ngoài vòng while
    with open(part_file, "wb") as f:
        while current_offset < offset + size:
            request_size = min(BUFFER_SIZE, offset + size - current_offset)
            request = f"REQUEST_FILE:{filename}:{current_offset}:{request_size}"
            sock.sendto(request.encode(), (SERVER_IP, PORT))

            try:
                sock.settimeout(5.0)
                chunk, _ = sock.recvfrom(BUFFER_SIZE + 256)

                if not chunk.startswith(b"FILE_CHUNK"):
                    raise ValueError(f"❌ Chunk không hợp lệ tại offset {current_offset}")

                parts = chunk.split(b":", 4)
                recv_offset = int(parts[2].decode())
                file_data = parts[4]

                if len(file_data) == 0:
                    print(f"❌ Chunk rỗng tại offset {current_offset}, thử lại...")
                    attempts += 1
                    if attempts >= MAX_ATTEMPTS:
                        print(f"❌ Không thể nhận chunk tại offset {current_offset} sau {MAX_ATTEMPTS} lần.")
                        print("🛑 Dừng tải để tránh file bị thiếu dữ liệu.")
                        sock.close()
                        os._exit(1)
                    continue

                # Ghi dữ liệu tại vị trí chính xác
                f.seek(recv_offset - offset)
                f.write(file_data)

                ack = f"ACK:{filename}:{recv_offset}"
                sock.sendto(ack.encode(), (SERVER_IP, PORT))

                progress[part_id] = min(progress[part_id] + len(file_data), size)
                part_percent = min(progress[part_id] / size * 100, 100.0)
                total_progress = min(sum(progress) / total_size * 100, 100.0)
                print(f"\r📥 Downloading {filename} part {part_id+1} .... {part_percent:.2f}% | Tổng: {total_progress:.2f}% - Nhận {len(file_data)} bytes tại offset {recv_offset}", end="", flush=True)

                attempts = 0
                current_offset += len(file_data)

            except socket.timeout:
                attempts += 1
                print(f"\n❌ Lỗi tại offset {current_offset} (lần {attempts}): timed out")
                if attempts >= MAX_ATTEMPTS:
                    print(f"❌ Không thể nhận chunk tại offset {current_offset} sau {MAX_ATTEMPTS} lần timeout.")
                    print("🛑 Dừng tải để tránh file bị thiếu dữ liệu.")
                    sock.close()
                    os._exit(1)

            except Exception as e:
                print(f"\n❌ Lỗi tại offset {current_offset}: {e}")
                attempts += 1
                if attempts >= MAX_ATTEMPTS:
                    print(f"❌ Không thể nhận chunk tại offset {current_offset} sau {MAX_ATTEMPTS} lần.")
                    print("🛑 Dừng tải để tránh file bị thiếu dữ liệu.")
                    sock.close()
                    os._exit(1)

    sock.close()
    actual_size = os.path.getsize(part_file)

    if actual_size < size:
        print(f"\n❌ PHẦN {part_id+1} KHÔNG ĐỦ DỮ LIỆU! Ghi được {actual_size} / {size} bytes.")
        print("🛑 Dừng tải để tránh tạo file lỗi.")
        os._exit(1)

    print(f"\n✅ Tải xong phần {part_id+1} ({part_file}) - Ghi đủ {actual_size} bytes")

    
if __name__ == "__main__":
    request_file_list()
    filename = "1GB.bin"
    file_size = get_file_size(client_socket, filename, (SERVER_IP, PORT))

    if file_size:
        download_file_parallel(filename, f"Copy_{filename}", file_size)
    else:
        print("Không thể tải file vì không nhận được kích thước.")

    client_socket.close()
