import os
import time
import subprocess
import platform

def run_script(path):
    print(f"🚀 {path} başlatılıyor...")
    subprocess.run(["python", path], check=True)
    print(f"✅ {path} tamamlandı.\n")


def shutdown_or_sleep(action="shutdown"):
    if platform.system() == "Windows":
        if action == "shutdown":
            os.system("shutdown /s /t 1")
        elif action == "sleep":
            os.system("rundll32.exe powrprof.dll,SetSuspendState Sleep")
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        if action == "shutdown":
            os.system("sudo shutdown now")
        elif action == "sleep":
            os.system("systemctl suspend")
    else:
        print("⚠️ İşletim sistemi desteklenmiyor!")


if __name__ == "__main__":
    try:
        # 📁 Buraya doğru pathleri ver
        run_script(r"C:\Users\emrea\Desktop\FINAL_PROJECT\MongoDBProject\Build\ShopsDataSet.py")
        run_script(r"C:\Users\emrea\Desktop\FINAL_PROJECT\MongoDBProject\Build\CollusionDataSet.py")

        print("🎉 Tüm işlemler başarıyla tamamlandı!")

        # 💤 İşlemden sonra seç:
        time.sleep(10)  # 10 saniye bekle sonra kapat/uykuya al

        shutdown_or_sleep(action="shutdown")  # veya "sleep"

    except subprocess.CalledProcessError:
        print("❌ Hata oluştu, işlemler kesildi.")
