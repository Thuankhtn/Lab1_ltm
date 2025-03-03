#include <iostream>
#include <cstring>
#include <winsock2.h>
#include <ws2tcpip.h>
//#include <arpa/inet.h>
//#include <unistd.h>
//g++ client.cpp -o client -lws2_32 
//.\client.exe
//cho linux
using namespace std;
SOCKET client_socket;
sockaddr_in serverAddr;
char buffer[1024];
// Hàm khởi tạo Winsock
void initWinsock() {
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed\n";
        exit(1);
    }
}
int initClientSocket() {
    SOCKET client_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (client_socket == INVALID_SOCKET) {
        std::cerr << "Socket creation failed\n";
        WSACleanup();
        exit(1);
    }
    // Cấu hình địa chỉ server
    //struct sockaddr_in server_addr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(12345); // Port 12345
    serverAddr.sin_addr.s_addr = inet_addr("127.0.0.1"); // Địa chỉ IP của server
    //inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr); // Địa chỉ IP của server
    const char *message = "Hello from client!";
    sendto(client_socket, message, strlen(message), 0,
           (struct sockaddr *)&serverAddr, sizeof(serverAddr));

    // Nhận phản hồi từ server
    //socklen_t server_len = sizeof(server_addr);
    int server_len = sizeof(serverAddr);
    memset(buffer, 0, sizeof(buffer));
    int bytes_received = recvfrom(client_socket, buffer, sizeof(buffer), 0,
                                  (struct sockaddr *)&serverAddr, &server_len);
    if (bytes_received < 0) {
        std::cerr << "Error receiving data\n";
        //close(client_socket);
        closesocket(client_socket);

        return 1;
    }
    // In phản hồi từ server
    std::cout << "Received from server: " << buffer << "\n";
}
int main() {
    initWinsock();
    initClientSocket();
   

    
    // Đóng socket
   // close(client_socket);
   closesocket(client_socket);

    return 0;
}