import os
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap


class ImagePane():
  """
  This class encapsulates all operations related to managing and displaying images in PhotoBooth.
  It is responsible for loading images from a directory, displaying them in the preview pane,
  and allowing the user to navigate through the images.
  """
  def __init__(self, init_file, image_preview_label, image_counter_label, current_file_label):
    self.image_preview_label = image_preview_label
    self.image_counter_label = image_counter_label
    self.fpCurrentFileLabel = current_file_label

    self.selected_image_paths = []
    self.current_image_index = 0

    # Load the initial image if one was specified
    if init_file:
      self.selected_image_paths = [init_file] 

  def load_images(self, image_paths):
    # Convert single image path to list if necessary
    if isinstance(image_paths, str):
      image_paths = [image_paths]

    # Set the selected image paths and reset the current image index
    self.selected_image_paths = image_paths
    self.current_image_index = 0
    # Update the current image and display it
    self.show_image()
 
  def show_image(self):
    """
    @brief Sets the image in the preview label to the image specified by the path.
    The image is scaled to fit the label. Updates the file name label and image counter label.
    """
    try:
      image_path = self.selected_image_paths[self.current_image_index]
      # Convert the image to a format that can be displayed by Qt
      pixmap = QPixmap(image_path)
      scaled_pixmap = pixmap.scaled(self.image_preview_label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
      # Set the image in the preview label
      self.image_preview_label.setPixmap(scaled_pixmap)
      # Update the current file label (displays the file name currently in preview pane)
      self.fpCurrentFileLabel.setText(os.path.basename(image_path))
      # Update the image counter label
      self.update_image_counter()
    except IndexError:  # Handles out of range index
      pass  # Maybe you want to display a default image or clear the current image
    except TypeError:  # Handles case where selected_image_paths is None
      pass  # Maybe you want to display a default image or clear the current image

  def update_image_counter(self):
    """
    @brief Update a label on the UI to show the current image index and total images loaded.
    """
    self.image_counter_label.setText(f"Image {self.current_image_index + 1} of {len(self.selected_image_paths)}")

  def go_previous(self):
    """
    Go to the previous image.
    """
    self.current_image_index = max(self.current_image_index - 1, 0)
    self.show_image()

  def go_next(self):
    """
    Go to the next image.
    """
    self.current_image_index = min(self.current_image_index + 1, len(self.selected_image_paths) - 1)
    self.show_image()

  def images_loaded(self):
    """
    @brief Checks if any images have been loaded for previewing

    @returns True if there are any loaded images, otherwise False
    """
    return bool(self.selected_image_paths)
 
  def refresh(self):
    """
    @brief Refreshes the preview pane to display the current image.
    """
    self.show_image()

  def get_current_image_paths(self):
    """
    @brief Gets the paths of the images currently loaded for previewing.

    @returns A list of image paths
    """
    return self.selected_image_paths

