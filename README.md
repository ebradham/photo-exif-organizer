# Image Organizer
Warning: most of this program was written by AI, I then cleaned it up and debugged it.  I didn't like anything that was out there, so I figured I would just throw something together that would do exactly what I needed.

A Python utility that scans folders for images, reads their EXIF data using the Pillow library, and organizes them into a year/month folder structure.

## Features

- Scan multiple source folders for images
- Extract date information from image EXIF data
- Fallback to file modification date if EXIF data is unavailable
- Organize images into a year/month folder structure
- Prevent file name conflicts by adding a suffix to duplicate file names
- Provide statistics on processed and skipped files

## Requirements

- Python 3.x
- Pillow library (already installed)

## Usage

```bash
python image_organizer.py SOURCE_FOLDER [SOURCE_FOLDER ...] [-d DESTINATION_FOLDER]
```

### Arguments

- `SOURCE_FOLDER`: One or more folders containing images to organize (required)
- `-d, --destination`: Destination folder for organized images (default: ./organized_images)

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

## How It Works

1. The program scans all files in the specified source folders
2. For each image file (based on file extension), it:
   - Extracts EXIF data to determine when the photo was taken
   - Falls back to file modification date if EXIF data is unavailable
   - Creates a folder structure based on year/month (e.g., 2023/05/)
   - Copies the image to the appropriate folder
   - Handles duplicate file names by adding a numeric suffix

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff)
- WebP (.webp)
