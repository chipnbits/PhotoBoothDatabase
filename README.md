# PhotoBoothDatabase
A small GUI application to manage photo documentation of ITk Modules 

Note, this application is OS dependent and is made to run on a Windows machine

- photoBooth.py : The main program file
- photoBooth.ui : The GUI settings that can be edited or modified using Qt Designer https://build-system.fman.io/qt-designer-download
- config.json : Saved configurations for the filepaths for saving photos, database log, and default image folder
- database.csv : Database log, program will generate a new one at the log filepath if one does not already exist
- trayicon.ico : An icon for creating an executable with pyinstaller
- trayicon.png : An icon for the windows taskbar to identify application



`pip install pyinstaller`    

Remember, when you use PyInstaller, you need to be in the active environment where you installed it (Windows in this case).
```
pyinstaller --onefile --windowed --icon=trayicon.ico --add-data "photoBooth.ui;." --add-data "trayicon.ico;." --add-data "trayicon.png;." --add-data "config.json;." photoBooth.py
```
This runs from the directory with all the files in it, the executable needs to be moved back into the main directory (containing .ui, etc) after the compilation happens or else it wont work.

After the .exe from dist folder should be moved back into the main PhotoBooth folder so that it is in the same folder as the data files (ui, json, etc) 
