# PhotoBoothDatabase
[![Image](https://i.imgur.com/dcGuVou.png)](IMAGE_URL)


A small GUI application to manage photo documentation of ITk Modules 

Note, this application is OS dependent and is made to run on a Windows machine

Python source files are found in /src
- photoBooth.py : The main program file handles UI, etc
- file_manager.py : A class to manage the transfer of files and writing to log
- image_pane.py: A class to handle the navigation and display of images in the program
- config.py: file path settings handler

Additional resource files
- photoBooth.ui : The GUI settings that can be edited or modified using Qt Designer https://build-system.fman.io/qt-designer-download
- config.json : Saved configurations for the filepaths for saving photos, database log, and default image folder *this must be made see below*
- trayicon.ico : An icon for creating an executable with pyinstaller
- trayicon.png : An icon for the windows taskbar to identify application

- database.csv : Database log, program will generate a new one at the log filepath if one does not already exist

### Config file
This is a .json that should contain the locations:

- A default folder for loading images from (where you are saving raw images from camera)
- A data folder where the images are databased
- A csv log file for storing actions taken in the software and logging comments

{
    "default_folder": "C:\\Users\\sghys\\Desktop\\PhotoBooth\\Test Images",
    "data_folder": "C:\\Users\\sghys\\Desktop\\PhotoBooth\\Database Images",
    "csv_data_file": "C:\\Users\\sghys\\Desktop\\PhotoBooth\\database.csv"
}

### Packaging into an executable for deployment onto any machine

This requires pyinstaller.  Run the commands below and it will produce a .exe file int he /dist folder that should not be moved from withing the PhotoBooth folder location.  This .exe can run on machines without Python installed

### Packaging the files for use on machine without Python installed
`pip install pyinstaller`    

Remember, when you use PyInstaller, you need to be in the active environment where you installed it (Windows in this case).
```
pyinstaller --onefile --windowed --icon=./resources/trayicon.ico --add-data "./resources/photoBooth.ui;resources/" --add-data "./resources/trayicon.ico;resources/" --add-data "./resources/trayicon.png;resources/" ./src/photoBooth.py
```
This runs from the root PhotoBooth directory with all the files in it.  The executable stays in the dist/ folder where it can be run with a shortcut.  The header of the photoBooth.py handles relative file paths for both the 'compiled' dist for the computer in the clean room and also for the interpreted development mode running the .py directly



