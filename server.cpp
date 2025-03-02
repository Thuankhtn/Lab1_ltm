#include <iostream>
#include <cstring>
#include <winsock2.h>
#include <ws2tcpip.h>

//g++ server.cpp -o server.exe -lws2_32
//.\server.exe

//cho linux 
//g++ server.cpp -o server
//./server
//#include <arpa/inet.h>
//#include <sys/socket.h>
#pragma comment(lib, "ws2_32.lib") // Liên kết thư viện Winsock

int main() {
    // Khởi tạo Winsock
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed\n";
        return 1;
    }

    // Tạo socket
    SOCKET server_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (server_socket == INVALID_SOCKET) {
        std::cerr << "Socket creation failed: " << WSAGetLastError() << "\n";
        WSACleanup();
        return 1;
    }

    // Cấu hình địa chỉ server
    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(12345); // Port 12345
    server_addr.sin_addr.s_addr = INADDR_ANY; // Lắng nghe trên mọi địa chỉ IP

    // Bind socket đến địa chỉ và port
    if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        std::cerr << "Bind failed: " << WSAGetLastError() << "\n";
        closesocket(server_socket);
        //close(client_socket);

        WSACleanup();
        return 1;
    }

    std::cout << "Server is listening on port 12345\n";

    // Nhận và xử lý dữ liệu từ client
    char buffer[1024];
    sockaddr_in client_addr;
    int client_len = sizeof(client_addr);

    while (true) {
        // Nhận dữ liệu
        memset(buffer, 0, sizeof(buffer));
        int bytes_received = recvfrom(server_socket, buffer, sizeof(buffer), 0,
                                      (struct sockaddr *)&client_addr, &client_len);
        if (bytes_received == SOCKET_ERROR) {
            std::cerr << "Error receiving data: " << WSAGetLastError() << "\n";
            continue;
        }

        // In dữ liệu nhận được
        std::cout << "Received from client: " << buffer << "\n";

        // Gửi phản hồi lại client
        const char *response = "Hello from server!";
        if (sendto(server_socket, response, strlen(response), 0,
                   (struct sockaddr *)&client_addr, client_len) == SOCKET_ERROR) {
            std::cerr << "Send failed: " << WSAGetLastError() << "\n";
        }
    }

    // Đóng socket và giải phóng Winsock
    closesocket(server_socket);
    //close(client_socket);

    WSACleanup();
    return 0;
}