#include <iostream>
#include <cstring>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <map>
#include <fstream>
#include <vector>
//g++ server.cpp -o server.exe -lws2_32
//.\server.exe

//cho linux 
//g++ server.cpp -o server
//./server
//#include <arpa/inet.h>
//#include <sys/socket.h>
#pragma comment(lib, "ws2_32.lib") // Liên kết thư viện Winsock
#define PORT 12345
#define BUFFER_SIZE 1024
#define CHUNK_SIZE 262144 // 256KB per chunk
SOCKET server_socket;
char buffer[1024];
sockaddr_in serverAddr, clientAddr;
int clientLen = sizeof(clientAddr);

// Hàm khởi tạo Winsock
void initWinsock() {
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed\n";
        exit(1);
    }
}

// Hàm tạo UDP socket và bind
void createSocket() {
    server_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (server_socket == INVALID_SOCKET) {
        std::cerr << "Socket creation failed\n";
        WSACleanup();
        exit(1);
    }
    
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(PORT);

    if (bind(server_socket, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        std::cerr << "Bind failed\n";
        closesocket(server_socket);
        WSACleanup();
        exit(1);
    }
}
std::map<std::string, int> fileList = {
    {"File1.zip", 5 * 1024 * 1024},
    {"File2.zip", 10 * 1024 * 1024}
};


// Gửi danh sách file về Client
void sendFileList(sockaddr_in clientAddr) {
    std::string fileListMsg = "FILE_LIST:";
    for (auto& file : fileList) {
        fileListMsg += file.first + ":" + std::to_string(file.second) + "\n";
    }
    sendto(server_socket, fileListMsg.c_str(), fileListMsg.size(), 0, (sockaddr*)&clientAddr, clientLen);
}

void sendFileChunk(const std::string& filename, int offset, int size, sockaddr_in clientAddr) {
    std::ifstream file(filename, std::ios::binary);
    if (!file) {
        std::cerr << "File not found: " << filename << "\n";
        std::string errorMsg = "ERROR: File not found";
        sendto(server_socket, errorMsg.c_str(), errorMsg.size(), 0, (sockaddr*)&clientAddr, clientLen);
        return;
    }

    file.seekg(offset);
    std::vector<char> buffer(size);
    file.read(buffer.data(), size);
    
    std::string header = "FILE_CHUNK:" + filename + ":" + std::to_string(offset) + ":" + std::to_string(size) + ":";
    std::string packet = header + std::string(buffer.begin(), buffer.end());

    sendto(server_socket, packet.c_str(), packet.size(), 0, (sockaddr*)&clientAddr, clientLen);
}
void handleClientRequest() {
    char buffer[BUFFER_SIZE];
    while (true) {
        int bytesReceived = recvfrom(server_socket, buffer, BUFFER_SIZE, 0, (sockaddr*)&clientAddr, &clientLen);
        buffer[bytesReceived] = '\0';
        std::string request(buffer);

        if (request.rfind("LIST_FILES", 0) == 0) {
            sendFileList(clientAddr);
        } else if (request.rfind("REQUEST_FILE:", 0) == 0) {
            size_t pos1 = request.find(":");
            size_t pos2 = request.find(":", pos1 + 1);
            size_t pos3 = request.find(":", pos2 + 1);
            std::string filename = request.substr(pos1 + 1, pos2 - pos1 - 1);
            int offset = std::stoi(request.substr(pos2 + 1, pos3 - pos2 - 1));
            int size = std::stoi(request.substr(pos3 + 1));
            sendFileChunk(filename, offset, size, clientAddr);
        }
    }
}


int main() {
    initWinsock();
    createSocket();
    std::cout << "Server is listening on port 12345\n";

    // Nhận và xử lý dữ liệu từ client
    
    //sockaddr_in client_addr;
    //int client_len = sizeof(client_addr);

    while (true) {
        // Nhận dữ liệu
        memset(buffer, 0, sizeof(buffer));
        int bytes_received = recvfrom(server_socket, buffer, sizeof(buffer), 0,
                                      (struct sockaddr *)&clientAddr, &clientLen);
        if (bytes_received == SOCKET_ERROR) {
            std::cerr << "Error receiving data: " << WSAGetLastError() << "\n";
            continue;
        }

        // In dữ liệu nhận được
        std::cout << "Received from client: " << buffer << "\n";

        // Gửi phản hồi lại client
        const char *response = "Hello from server ne!";
        if (sendto(server_socket, response, strlen(response), 0,
                   (struct sockaddr *)&clientAddr, clientLen) == SOCKET_ERROR) {
            std::cerr << "Send failed: " << WSAGetLastError() << "\n";
        }
    }

    // Đóng socket và giải phóng Winsock
    closesocket(server_socket);
    //close(client_socket);

    WSACleanup();
    return 0;
}