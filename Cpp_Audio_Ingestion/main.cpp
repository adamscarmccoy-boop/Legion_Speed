#define MINIAUDIO_IMPLEMENTATION
#include "miniaudio.h"
#include <iostream>
#include <vector>
#include <string>
#include <curl/curl.h>
#include <fstream>

// Memory buffer for curl to write to
struct MemoryStruct {
    char *memory;
    size_t size;
};

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;
    
    char *ptr = (char*)realloc(mem->memory, mem->size + realsize + 1);
    if(!ptr) return 0;
    
    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->memory[mem->size] = 0;
    
    return realsize;
}

int main(int argc, char** argv) {
    if(argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <raw_media_url>\n";
        return 1;
    }
    std::string url = argv[1];
    
    std::cout << "[1/3] Initializing libcurl to fetch stream...\n";
    curl_global_init(CURL_GLOBAL_ALL);
    CURL *curl_handle = curl_easy_init();
    
    struct MemoryStruct chunk;
    chunk.memory = (char*)malloc(1);
    chunk.size = 0;
    
    curl_easy_setopt(curl_handle, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl_handle, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
    curl_easy_setopt(curl_handle, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(curl_handle, CURLOPT_USERAGENT, "libcurl-agent/1.0");
    curl_easy_setopt(curl_handle, CURLOPT_FOLLOWLOCATION, 1L);
    
    std::cout << "[2/3] Downloading raw binary stream to memory...\n";
    CURLcode res = curl_easy_perform(curl_handle);
    if(res != CURLE_OK) {
        std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << "\n";
        return 1;
    }
    
    std::cout << "Successfully downloaded " << chunk.size << " bytes.\n";
    
    // Decode with miniaudio from memory buffer
    std::cout << "[3/3] Decoding compressed binary to pure float32 tensor via miniaudio...\n";
    
    ma_decoder decoder;
    ma_decoder_config config = ma_decoder_config_init(ma_format_f32, 2, 44100);
    ma_result result = ma_decoder_init_memory(chunk.memory, chunk.size, &config, &decoder);
    if (result != MA_SUCCESS) {
        std::cerr << "Failed to initialize decoder from memory.\n";
        return 1;
    }
    
    ma_uint64 frameCount;
    ma_decoder_get_length_in_pcm_frames(&decoder, &frameCount);
    
    std::vector<float> pcmData(frameCount * decoder.outputChannels);
    ma_uint64 framesRead;
    ma_decoder_read_pcm_frames(&decoder, pcmData.data(), frameCount, &framesRead);
    
    std::cout << "Successfully decoded " << framesRead << " PCM frames.\n";
    std::cout << "Writing pure 32-bit floating point math to sovereign_output.raw...\n";
    
    std::ofstream outFile("sovereign_output.raw", std::ios::binary);
    outFile.write(reinterpret_cast<const char*>(pcmData.data()), pcmData.size() * sizeof(float));
    outFile.close();
    
    ma_decoder_uninit(&decoder);
    free(chunk.memory);
    curl_easy_cleanup(curl_handle);
    curl_global_cleanup();
    
    std::cout << "SUCCESS! Pure Binary Output ready for Ray ingestion.\n";
    return 0;
}
