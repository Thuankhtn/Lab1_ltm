#include <iostream>
#include <cstring>
#include <winsock2.h>
#include <ws2tcpip.h>
//#include <arpa/inet.h>
//#include <unistd.h>
//g++ client.cpp -o client -lws2_32 
//.\server.exe
using namespace std;
int main() {
    // Khởi tạo Winsock
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed\n";
        return 1;
    }

    // Tạo socket
    SOCKET client_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (client_socket == INVALID_SOCKET) {
        std::cerr << "Socket creation failed: " << WSAGetLastError() << "\n";
        WSACleanup();
        return 1;
    }
    // Cấu hình địa chỉ server
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(12345); // Port 12345
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1"); // Địa chỉ IP của server
    //inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr); // Địa chỉ IP của server

    // Gửi dữ liệu đến server
    const char *message = "Hello from client!";
    sendto(client_socket, message, strlen(message), 0,
           (struct sockaddr *)&server_addr, sizeof(server_addr));

    // Nhận phản hồi từ server
    char buffer[1024];
    //socklen_t server_len = sizeof(server_addr);
    int server_len = sizeof(server_addr);
    memset(buffer, 0, sizeof(buffer));
    int bytes_received = recvfrom(client_socket, buffer, sizeof(buffer), 0,
                                  (struct sockaddr *)&server_addr, &server_len);
    if (bytes_received < 0) {
        std::cerr << "Error receiving data\n";
        //close(client_socket);
        closesocket(client_socket);

        return 1;
    }

    // In phản hồi từ server
    std::cout << "Received from server: " << buffer << "\n";

    // Đóng socket
   // close(client_socket);
   closesocket(client_socket);

    return 0;
}