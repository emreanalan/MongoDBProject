import subprocess
import sys
import time
import os
import platform

files_to_run = [
    "ShopsDataSet.py",
    "CollusionDataSet.py"
]

python_path = sys.executable  # Aktif ortamın Python yolu

def shutdown_or_sleep(action="sleep"):
    if platform.system() == "Windows":
        if action == "shutdown":
            os.system("shutdown /s /t 1")
        elif action == "sleep":
            os.system("rundll32.exe powrprof.dll,SetSuspendState Sleep")
    elif platform.system() in ["Linux", "Darwin"]:
        if action == "shutdown":
            os.system("sudo shutdown now")
        elif action == "sleep":
            os.system("systemctl suspend")
    else:
        print("⚠️ İşletim sistemi desteklenmiyor!")

if __name__ == "__main__":
    for file in files_to_run:
        try:
            print(f"🚀 {file} başlatılıyor...")
            subprocess.run([python_path, file], check=True)
            print(f"✅ {file} tamamlandı.\n")
        except subprocess.CalledProcessError as e:
            print(f"❌ Hata oluştu: {e}\n")
            break

    print("🎉 Tüm işlemler başarıyla tamamlandı.")
    time.sleep(50)  # 10 saniye bekle
    shutdown_or_sleep("sleep")  # veya "shutdown"
