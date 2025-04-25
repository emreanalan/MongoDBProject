import subprocess
import sys

files_to_run = [
    "Al_GD_Cop_fetching.py",
    "EUR_TRY_Fetching.py"
]

python_path = sys.executable  # Aktif ortamın Python yolu

for file in files_to_run:
    try:
        print(f"Running {file}...")
        subprocess.run([python_path, file], check=True)
        print(f"Finished running {file}.\n")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running {file}: {e}\n")
        break
