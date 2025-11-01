import importlib
import subprocess
import sys
from typing import List, Set

# Required packages for the application with specific versions
REQUIRED_PACKAGES = {
    'flet>=0.14.0',
    'opencv-contrib-python==4.8.0.74',  # Pin to working version
    'numpy>=1.24.0',
    'pillow>=10.0.0',
    'scikit-learn>=1.3.0',
    'scipy>=1.11.0',
    'requests>=2.31.0',
   # 'ultralytics>=8.0.0',  # For YOLOv8
   # 'insightface>=0.7.0'   # For ArcFace
}

def check_and_install_dependencies() -> None:
    """Check and install required packages."""
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        package_name = package.split('>=')[0]  # Get package name without version
        try:
            importlib.import_module(package_name.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            # First ensure pip is up to date
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip"
            ])
            
            # Then install required packages
            subprocess.check_call([
                sys.executable, 
                "-m", 
                "pip", 
                "install",
                *missing_packages
            ])
            print("Dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            sys.exit(1)