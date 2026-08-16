@echo off
echo Building Sovereign Audio Ingestion C++ Engine...
mkdir build
cd build
cmake ..
cmake --build . --config Release
echo Done! Run Release\SovereignAudioIngest.exe [MEDIA_URL]
