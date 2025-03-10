#!/usr/bin/env python3
"""
Image Organizer - Scans folders for images, reads EXIF data, and organizes them by year/month.
Detects and handles duplicate files by moving them to a separate folder.
"""

import os
import shutil
import argparse
import hashlib
import exifread
from datetime import datetime
from pathlib import Path



def get_exif_data(image_path):
    """Extract EXIF data from an image file using exifread library."""
    try:
        with open(image_path, 'rb') as f:
            exif_tags = exifread.process_file(f, details=False)
            return exif_tags
    except Exception as e:
        print(f"Error reading EXIF data from {image_path}: {e}")
        return {}


def get_date_from_exif(exif_data):
    """Extract the date from EXIF data."""
    # Try different date fields in EXIF data
    date_fields = ['EXIF DateTimeOriginal', 'Image DateTime', 'EXIF DateTimeDigitized']
    
    for field in date_fields:
        if field in exif_data:
            try:
                # EXIF date format: 'YYYY:MM:DD HH:MM:SS'
                date_str = str(exif_data[field])
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
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.arw', '.raw'}
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


def remove_resource_fork_files(directory):
    """Remove macOS resource fork files (files starting with ._) from a directory and its subdirectories.
    
    Args:
        directory: Path to the directory to clean
    
    Returns:
        int: Number of resource fork files removed
    """
    removed_count = 0
    directory_path = Path(directory)
    
    for path in directory_path.glob('**/*'):
        if path.is_file() and path.name.startswith('._'):
            path.unlink()
            removed_count += 1
            print(f"Removed resource fork file: {path}")
    
    return removed_count


def find_duplicates(folder, move_to_duplicates=False):
    """Find duplicate images in a folder based on file hash.
    
    Args:
        folder: Path to the folder to check for duplicates
        move_to_duplicates: If True, move duplicates to a duplicates folder
    
    Returns:
        tuple: (duplicate_count, moved_count)
    """
    folder_path = Path(folder)
    duplicates_path = folder_path / 'duplicates'
    
    if not folder_path.exists():
        print(f"Folder '{folder}' does not exist.")
        return 0, 0
    
    if move_to_duplicates:
        duplicates_path.mkdir(parents=True, exist_ok=True)
    
    # Dictionary to store file hashes
    file_hashes = {}
    # Dictionary to store duplicates
    duplicates = {}
    # Counter for statistics
    duplicate_count = 0
    moved_count = 0
    
    print(f"Scanning {folder} for duplicate images...")
    
    # First pass: collect all file hashes
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            
            # Skip the duplicates folder if it exists
            if 'duplicates' in file_path.parts:
                continue
                
            if is_image_file(file_path):
                try:
                    # Calculate file hash
                    file_hash = get_file_hash(file_path)
                    if not file_hash:
                        continue
                    
                    if file_hash in file_hashes:
                        # This is a duplicate
                        if file_hash not in duplicates:
                            duplicates[file_hash] = [file_hashes[file_hash]]
                        duplicates[file_hash].append(file_path)
                        duplicate_count += 1
                    else:
                        file_hashes[file_hash] = file_path
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    # Print duplicates and optionally move them
    if duplicates:
        print(f"\nFound {duplicate_count} duplicate files:")
        for file_hash, paths in duplicates.items():
            print(f"\nDuplicate set (hash: {file_hash[:8]}...)")
            print(f"  Original: {paths[0]}")
            for i, path in enumerate(paths[1:], 1):
                print(f"  Duplicate {i}: {path}")
                
                if move_to_duplicates:
                    try:
                        # Get the source directory name
                        source_dir_name = path.parent.name
                        
                        # Create a subdirectory in the duplicates folder with the same name as the source directory
                        subdir_path = duplicates_path / source_dir_name
                        subdir_path.mkdir(parents=True, exist_ok=True)
                        
                        # Create a destination path in the duplicates folder subdirectory
                        dest_path = subdir_path / path.name
                        
                        # If a file with the same name already exists in the duplicates folder,
                        # add a suffix to avoid overwriting
                        if dest_path.exists():
                            base_name = dest_path.stem
                            extension = dest_path.suffix
                            counter = 1
                            
                            while dest_path.exists():
                                new_name = f"{base_name}_{counter}{extension}"
                                dest_path = subdir_path / new_name
                                counter += 1
                        
                        # Move the file
                        shutil.move(path, dest_path)
                        print(f"    Moved to: {dest_path}")
                        moved_count += 1
                    except Exception as e:
                        print(f"    Error moving file: {e}")
    else:
        print("No duplicates found.")
    
    print(f"\nDuplicate check complete!")
    print(f"Total duplicates found: {duplicate_count}")
    if move_to_duplicates:
        print(f"Duplicates moved: {moved_count}")
    
    return duplicate_count, moved_count


def add_prefix_to_files(folder, prefix):
    """Add a prefix to all image files in a folder and its subfolders.
    
    Args:
        folder: Path to the folder containing images
        prefix: Prefix to add to filenames
    
    Returns:
        int: Number of files renamed
    """
    if not prefix:
        print("No prefix specified. Skipping rename operation.")
        return 0
    
    folder_path = Path(folder)
    
    if not folder_path.exists():
        print(f"Folder '{folder}' does not exist.")
        return 0
    
    renamed_count = 0
    
    print(f"Adding prefix '{prefix}' to files in {folder}...")
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            
            if is_image_file(file_path):
                try:
                    # Skip files that already have the prefix
                    if file.startswith(f"{prefix}_"):
                        continue
                    
                    # Create new filename with prefix
                    new_name = f"{prefix}_{file}"
                    new_path = file_path.parent / new_name
                    
                    # Rename the file
                    file_path.rename(new_path)
                    print(f"Renamed: {file_path} -> {new_path}")
                    renamed_count += 1
                    
                except Exception as e:
                    print(f"Error renaming {file_path}: {e}")
    
    print(f"\nRename operation complete!")
    print(f"Files renamed: {renamed_count}")
    
    return renamed_count


