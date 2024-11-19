import PyInstaller.__main__
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'guiApp.py',  # Your main script
    '--name=YOKI',  # Name of the executable
    '--onefile',  # Create a single executable file
    '--windowed',  # Don't show console window
    '--icon=NONE',  # You can add an icon file here if you have one
    '--add-data=uploaded_products.db;.',  # Include the database file
    f'--distpath={os.path.join(current_dir, "dist")}',  # Output directory
    f'--workpath={os.path.join(current_dir, "build")}',  # Working directory
    '--clean',  # Clean PyInstaller cache
    '--noconfirm',  # Replace output directory without asking
])
