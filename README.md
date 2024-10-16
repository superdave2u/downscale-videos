# Video Downscaling Script

This Python script is designed to recursively downscale and compress video files in a given directory or for a single video file. It uses FFMPEG to process the video files and can adjust the resolution, framerate, audio bitrate, and compression settings to optimize video file sizes.

## Features

- **Resolution Downscaling**: Downscales videos to a specified resolution (default: 480p) if their height exceeds the given limit.
- **Framerate Adjustment**: Adjusts the video framerate to a set limit (default: 24 fps) if it exceeds the threshold.
- **Audio Compression**: Reduces the audio bitrate to a specified limit (default: 96 kbps).
- **Compression (CRF)**: Optionally applies FFMPEG's Constant Rate Factor (CRF) for compression to reduce file size.
- **Recursive Processing**: Can recursively process all videos in a directory.
- **File Preservation**: The original files are replaced by the processed versions if no errors occur.

## Requirements

The script requires the following dependencies:

- **FFMPEG**: This must be installed on your system and accessible via the command line.
- **Python 3**: The script requires Python 3.
- **MoviePy**: A Python library used to extract video information.

### Installing Required Packages

To install `moviepy`, you can use pip:

```bash
pip install moviepy
```

Ensure that FFMPEG is installed and available in your system's PATH. You can check if FFMPEG is installed by running:

```bash
ffmpeg -version
```

## Usage

### Basic Usage

To run the script, execute the following command:

```bash
python script.py <path> [options]
```

Here, `<path>` can be the path to a single video file or a directory containing video files.

### Options

- `--recursive`: Recursively process video files within subdirectories.
- `--audio`: Adjust the audio bitrate to the specified or default limit.
- `--video`: Downscale video resolution to the specified or default height limit.
- `--framerate`: Adjust the video framerate to the specified or default limit.
- `--compression`: Apply compression using FFMPEG's CRF (Constant Rate Factor).
- `--compression-factor <factor>`: Specify a custom compression factor (CRF). Defaults to 30 if not specified.
- `--height-limit <limit>`: Specify a custom resolution height limit. Defaults to 480.
- `--rate-limit <limit>`: Specify a custom framerate limit. Defaults to 24 fps.
- `--bitrate-limit <limit>`: Specify a custom audio bitrate limit in kbps. Defaults to 96 kbps.

### Examples

1. **Process a Single Video File:**

   ```bash
   python script.py /path/to/video.mp4
   ```

   This will check the video file for resolution, audio, and framerate, applying changes if needed.

2. **Process Videos Recursively in a Directory:**

   ```bash
   python script.py /path/to/directory
   ```

   This will process all video files in the specified directory and its subdirectories.

3. **Apply Compression (CRF) Without Changing Resolution or Framerate:**

   ```bash
   python script.py /path/to/video.mp4 --compression
   ```

   This will apply CRF compression to the video without altering its resolution or framerate.

4. **Specify Custom Compression Factor:**

   ```bash
   python script.py /path/to/video.mp4 --compression --compression-factor 25
   ```

   This will apply CRF compression with a factor of 25.

5. **Change Audio Bitrate Limit and Resolution:**

   ```bash
   python script.py /path/to/video.mp4 --audio --video --bitrate-limit 128 --height-limit 720
   ```

   This will adjust the video resolution to 720p if the original resolution is higher and limit the audio bitrate to 128 kbps.

## Logging

The script uses Python's logging module to display information about the process, including:

- Videos being processed
- Changes being applied (e.g., resolution, framerate, audio compression)
- Errors encountered during processing

## Error Handling

The script will skip a video if it encounters an error during processing and will log the error message. It will continue processing the remaining videos in the directory if the `--recursive` option is used.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
