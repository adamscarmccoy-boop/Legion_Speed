#include <windows.h>
#include <tlhelp32.h>
#include <psapi.h>
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <iomanip>

// Helper to convert FILETIME to a 64-bit integer
uint64_t FileTimeToUInt64(const FILETIME& ft) {
    ULARGE_INTEGER uli;
    uli.LowPart = ft.dwLowDateTime;
    uli.HighPart = ft.dwHighDateTime;
    return uli.QuadPart;
}

// Struct to hold our process data
struct ProcessInfo {
    DWORD pid;
    DWORD parentPid;
    std::wstring name;
    std::wstring parentName;
    double cpuTimeMs;
};

// Function to get the name of a process given its PID
std::wstring GetProcessName(DWORD pid) {
    std::wstring name = L"<Unknown/Access Denied>";
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (hProcess) {
        WCHAR szProcessName[MAX_PATH];
        if (GetModuleBaseNameW(hProcess, NULL, szProcessName, sizeof(szProcessName) / sizeof(WCHAR))) {
            name = szProcessName;
        }
        CloseHandle(hProcess);
    }
    return name;
}

// Function to get total CPU time (User + Kernel) for a process in milliseconds
double GetProcessCpuTimeMs(DWORD pid) {
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    if (!hProcess) return 0.0;

    FILETIME creationTime, exitTime, kernelTime, userTime;
    double totalTimeMs = 0.0;
    
    if (GetProcessTimes(hProcess, &creationTime, &exitTime, &kernelTime, &userTime)) {
        uint64_t kernel = FileTimeToUInt64(kernelTime);
        uint64_t user = FileTimeToUInt64(userTime);
        // FILETIME resolution is 100-nanosecond intervals. Divide by 10,000 to get milliseconds.
        totalTimeMs = static_cast<double>(kernel + user) / 10000.0;
    }
    
    CloseHandle(hProcess);
    return totalTimeMs;
}

int main() {
    std::cout << "========================================================\n";
    std::cout << " C++ SVCHOST & BACKGROUND PROCESS MONITOR \n";
    std::cout << "========================================================\n\n";

    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) {
        std::cerr << "Failed to create process snapshot.\n";
        return 1;
    }

    PROCESSENTRY32W pe32;
    pe32.dwSize = sizeof(PROCESSENTRY32W);

    if (!Process32FirstW(hSnapshot, &pe32)) {
        std::cerr << "Failed to read first process.\n";
        CloseHandle(hSnapshot);
        return 1;
    }

    std::vector<ProcessInfo> svchostList;
    std::map<DWORD, std::wstring> pidToNameMap;

    // First pass: Build a map of all PIDs to Names
    do {
        pidToNameMap[pe32.th32ProcessID] = pe32.szExeFile;
    } while (Process32NextW(hSnapshot, &pe32));

    // Reset snapshot to iterate again for svchost specifically
    Process32FirstW(hSnapshot, &pe32);
    do {
        std::wstring exeName = pe32.szExeFile;
        // Check if it's svchost.exe (case-insensitive)
        if (_wcsicmp(exeName.c_str(), L"svchost.exe") == 0) {
            ProcessInfo info;
            info.pid = pe32.th32ProcessID;
            info.parentPid = pe32.th32ParentProcessID;
            info.name = exeName;
            
            // Resolve Parent Name
            if (pidToNameMap.find(info.parentPid) != pidToNameMap.end()) {
                info.parentName = pidToNameMap[info.parentPid];
            } else {
                info.parentName = L"<Terminated/Unknown>";
            }

            // Get CPU Time
            info.cpuTimeMs = GetProcessCpuTimeMs(info.pid);
            svchostList.push_back(info);
        }
    } while (Process32NextW(hSnapshot, &pe32));

    CloseHandle(hSnapshot);

    // Output Results
    std::cout << "Found " << svchostList.size() << " svchost.exe processes.\n\n";
    std::cout << std::left << std::setw(10) << "PID" 
              << std::setw(25) << "SPAWNED BY (PARENT)" 
              << std::setw(15) << "PARENT PID" 
              << "CPU TIME (ms)\n";
    std::cout << "--------------------------------------------------------------------\n";

    double totalCpuTime = 0.0;

    for (const auto& svc : svchostList) {
        totalCpuTime += svc.cpuTimeMs;
        
        std::wcout << std::left << std::setw(10) << svc.pid 
                   << std::setw(25) << svc.parentName 
                   << std::setw(15) << svc.parentPid 
                   << svc.cpuTimeMs << L" ms\n";
    }

    std::cout << "--------------------------------------------------------------------\n";
    std::cout << "Total svchost CPU Time: " << totalCpuTime << " ms\n";
    std::cout << "========================================================\n";
    std::cout << "Note: In Windows, most svchost.exe instances are spawned by 'services.exe'.\n";
    std::cout << "If an unexpected application spawns svchost, it will show up here.\n";

    return 0;
}
