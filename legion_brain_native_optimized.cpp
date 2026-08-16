#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <winsock2.h>
#include <ws2tcpip.h>

// Link Windows Socket Library
#pragma comment(lib, "ws2_32.lib")

// --- SYSTEM STACK CONFIGURATION ---
const std::string HOST = "127.0.0.1";
const int LM_STUDIO_PORT = 1234;
const std::string PIPE_NAME = "\\\\.\\pipe\\LegionLocalBrainPipe";

// --- SANITIZED WORKSTATION PERFORMANCE SCHEMA ---
struct WorkstationPerformanceState {
    double cpu_utilization_pct = 0.0;
    double vram_headroom_mib = 4095.0;
    int active_parallel_slots = 1;
    bool is_gpu_bound = true;
};

// --- LANGGRAPH STATE MACHINE METAPHOR ---
struct BaseMessage {
    std::string role;
    std::string content;
};

struct AgentState {
    std::vector<BaseMessage> messages;
    WorkstationPerformanceState performance_metrics;
    bool execution_complete = false;
    std::string next_node = "agent_critic";
    std::string final_critique = "";
};

// --- ZERO-DEPENDENCY WINSOCK HTTP CLIENT ---
class BareMetalWinsockClient {
private:
    std::string host;
    int port;

public:
    BareMetalWinsockClient(std::string h, int p) : host(h), port(p) {}

    std::string post(const std::string& path, const std::string& json_payload) {
        WSADATA wsa;
        SOCKET s;
        struct sockaddr_in server;
        std::string response = "";

        if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
            return "{\"status\": \"FAILED\", \"error\": \"WSAStartup Failed\"}";
        }

        s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (s == INVALID_SOCKET) {
            WSACleanup();
            return "{\"status\": \"FAILED\", \"error\": \"Socket Creation Failed\"}";
        }

        char optval = 1;
        setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));

        server.sin_addr.s_addr = inet_addr(host.c_str());
        server.sin_family = AF_INET;
        server.sin_port = htons(port);

        if (connect(s, (struct sockaddr*)&server, sizeof(server)) < 0) {
            closesocket(s);
            WSACleanup();
            return "{\"status\": \"FAILED\", \"error\": \"Connection to LM Studio Port Refused\"}";
        }

        std::stringstream req_stream;
        req_stream << "POST " << path << " HTTP/1.1\r\n"
                   << "Host: " << host << ":" << port << "\r\n"
                   << "Content-Type: application/json\r\n"
                   << "Content-Length: " << json_payload.length() << "\r\n"
                   << "Connection: close\r\n\r\n"
                   << json_payload;

        std::string request = req_stream.str();
        send(s, request.c_str(), request.length(), 0);

        char buffer[4096];
        int bytes_recv;
        while ((bytes_recv = recv(s, buffer, sizeof(buffer) - 1, 0)) > 0) {
            buffer[bytes_recv] = '\0';
            response += buffer;
        }

        closesocket(s);
        WSACleanup();

        size_t body_pos = response.find("\r\n\r\n");
        if (body_pos != std::string::npos) {
            return response.substr(body_pos + 4);
        }
        return response;
    }
};