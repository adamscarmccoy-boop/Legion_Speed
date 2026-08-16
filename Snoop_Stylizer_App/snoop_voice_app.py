import pyaudio, numpy as np, torch, sys, os, threading, time
from pedalboard import Pedalboard, Compressor, PitchShift, LowpassFilter, Delay

running = False

def run_audio(ui_status_callback=None):
    global running
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        shift = float(torch.load(os.path.join(base_dir, "snoop_pitch_delta.pt"))[0])
        board = Pedalboard([Compressor(threshold_db=-15, ratio=4), PitchShift(semitones=shift), LowpassFilter(cutoff_frequency_hz=2500), Delay(delay_seconds=0.15, mix=0.1)])
        
        p = pyaudio.PyAudio()
        stream_in = p.open(format=pyaudio.paFloat32, channels=1, rate=48000, input=True, frames_per_buffer=1024)
        stream_out = p.open(format=pyaudio.paFloat32, channels=1, rate=48000, output=True, frames_per_buffer=1024)
        
        if ui_status_callback: ui_status_callback("Status: LIVE 🎙️")
        while running:
            data = stream_in.read(1024, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.float32)
            out = board(audio, sample_rate=48000)
            stream_out.write(np.clip(out, -1.0, 1.0).astype(np.float32).tobytes())
    except Exception as e:
        print(f"Audio Error: {e}")
    finally:
        try: stream_in.close(); stream_out.close(); p.terminate()
        except: pass
        if ui_status_callback: ui_status_callback("Status: OFF")

def run_tkinter():
    import tkinter as tk
    root = tk.Tk()
    root.title("Snoop Stylizer (Tkinter)")
    root.geometry("300x150")
    
    status_var = tk.StringVar(value="Status: OFF")
    tk.Label(root, textvariable=status_var, font=("Arial", 12)).pack(pady=5)
    
    def toggle():
        global running
        if running:
            running = False
            btn.config(text="START", bg="green")
        else:
            running = True
            btn.config(text="STOP", bg="red")
            threading.Thread(target=run_audio, args=(lambda m: root.after(0, status_var.set, m),), daemon=True).start()
            
    btn = tk.Button(root, text="START", font=("Arial", 20, "bold"), command=toggle, bg="green", fg="white")
    btn.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    root.mainloop()

def run_pyqt():
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Snoop Stylizer (PyQt)")
    window.resize(300, 150)
    layout = QVBoxLayout()
    
    lbl = QLabel("Status: OFF")
    layout.addWidget(lbl)
    
    btn = QPushButton("START")
    btn.setStyleSheet("background-color: green; color: white; font-size: 20px; font-weight: bold;")
    
    def toggle():
        global running
        if running:
            running = False
            btn.setText("START")
            btn.setStyleSheet("background-color: green; color: white; font-size: 20px; font-weight: bold;")
        else:
            running = True
            btn.setText("STOP")
            btn.setStyleSheet("background-color: red; color: white; font-size: 20px; font-weight: bold;")
            threading.Thread(target=run_audio, args=(lbl.setText,), daemon=True).start()
            
    btn.clicked.connect(toggle)
    layout.addWidget(btn)
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())

def run_cli():
    print("\n========== VOICE STYLIZER (Terminal) ==========")
    while True:
        choice = input("1. Toggle Audio\n2. Exit\nChoice: ")
        if choice == '1':
            global running
            if running:
                running = False
                print("Audio Stopped.")
            else:
                running = True
                print("Audio Started.")
                threading.Thread(target=run_audio, daemon=True).start()
        elif choice == '2':
            running = False
            break

if __name__ == '__main__':
    try: run_tkinter()
    except:
        try: run_pyqt()
        except: run_cli()
