import ctypes
import sys
import os

from image_pane import ImagePane
from file_manager import FileManager

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog, QMessageBox

import json

# Load the config file, config.json, in the same folder as this script
# default_folder: The image folder that is opened when the application is launched
# data_folder: The folder where the database images are copied to
# csv_data_file: The csv file where the database entries are stored


# If running as a PyInstaller package
if getattr(sys, 'frozen', False):
    # Use the directory of the executable as the base path
    base_path = os.path.dirname(sys.executable)
else:
    # Otherwise, use the directory of this script as the base path
    base_path = os.path.dirname(os.path.realpath(__file__))

# Move up one directory from the base path
parent_dir = os.path.dirname(base_path)

# Get supporting files relative to this script's directory
UI_FILE = os.path.join(parent_dir, 'resources', 'photoBooth.ui')
ICON_FILE = os.path.join(parent_dir, 'resources', 'trayicon.png')

def load_config():
    # Define the path to the config file, relative to the base path
    config_path = os.path.join(parent_dir, 'resources', 'config.json')    
    with open(config_path) as f:
        return json.load(f)

config = load_config()
DEFAULT_FOLDER = config['default_folder']

class MainWindow(QtWidgets.QMainWindow):
    """
    @brief Represents the main window of the PhotoBooth application.
    
    Loads the UI file created using Qt Designer and handles the signals
    and slots for the user interface elements.

    The UI file can be edited using Qt Designer to customize the appearance
    and layout of the user interface. 

    The names of the GUI elements can be found and edited in Qt Designer 
    """
    
    def __init__(self):
        """
        @brief Initializes the MainWindow object.  

        Instantiates the UI file and connects the signals and slots. Adds the most recent image
        from the default folder to the preview pane, ready to be added to the database.              

        """
        super(MainWindow, self).__init__()
        # Load the UI file created using Qt Designer
        uic.loadUi(UI_FILE, self)

        # Set window title
        self.setWindowTitle('PhotoBooth Database')

        # Initialize the file manager with the config settings for file paths
        self.file_manager = FileManager(config)  
        # Initialize the image pane (Image previewing and navigation)
        self.image_pane = ImagePane(self.file_manager.get_latest_file(), 
                                    self.imagePreviewLabel, 
                                    self.imageCounterLabel, 
                                    self.fpCurrentFileLabel)
        # Refresh the image preview label after iage_pane is initialized
        QtCore.QTimer.singleShot(0, lambda: self.image_pane.refresh())      

        # Connect the signals and slots for the GUI elements
        self.assign_signals_and_slots()
        # Populate the serial number list
        self.refresh_serial_number_list()

    def assign_signals_and_slots(self):
        """
        @brief Initializes the signals and slots for the GUI elements.

        """
        self.openImageButton.clicked.connect(self.open_images)
        self.addPhotoButton.clicked.connect(self.add_photos)
        self.exitButton.clicked.connect(self.close)
        self.previousButton.clicked.connect(self.image_pane.go_previous)
        self.nextButton.clicked.connect(self.image_pane.go_next)
        # Connect the selection signal to the handler function
        self.serialNumberList.itemSelectionChanged.connect(self.select_serial_number) 

    def open_images(self):
        """
        @brief Opens a file dialog to select multiple image files and update the image pane.

        """
        fnames, _ = QFileDialog.getOpenFileNames(self, 'Open file',
                                                 DEFAULT_FOLDER, "Image files (*.jpg *.gif *.png)")     
        if fnames:
            self.image_pane.load_images(fnames)

    def add_photos(self):
        """
        @brief Add the photos selected in the preview pane to the database. Record the entry in the database log

        Each photo is copied to the database folder specified in config settings, and the entry is recorded in the database log csv file.
        The details are pulled from the user selected fields in the GUI. The file name is generated according to the naming convention. 
        A warning is displayed if the file type already exists in the database or if a photo has not been selected, or if the serial number is invalid.
        """
        # Get the serial number, status, and comments from the GUI
        module_data = {
            'serial_number': self.snLineEdit.text(),
            'status': self.statusComboBox.currentText(),
            'comments': self.commentsTextEdit.toPlainText()
        }

        # Get the selected image paths from the image pane
        image_file_paths = self.image_pane.get_current_image_paths()

        # Validate the serial number and image, inform user if invalid
        if (not image_file_paths or not self.validate_serial_number(module_data['serial_number'])):
            QMessageBox.warning(self, "Warning", "No photo selected or serial number is invalid.")
            return

        # Try to add the photos to the database
        try:
            successful_files = self.file_manager.add_photos(image_file_paths, module_data)
        except PermissionError:
            QMessageBox.critical(self, "Error", 
                            "Unable to write to the database file. Please close any other applications using it (e.g. Excel) and try again.")
            return
        else:
            # Display the final result
            QMessageBox.information(self, "Success", f"Added {successful_files} out of {len(image_file_paths)} photos to the database.")
            # Refresh the recent serial numbers list
            self.refresh_serial_number_list()
  
    def validate_serial_number(self, serial_number):
        """
        @brief Validates the serial number against any specific rules.

        """      
        # Replace this with more complex validation logic if needed
        return bool(serial_number and not serial_number.isspace())
        
    def refresh_serial_number_list(self):
        """
        Refreshes the list of serial numbers from the data folder, sorted by most recently modified.
        """
        serial_numbers = self.file_manager.get_most_recent_serial_numbers()  
        self.serialNumberList.clear()  # Clear the list
        self.serialNumberList.addItems(serial_numbers) 

    def select_serial_number(self):
        """
        Handles the serial number selection event. Sets the text of the serial number field to the selected serial number.
        """
        selected_items = self.serialNumberList.selectedItems()
        if selected_items:  # If there is a selected item
            self.snLineEdit.setText(selected_items[0].text())

    def keyPressEvent(self, event):
        """
        @brief Handle key press events to navigate through selected files with arrow keys.
        """
        if self.image_pane.images_loaded():  # Only process keys if images have been loaded
            if event.key() == QtCore.Qt.Key_Right:
                self.image_pane.go_next()
            elif event.key() == QtCore.Qt.Key_Left:
                self.image_pane.go_previous()
        else:
            super().keyPressEvent(event)
    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_FILE))

    # Some silly Windows stuff to make the taskbar icon look better
    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
    myappid = u'atlasitk.photoboothdatabase.1a' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
