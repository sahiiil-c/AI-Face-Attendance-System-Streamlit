import subprocess
import sys
import importlib

def install(package):
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--upgrade", package]
    )


def ensure_packages():

    required_packages = {
        "streamlit": "streamlit",
        "opencv-python": "cv2",
        "numpy": "numpy",
        "pandas": "pandas",
        "openpyxl": "openpyxl",
        "matplotlib": "matplotlib",
        "seaborn": "seaborn"
    }

    print("\n🔍 Checking required libraries...\n")

    for package, module in required_packages.items():

        try:
            importlib.import_module(module)
            print(f"✅ {package} already installed")

        except ImportError:

            print(f"⬇ Installing {package}...")
            install(package)

    print("\n🚀 All libraries are ready!\n")


if __name__ == "__main__":
    ensure_packages()