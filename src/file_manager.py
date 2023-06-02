import os
import csv
import datetime
import shutil

class FileManager:
  def __init__(self, config):
    self.default_folder = config['default_folder']
    self.save_folder = config['data_folder']
    self.log_file = config['csv_data_file']
    
  def add_photos(self, img_paths, module_data, move=False):
    """
    @brief Adds the given images to the database. The images are either moved or copied from the default folder 
    to the save folder depending on the 'move' parameter. The images are renamed according to the naming convention 
    specified for the database. The images are saved in the save folder in a subfolder named after the serial number.
    The images are also added to the CSV file.
    @param move If True, moves the images. If False or not provided, copies the images.
    """

    serial_number = module_data['serial_number']
    # Create a subfolder for the serial number if it does not exist
    serial_number_folder = os.path.join(self.save_folder, serial_number)
    os.makedirs(serial_number_folder, exist_ok=True)

    successful_files = 0  # Count of successfully added images

    # Copy or move the images from the default folder to the serial number folder
    for index, img_path in enumerate(img_paths):
      # Generate the new file name
      new_file_name = self.generate_file_name(img_path, serial_number, index)
      # Copy or move the file to the serial number folder
      destination_file = os.path.join(serial_number_folder, new_file_name)
      if move:
        shutil.move(img_path, destination_file)
      else:
        shutil.copy2(img_path, destination_file)
      # Write the entry to the CSV file
      self.write_to_csv(module_data, destination_file)
      successful_files += 1

    return successful_files
    
  def generate_file_name(self, source_image, serial_number, index):
    """
    @brief Generates a file name according to the naming convention specifed for the database.

    """  
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    _, file_extension = os.path.splitext(source_image)  # Extract extension from the original file path
    file_name = f"{serial_number}_{timestamp}_{index}{file_extension}"
    return file_name
    
  def write_to_csv(self, module_data, destination_file):
    """
    Write an entry to the CSV file. Each entry has the fields:
    date, time, serial number, status, comments, file save location
    If the file does not exist, creates a new one with headers.
    """

    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")        

    #Check if CSV file exists or needs to be made
    file_exists = os.path.isfile(self.log_file)

    # Add the entry to the CSV file
    with open(self.log_file, 'a', newline='') as f:
      writer = csv.writer(f)
      # If the file does not exist, write the headers
      if not file_exists:
        # Header format
        writer.writerow(["Date", "Time", 
                                 "Serial Number", 
                                 "Status", 
                                 "Comments", 
                                 "File Save Location"])
        # Entry format
      writer.writerow([date, time, 
                             module_data['serial_number'],  
                             module_data['status'], 
                             module_data['comments'], 
                             destination_file])

  def get_latest_file(self):
    """
    Returns the path of the latest (most recently modified) file of the default folder.
    If the directory does not exist or is empty, returns None.
    """
    if not os.path.exists(self.default_folder):
      return None
    files = os.listdir(self.default_folder)
    if not files:  # If the list is empty
      return None
    paths = [os.path.join(self.default_folder, basename) for basename in files]
    return max(paths, key=os.path.getctime)
    
  def get_most_recent_serial_numbers(self):
    """
    Refreshes the list of serial numbers from the data folder, sorted by most recently modified.
    """

    try:
      # Retrieve all folders in the directory
      folders = [name for name in os.listdir(self.save_folder) if os.path.isdir(os.path.join(self.save_folder, name))]
      # Sort folders by modification time in descending order
      folders.sort(key=lambda x: os.path.getmtime(os.path.join(self.save_folder, x)), reverse=True)
    except FileNotFoundError:
      folders = []
            
    # Take the 800 most recent folders (serial numbers)
    folders = folders[:50]
        
    return folders

  def get_default_folder(self):
    return self.default_folder   