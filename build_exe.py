import PyInstaller.__main__
import os
import shutil

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Clean the dist and build directories first
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

PyInstaller.__main__.run([
    'guiApp.py',  # Your main script
    '--name=YOKI',  # Name of the executable
    '--onefile',  # Create a single executable file
    '--windowed',  # Don't show console window
    '--icon=logo.ico',  # Using the ico file as icon
    '--add-data=uploaded_products.db;.',  # Include the database file
    '--add-data=logo.ico;.',  # Include the icon file
    f'--distpath={os.path.join(current_dir, "dist")}',  # Output directory
    f'--workpath={os.path.join(current_dir, "build")}',  # Working directory
    '--clean',  # Clean PyInstaller cache
    '--noconfirm',  # Replace output directory without asking
])
