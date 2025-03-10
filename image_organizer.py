#!/usr/bin/env python3
"""
Image Organizer - Scans folders for images, reads EXIF data, and organizes them by year/month.
Detects and handles duplicate files by moving them to a separate folder.
"""

import os
import sys
import shutil
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS


def get_exif_data(image_path):
    """Extract EXIF data from an image file."""
    try:
        image = Image.open(image_path)
        exif_data = {}
        
        if hasattr(image, '_getexif'):
            exif_info = image._getexif()
            if exif_info:
                for tag, value in exif_info.items():
                    decoded = TAGS.get(tag, tag)
                    exif_data[decoded] = value
        
        return exif_data
    except Exception as e:
        print(f"Error reading EXIF data from {image_path}: {e}")
        return {}


def get_date_from_exif(exif_data):
    """Extract the date from EXIF data."""
    # Try different date fields in EXIF data
    date_fields = ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']
    
    for field in date_fields:
        if field in exif_data:
            try:
                # EXIF date format: 'YYYY:MM:DD HH:MM:SS'
                date_str = exif_data[field]
                date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                return date_obj
            except Exception as e:
                print(f"Error parsing date {exif_data[field]}: {e}")
    
    return None


def get_date_from_file(file_path):
    """Get the file's modification date if EXIF data is not available."""
    try:
        mod_time = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mod_time)
    except Exception as e:
        print(f"Error getting file date for {file_path}: {e}")
        return datetime.now()


def is_image_file(file_path):
    """Check if the file is an image based on its extension.
    Ignores files that start with a dot (hidden files)."""
    # Ignore files that start with a dot (hidden files)
    if Path(file_path).name.startswith('.'):
        return False
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    return Path(file_path).suffix.lower() in image_extensions


def get_file_hash(file_path):
    """Calculate MD5 hash of a file to identify duplicates."""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            # Read the file in chunks to handle large files efficiently
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)
        return file_hash.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None


def organize_images(source_folder, destination_folder):
    """Scan for images and organize them into year/month folders.
    Detect duplicates and move them to a duplicates folder."""
    source_path = Path(source_folder)
    destination_path = Path(destination_folder)
    duplicates_path = destination_path / 'duplicates'
    
    if not source_path.exists():
        print(f"Source folder '{source_folder}' does not exist.")
        return
    
    # Create destination folder if it doesn't exist
    destination_path.mkdir(parents=True, exist_ok=True)
    duplicates_path.mkdir(parents=True, exist_ok=True)
    
    # Counter for statistics
    processed_count = 0
    duplicate_count = 0
    skipped_count = 0
    
    # Dictionary to store file hashes to detect duplicates
    file_hashes = {}
    
    # Walk through the source directory
    for root, _, files in os.walk(source_path):
        for file in files:
            file_path = Path(root) / file
            
            if is_image_file(file_path):
                try:
                    # Calculate file hash for duplicate detection
                    file_hash = get_file_hash(file_path)
                    if not file_hash:
                        print(f"Skipping {file_path} - could not calculate hash")
                        skipped_count += 1
                        continue
                    
                    # Get EXIF data
                    exif_data = get_exif_data(file_path)
                    
                    # Try to get date from EXIF data, fall back to file date
                    date = get_date_from_exif(exif_data) or get_date_from_file(file_path)
                    
                    # Check if this is a duplicate file
                    if file_hash in file_hashes:
                        # This is a duplicate - move to duplicates folder
                        original_path = file_hashes[file_hash]
                        dup_dest_path = duplicates_path / f"{date.year}_{date.month:02d}_{file_path.name}"
                        
                        # If the duplicate file already exists, add a suffix
                        if dup_dest_path.exists():
                            base_name = dup_dest_path.stem
                            extension = dup_dest_path.suffix
                            counter = 1
                            
                            while dup_dest_path.exists():
                                new_name = f"{base_name}_{counter}{extension}"
                                dup_dest_path = duplicates_path / new_name
                                counter += 1
                        
                        # Copy the duplicate file to the duplicates folder
                        shutil.copy2(file_path, dup_dest_path)
                        print(f"Duplicate found: {file_path}")
                        print(f"  Original: {original_path}")
                        print(f"  Saved to: {dup_dest_path}")
                        duplicate_count += 1
                    else:
                        # This is a new file - organize it normally
                        # Create year/month folder structure
                        year_folder = destination_path / str(date.year)
                        month_folder = year_folder / f"{date.month:02d}"
                        
                        # Create folders if they don't exist
                        month_folder.mkdir(parents=True, exist_ok=True)
                        
                        # Destination file path
                        dest_file_path = month_folder / file_path.name
                        
                        # Check if a file with the same name already exists at destination
                        if dest_file_path.exists():
                            # Add a suffix to avoid overwriting
                            base_name = dest_file_path.stem
                            extension = dest_file_path.suffix
                            counter = 1
                            
                            while dest_file_path.exists():
                                new_name = f"{base_name}_{counter}{extension}"
                                dest_file_path = month_folder / new_name
                                counter += 1
                        
                        # Copy the file
                        shutil.copy2(file_path, dest_file_path)
                        print(f"Copied: {file_path} -> {dest_file_path}")
                        processed_count += 1
                        
                        # Store the hash and path for future duplicate detection
                        file_hashes[file_hash] = dest_file_path
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    skipped_count += 1
            else:
                skipped_count += 1
    
    print(f"\nProcessing complete!")
    print(f"Images processed: {processed_count}")
    print(f"Duplicates found: {duplicate_count}")
    print(f"Files skipped: {skipped_count}")


def main():
    """Main function to parse arguments and start the process."""
    parser = argparse.ArgumentParser(description='Organize images into year/month folders based on EXIF data and handle duplicates.')
    parser.add_argument('source', nargs='+', help='Source folder(s) containing images')
    parser.add_argument('-d', '--destination', default='./organized_images',
                        help='Destination folder for organized images (default: ./organized_images)')
    
    args = parser.parse_args()
    
    # Process each source folder
    for source_folder in args.source:
        print(f"\nProcessing folder: {source_folder}")
        organize_images(source_folder, args.destination)


if __name__ == '__main__':
    main()
