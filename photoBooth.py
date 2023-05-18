import ctypes
import shutil
import csv
import sys
import os
import datetime

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QFileDialog, QSystemTrayIcon, QMessageBox

import json

# Load the config file, config.json, in the same folder as this script
# default_folder: The image folder that is opened when the application is launched
# data_folder: The folder where the database images are copied to
# csv_data_file: The csv file where the database entries are stored
def load_config(config_file='config.json'):
    with open(config_file) as f:
        return json.load(f)

config = load_config()

DEFAULT_FOLDER = config['default_folder']
DATA_FOLDER = config['data_folder']
CSV_DATA_FILE = config['csv_data_file']
UI_FILE = 'photoBooth.ui'
ICON_FILE = 'trayicon.png'

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

        # Assign function calls to the buttons
        self.openImageButton.clicked.connect(self.open_image)
        self.addPhotoButton.clicked.connect(self.add_photo)
        self.exitButton.clicked.connect(self.close)

        # Initialize the current image path (Image that is in the preview viewer)
        self.current_image_path = self.get_latest_file(DEFAULT_FOLDER)
        if self.current_image_path:  # If a latest file was found
            # Wait for main window to load before loading the image
            QtCore.QTimer.singleShot(0, lambda: self.preview_image(self.current_image_path))

    def open_image(self):
        """
        @brief Opens a file dialog to select an image file and displays it in the label.

        """
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file',
                                            DEFAULT_FOLDER, "Image files (*.jpg *.gif *.png)")
        if fname:
            self.current_image_path = fname
            self.preview_image(fname)


    def preview_image(self, img):
        """
        @brief Sets the image in the preview label to the image specified by the path.

        The image is scaled to fit the label.
        """

        # Convert the image to a format that can be displayed by Qt
        pixmap = QPixmap(img)
        scaled_pixmap = pixmap.scaled(self.imagePreviewLabel.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        # Set the image in the preview label
        self.imagePreviewLabel.setPixmap(scaled_pixmap)
        # Update the current file label (displays the file name currently in preview pane)
        self.fpCurrentFileLabel.setText(os.path.basename(img))

    def add_photo(self):
        """
        @brief Add the photo selected in the preview pane to the database. Record the entry in the database log

        The photo is copied to the database folder specifed in config settings, and the entry is recorded in the database log csv file.
        The details are pulled from the user selected fields in the GUI. The file name is generated according to the naming convention. 
        A warning is displayed if the file type already exists in the database or if a photo has not been selected, or if the serial number is invalid.
        """

        # Read the serial number and status from the GUI fields
        serial_number = self.snLineEdit.text()
        status = self.stausComboBox.currentText()

        # Validate the serial number and image, infom user if invalid
        if (not self.current_image_path or not self.validate_serial_number(serial_number)):
            QMessageBox.warning(self, "Warning", "No photo selected or serial number is invalid.")

        # If the serial number is valid and a photo is selected
        else:
            # Set the destination folder to reside in the database with the serial number as the folder name
            destination_folder = os.path.join(DATA_FOLDER, serial_number)
            # Create the folder matching the serial number if it does not already exist
            os.makedirs(destination_folder, exist_ok=True)
            # Generate the file name according to naming convention
            file_name = self.generate_file_name(serial_number, status)
            # Create a save path
            destination_file = os.path.join(destination_folder, file_name)

            # Check if the file status type already exists in the database
            # Recieved and Tested should usually only have one image per module in normal use cases
            if status in ['Received', 'Tested'] and self.file_status_exists(destination_folder, status):
                reply = QMessageBox.question(self, "File Duplicate Warning", "File with this status already exists. Are you sure you want to add another?", 
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.add_image_database(serial_number, status, destination_file)
                else:
                    QMessageBox.information(self, "Cancelled", "Operation cancelled.")
            else:
                self.add_image_database(serial_number, status, destination_file)

    def add_image_database(self, serial_number, status, destination_file):
        """
        @brief Write a copy of the image to disk and add the details to the database log csv file.

        """        
        shutil.copy2(self.current_image_path, destination_file)
        self.write_to_csv(serial_number, status, destination_file)
        QMessageBox.information(self, "Success", "Photo added to database.")       

    def validate_serial_number(self, serial_number):
        """
        @brief Validates the serial number against any specific rules.

        """      
        # Replace this with more complex validation logic if needed
        return bool(serial_number and not serial_number.isspace())
    
    def generate_file_name(self, serial_number, status):
        """
        @brief Generates a file name according to the naming convention specifed for the database.

        """  
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{serial_number}_{timestamp}_{status}"
        return file_name
    
    def file_status_exists(self, destination_folder, status):
        """
        Check if a file with the specified status already
        exists in the destination folder.
        """
        for filename in os.listdir(destination_folder):
            if status in filename:  # Checks if status keyword is in the filename
                return True
        return False
    
    def get_latest_file(self, dir_path):
        """
        Returns the path of the latest (most recently modified) file of the joined path(s)
        If the directory does not exist or is empty, returns None.
        """
        if not os.path.exists(dir_path):
            return None
        files = os.listdir(dir_path)
        if not files:  # If the list is empty
            return None
        paths = [os.path.join(dir_path, basename) for basename in files]
        return max(paths, key=os.path.getctime)
    
    def write_to_csv(self, serial_number, status, destination_file):
        """
        Write an entry to the CSV file. Each entry has the fields:
        date, time, serial number, status, comments, file save location
        If the file does not exist, creates a new one with headers.
        """

        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        comments = self.commentsTextEdit.toPlainText()  # Assuming comments are obtained from a QTextEdit widget

        #Check if CSV file exists or needs to be made
        file_exists = os.path.isfile(CSV_DATA_FILE)

        # Add the entry to the CSV file
        with open(CSV_DATA_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            # If the file does not exist, write the headers
            if not file_exists:
                # Header format
                writer.writerow(["Date", "Time", "Serial Number", "Status", "Comments", "File Save Location"])
                # Entry format
            writer.writerow([date, time, serial_number, status, comments, destination_file])

    
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
