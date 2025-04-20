import subprocess

files_to_run = [
    # "Al_GD_Cop_fetching.py",
    # "Production.py",
    # #"Manufacturer.py",
    # "FastUpdateMan.py",
    # #"Shops.py"
]

for file in files_to_run:
    try:
        print(f"Running {file}...")
        subprocess.run(["python", file], check=True)
        print(f"Finished running {file}.\n")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running {file}: {e}\n")
        break
