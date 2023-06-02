import os
import sys
import json

# config.json should be located in the resources folder 

# The config file contains the following settings:
# default_folder: The image folder that is opened when the application is launched
# data_folder: The folder where the database images are copied to
# csv_data_file: The csv file where the database entries are stored
# UI_FILE: The path to the UI file created using Qt Designer
# ICON_FILE: The path to the icon file used for the application

def load_config():
  # If running as a PyInstaller package
  if getattr(sys, 'frozen', False):
    # Use the directory of the executable as the base path
    base_path = os.path.dirname(sys.executable)
  else:
    # Otherwise, use the directory of this script as the base path
    base_path = os.path.dirname(os.path.realpath(__file__))

  # Move up one directory from the base path
  parent_dir = os.path.dirname(base_path)
  config_path = os.path.join(parent_dir, 'resources', 'config.json')    

  with open(config_path) as f:
    config = json.load(f)

  config['UI_FILE'] = os.path.join(parent_dir, 'resources', 'photoBooth.ui')
  config['ICON_FILE'] = os.path.join(parent_dir, 'resources', 'trayicon.png')

  return config
