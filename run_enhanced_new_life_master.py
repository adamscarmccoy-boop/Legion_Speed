import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

from dynamic_segment_master_enhanced import dynamic_segment_master

print("🚀 Launching ENHANCED dynamic mastering for 'GIRL NAME DREAM -  i need that.mp3'...")
# Run enhanced dynamic segment master targeting 'new life#1.wav' in Downloads
dynamic_segment_master(
    input_filename="GIRL NAME DREAM -  i need that.mp3",
    custom_output="new life#1.wav"
)
