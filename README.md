# Photo EXIF Organizer
Warning: most of this program was written by AI, I then cleaned it up and debugged it. I didn't like anything that was out there, so I figured I would just throw something together that would do exactly what I needed.

A Python utility that scans folders for images, reads their EXIF data using the exifread library, organizes them into a year/month folder structure, and provides advanced duplicate detection and handling capabilities.

## Features

- Scan multiple source folders for images
- Extract date information from image EXIF data (including RAW formats)
- Fallback to file modification date if EXIF data is unavailable
- Organize images into a year/month folder structure
- Detect and handle duplicate files based on content hash
- Add tag prefixes to filenames during organization
- Update existing folders with tag prefixes
- Preserve source directory structure when moving duplicates
- Skip hidden files (starting with .)
- Remove macOS resource fork files (._) at the end of processing
- Rerun mode to skip files that already exist in the destination
- Provide detailed statistics on processed, duplicate, and skipped files

## Requirements

- Python 3.x
- exifread library (for better RAW file support)
- Pillow library (for standard image formats)

## Usage

```bash
python image_organizer.py SOURCE_FOLDER [SOURCE_FOLDER ...] [OPTIONS]
```

### Arguments

- `SOURCE_FOLDER`: One or more folders containing images to organize (required)
- `-d, --destination`: Destination folder for organized images (default: ./organized_images)
- `-r, --rerun`: Skip copying files that already exist in the destination
- `-cd, --check-duplicates`: Check for duplicates in the source folder(s) without organizing
- `-m, --move-duplicates [DIR]`: Move duplicate files to specified directory (default: ./duplicates)
- `-t, --tag PREFIX`: Add specified prefix to filenames when organizing
- `-u, --update-folder FOLDER`: Update all image files in specified folder with the tag prefix

### Examples

Organize images from a single folder:
```bash
python image_organizer.py ~/Pictures
```

Organize images from multiple folders:
```bash
python image_organizer.py ~/Pictures ~/Downloads/Photos
```

Specify a custom destination folder:
```bash
python image_organizer.py ~/Pictures -d ~/OrganizedPhotos
```

Check for duplicates without organizing:
```bash
python image_organizer.py ~/Pictures -cd
```

Check for duplicates and move them to a specific folder:
```bash
python image_organizer.py ~/Pictures -cd -m ./my_duplicates
```

Add a tag prefix to filenames during organization:
```bash
python image_organizer.py ~/Pictures -t vacation
```

Update an existing folder with a tag prefix:
```bash
python image_organizer.py -u ~/OrganizedPhotos -t family
```

Skip files that already exist in the destination:
```bash
python image_organizer.py ~/Pictures -r
```

Combine multiple options:
```bash
python image_organizer.py ~/Pictures -d ~/OrganizedPhotos -t vacation -r
```

## How It Works

### Image Organization Mode

1. The program scans all files in the specified source folders
2. For each image file (based on file extension), it:
   - Extracts EXIF data using the exifread library to determine when the photo was taken
   - Falls back to file modification date if EXIF data is unavailable
   - Creates a folder structure based on year/month (e.g., 2023/05/)
   - Optionally adds a tag prefix to the filename
   - Copies the image to the appropriate folder
   - Detects duplicates based on file content hash
   - Handles duplicate file names by adding a numeric suffix
3. After processing, it removes any macOS resource fork files

### Duplicate Detection Mode

1. The program scans all files in the specified source folders
2. For each image file, it calculates a hash based on file content
3. It identifies duplicate files based on matching hashes
4. It displays all sets of duplicate files
5. If requested, it moves duplicates to a specified folder, preserving the source directory structure

### Tag Prefix Mode

1. The program scans all files in the specified folder
2. For each image file, it adds the specified prefix to the filename
3. It skips files that already have the specified prefix

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- WebP (.webp)
- RAW formats (.arw, .raw, .cr2, .nef, etc.) - supported via exifread library
