
import PyInstaller.__main__
import shutil
import os

if __name__ == '__main__':
    # Clean dist/build folders
    if os.path.exists('dist'): shutil.rmtree('dist')
    if os.path.exists('build'): shutil.rmtree('build')

    PyInstaller.__main__.run([
        'main.py',
        '--paths=src',
        '--name=GameMonitor',
        '--onefile',
        '--windowed',
        '--icon=resources/icon.ico',
        '--add-data=resources;resources',
        '--collect-all=sv_ttk',  # Ensure sun-valley-ttk theme is collected
        '--clean',
        '--noconfirm',
    ])
