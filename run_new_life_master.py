import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

from dynamic_segment_master import dynamic_segment_master

print("🚀 Launching dynamic mastering for 'GIRL NAME DREAM -  i need that.mp3'...")
# Run dynamic segment master targeting 'new life.wav' in Downloads
dynamic_segment_master(
    input_filename="GIRL NAME DREAM -  i need that.mp3",
    custom_output="new life.wav"
)