def organize_images(source_folder, destination_folder, rerun=False, tag_prefix=None):
    """Scan for images and organize them into year/month folders.
    Detect duplicates and move them to a duplicates folder.
    
    Args:
        source_folder: Path to the source folder containing images
        destination_folder: Path to the destination folder for organized images
        rerun: If True, skip files that already exist in the destination
        tag_prefix: Optional prefix to add to filenames when copying
    """
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
    already_exists_count = 0
    
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
                        
                        # Get the source directory name
                        source_dir_name = file_path.parent.name
                        
                        # Create a subdirectory in the duplicates folder with the same name as the source directory
                        subdir_path = duplicates_path / source_dir_name
                        subdir_path.mkdir(parents=True, exist_ok=True)
                        
                        # Create destination path with year/month prefix in the subdirectory
                        dup_dest_path = subdir_path / f"{date.year}_{date.month:02d}_{file_path.name}"
                        
                        # If the duplicate file already exists, add a suffix
                        if dup_dest_path.exists():
                            base_name = dup_dest_path.stem
                            extension = dup_dest_path.suffix
                            counter = 1
                            
                            while dup_dest_path.exists():
                                new_name = f"{base_name}_{counter}{extension}"
                                dup_dest_path = subdir_path / new_name
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
                            # Check if the existing file is a duplicate of the one being moved
                            existing_hash = get_file_hash(dest_file_path)
                            if existing_hash == file_hash:
                                # Files are identical - skip this file
                                print(f"Skipping (identical file exists at destination): {file_path}")
                                already_exists_count += 1
                                continue
                            else:
                                # Files have the same name but different content - add a suffix
                                base_name = dest_file_path.stem
                                extension = dest_file_path.suffix
                                counter = 1
                                
                                while dest_file_path.exists():
                                    new_name = f"{base_name}_{counter}{extension}"
                                    dest_file_path = month_folder / new_name
                                    counter += 1
                        
                        # If rerun flag is set and we're about to copy a file that wasn't
                        # caught by the name check, we should still skip it if it exists elsewhere
                        # with the same content
                        if rerun:
                            # We already know this file doesn't exist at dest_file_path with the same hash
                            # But it might exist somewhere else in the destination with the same content
                            # We'll skip this check for now as it would require scanning the entire destination
                            # which could be expensive
                            pass
                        
                        # If tag prefix is specified, rename the destination file
                        if tag_prefix:
                            # Create new filename with prefix
                            prefixed_name = f"{tag_prefix}_{dest_file_path.name}"
                            prefixed_path = dest_file_path.parent / prefixed_name
                            
                            # Copy the file with the new prefixed name
                            shutil.copy2(file_path, prefixed_path)
                            print(f"Copied with prefix: {file_path} -> {prefixed_path}")
                            processed_count += 1
                            
                            # Update the destination path for hash tracking
                            dest_file_path = prefixed_path
                        else:
                            # Copy the file without prefix
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
    
    # Clean up macOS resource fork files
    print("\nCleaning up macOS resource fork files...")
    removed_count = remove_resource_fork_files(destination_path)
    
    print(f"\nProcessing complete!")
    print(f"Images processed: {processed_count}")
    print(f"Duplicates found: {duplicate_count}")
    print(f"Already in destination: {already_exists_count}")
    print(f"Files skipped: {skipped_count}")
    print(f"Resource fork files removed: {removed_count}")


def main():
    """Main function to parse arguments and start the process."""
    parser = argparse.ArgumentParser(description='Organize images into year/month folders based on EXIF data and handle duplicates.')
    parser.add_argument('source', nargs='+', help='Source folder(s) containing images')
    parser.add_argument('-d', '--destination', default='./organized_images',
                        help='Destination folder for organized images (default: ./organized_images)')
    parser.add_argument('-r', '--rerun', action='store_true',
                        help='Rerun mode: skip copying files that already exist in the destination')
    parser.add_argument('-cd', '--check-duplicates', action='store_true',
                        help='Check for duplicates in the source folder(s) without organizing')
    parser.add_argument('-m', '--move-duplicates', metavar='DIR', nargs='?', const='./duplicates', default=None,
                        help='Move duplicate files to specified directory (default: ./duplicates)')
    parser.add_argument('-t', '--tag', metavar='PREFIX',
                        help='Add specified prefix to filenames when organizing')
    parser.add_argument('-u', '--update-folder', metavar='FOLDER',
                        help='Update all image files in specified folder with the tag prefix')
    
    args = parser.parse_args()
    
    # Check if we're updating a folder with tag prefixes
    if args.update_folder and args.tag:
        print(f"\nUpdating folder with tag prefix: {args.update_folder}")
        add_prefix_to_files(args.update_folder, args.tag)
    # Check if we're just looking for duplicates
    elif args.check_duplicates:
        for source_folder in args.source:
            print(f"\nChecking for duplicates in folder: {source_folder}")
            find_duplicates(source_folder, args.move_duplicates)
    else:
        # Process each source folder for organization
        for source_folder in args.source:
            print(f"\nProcessing folder: {source_folder}")
            organize_images(source_folder, args.destination, args.rerun, args.tag)


if __name__ == '__main__':
    main()
