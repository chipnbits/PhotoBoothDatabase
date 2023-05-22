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
        self.addPhotoButton.clicked.connect(self.add_photos)
        self.exitButton.clicked.connect(self.close)
        self.previousButton.clicked.connect(self.go_previous)
        self.nextButton.clicked.connect(self.go_next)

        # Initialize the current image paths and current index
        self.selected_image_paths = []
        self.current_image_index = 0

        # Initialize the current image path (Image that is in the preview viewer)
        self.current_image_path = self.get_latest_file(DEFAULT_FOLDER)
        if self.current_image_path:  # If a latest file was found
            self.selected_image_paths.append(self.current_image_path)  # Add the file to the list
            # Wait for main window to load before loading the image
            QtCore.QTimer.singleShot(0, lambda: self.preview_image(self.current_image_path))
            # Update image count label
            self.imageCounterLabel.setText("Image 1 of 1")

        # Populate the serial number list
        self.refresh_serial_number_list()
        # Connect the selection signal to the handler function
        self.serialNumberList.itemSelectionChanged.connect(self.serial_number_selected)    


    def open_image(self):
        """
        @brief Opens a file dialog to select multiple image files and displays the first in the label.

        """
        fnames, _ = QFileDialog.getOpenFileNames(self, 'Open file',
                                                 DEFAULT_FOLDER, "Image files (*.jpg *.gif *.png)")
        if fnames:
            self.selected_image_paths = fnames  # Save all selected file paths
            self.current_image_index = 0  # Reset index
            self.current_image_path = fnames[0]  # Select the first file to display
            self.preview_image(self.current_image_path)
            self.update_image_counter()  # Update the counter display


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

    def add_photos(self):
        """
        @brief Add the photos selected in the preview pane to the database. Record the entry in the database log

        Each photo is copied to the database folder specified in config settings, and the entry is recorded in the database log csv file.
        The details are pulled from the user selected fields in the GUI. The file name is generated according to the naming convention. 
        A warning is displayed if the file type already exists in the database or if a photo has not been selected, or if the serial number is invalid.
        """

        # Read the serial number and status from the GUI fields
        serial_number = self.snLineEdit.text()
        status = self.stausComboBox.currentText()

        # Validate the serial number and image, inform user if invalid
        if (not self.selected_image_paths or not self.validate_serial_number(serial_number)):
            QMessageBox.warning(self, "Warning", "No photo selected or serial number is invalid.")
            return

        # If the serial number is valid and photos are selected
        else:
            # Set the destination folder to reside in the database with the serial number as the folder name
            serial_number_folder = os.path.join(DATA_FOLDER, serial_number)
            status_folder = os.path.join(serial_number_folder, status)

            # Create the folder matching the serial number and status if they do not already exist
            os.makedirs(status_folder, exist_ok=True)

            successful_files = 0  # Count of successfully added images

            try:
                for index, image_path in enumerate(self.selected_image_paths):
                    # Update the current image path
                    self.current_image_path = image_path  
                    # Generate the file name according to naming convention
                    file_name = self.generate_file_name(serial_number, index)

                    # Create a save path
                    destination_file = os.path.join(status_folder, file_name)

                    # Try to add the image to the database
                    if self.add_image_database(serial_number, status, destination_file):
                        successful_files += 1
            except PermissionError:
                QMessageBox.critical(self, "Error", 
                                "Unable to write to the database file. Please close any other applications using it (e.g. Excel) and try again.")
                return
            else:
                # Display the final result
                QMessageBox.information(self, "Success", f"Added {successful_files} out of {len(self.selected_image_paths)} photos to the database.")
                # Refresh the recent serial numbers list
                self.refresh_serial_number_list()


    def add_image_database(self, serial_number, status, destination_file):
        """
        @brief Write a copy of the image to disk and add the details to the database log csv file.

        @returns True if the image was successfully added to the database, otherwise False
        """
        self.write_to_csv(serial_number, status, destination_file)

        # If the CSV file is writable, proceed with copying the image
        shutil.copy2(self.current_image_path, destination_file)
        return True
   

    def validate_serial_number(self, serial_number):
        """
        @brief Validates the serial number against any specific rules.

        """      
        # Replace this with more complex validation logic if needed
        return bool(serial_number and not serial_number.isspace())
    
    def generate_file_name(self, serial_number, index):
        """
        @brief Generates a file name according to the naming convention specifed for the database.

        """  
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        _, file_extension = os.path.splitext(self.current_image_path)  # Extract extension from the original file path
        file_name = f"{serial_number}_{timestamp}_{index}{file_extension}"
        return file_name

        
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

    def refresh_serial_number_list(self):
        """
        Refreshes the list of serial numbers from the data folder.
        """
        self.serialNumberList.clear()  # Clear the list
        folders = [name for name in os.listdir(DATA_FOLDER) if os.path.isdir(os.path.join(DATA_FOLDER, name))]
        self.serialNumberList.addItems(folders)  # Add each folder name to the list

    def serial_number_selected(self):
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
        if self.selected_image_paths:  # Only process keys if images have been loaded
            if event.key() == QtCore.Qt.Key_Right:
                self.go_next()
            elif event.key() == QtCore.Qt.Key_Left:
                self.go_previous()
            else:
                super().keyPressEvent(event)
                return


    def update_image_counter(self):
        """
        @brief Update a label on the UI to show the current image index and total images loaded.

        """
        # Assuming you have a QLabel named imageCounterLabel to display the counter
        self.imageCounterLabel.setText(f"Image {self.current_image_index + 1} of {len(self.selected_image_paths)}")

    def go_previous(self):
        """
        Go to the previous image.
        """
        self.current_image_index = max(self.current_image_index - 1, 0)
        # Update the current image and display it
        self.current_image_path = self.selected_image_paths[self.current_image_index]
        self.preview_image(self.current_image_path)
        self.update_image_counter()  # Update the counter display        

    def go_next(self):
        """
        Go to the next image.
        """
        self.current_image_index = min(self.current_image_index + 1, len(self.selected_image_paths) - 1)
        # Update the current image and display it
        self.current_image_path = self.selected_image_paths[self.current_image_index]
        self.preview_image(self.current_image_path)
        self.update_image_counter()  # Update the counter display





    
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
