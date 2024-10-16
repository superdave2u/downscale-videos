import os
import sys
import subprocess
import logging
import mimetypes
import re
import time
from moviepy.editor import VideoFileClip

# Default values for video processing
FRAME_HEIGHT_LIMIT = 480
FRAME_RATE_LIMIT = 24
AUDIO_BITRATE_LIMIT = 96  # In kbps

CONSTANT_RATE_FACTOR = 30

# Configure Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Helper: Get video file statistics
def get_video_stats(file_path):
    try:
        with VideoFileClip(file_path) as clip:
            return {
                "size": os.path.getsize(file_path),
                "fps": clip.fps,
                "resolution": clip.size,
                "height": clip.size[1],
                "bitrate": get_audio_bitrate(file_path),
            }
    except Exception as e:
        logging.error(f"Error getting stats for {file_path}: {e}")
        return None


# Helper: Get audio bitrate using ffprobe
def get_audio_bitrate(file_path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=bit_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        return int(result.stdout.strip()) // 1000  # Convert from bps to kbps
    except Exception as e:
        logging.error(f"Error getting audio bitrate for {file_path}: {e}")
        return None


# Helper: Determine needed changes
def determine_changes(
    stats,
    process_audio,
    process_framerate,
    process_resolution,
    frame_height_limit,
    frame_rate_limit,
    audio_bitrate_limit,
):
    changes = []

    if process_resolution and stats["height"] > frame_height_limit:
        changes.append("Resolution")

    # Only compare audio bitrate if it is not None
    if (
        process_audio
        and stats["bitrate"] is not None
        and stats["bitrate"] > audio_bitrate_limit
    ):
        changes.append("Audio")

    if process_framerate and stats["fps"] > frame_rate_limit:
        changes.append("Framerate")

    return changes


# Helper: Build FFMPEG command based on changes
def build_ffmpeg_command(
    input_file,
    output_file,
    changes,
    compression,
    compression_factor,
    frame_height_limit,
    frame_rate_limit,
    audio_bitrate_limit,
):
    command = ["ffmpeg", "-y", "-i", input_file, "-map_metadata", "0"]

    if "Resolution" in changes:
        command += [
            "-vf",
            f"scale=-2:'min({frame_height_limit},ih)'",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
        ]
    elif compression:
        command += ["-vf", "scale=iw:ih", "-c:v", "libx264", "-preset", "ultrafast"]

    if compression:
        command += ["-crf", str(compression_factor)]

    if "Framerate" in changes:
        command += ["-r", str(frame_rate_limit)]

    if "Audio" in changes:
        command += ["-c:a", "aac", "-b:a", f"{audio_bitrate_limit}k"]
    else:
        command += ["-c:a", "copy"]  # Copy audio if no changes

    command.append(output_file)
    return command


# Main logic to process videos
def process_video(
    file_path,
    process_audio,
    process_framerate,
    process_resolution,
    compression,
    compression_factor,
    frame_height_limit,
    frame_rate_limit,
    audio_bitrate_limit,
):
    try:
        logging.info(f"Checking {os.path.basename(file_path)}...")

        # Gather statistics about the video
        stats = get_video_stats(file_path)
        if not stats:
            logging.warning(
                f"Skipping {os.path.basename(file_path)} due to error in fetching stats."
            )
            return

        # Determine what needs to change
        changes = determine_changes(
            stats,
            process_audio,
            process_framerate,
            process_resolution,
            frame_height_limit,
            frame_rate_limit,
            audio_bitrate_limit,
        )

        if not changes and not compression:
            logging.info(f"No changes needed for {os.path.basename(file_path)}.")
            return

        # Output what is being applied
        logging.info(
            f"Processing {os.path.basename(file_path)}: {', '.join(changes)}{' + Compression' if compression else ''}"
        )

        output_file = get_output_file_path(file_path)
        command = build_ffmpeg_command(
            file_path,
            output_file,
            changes,
            compression,
            compression_factor,
            frame_height_limit,
            frame_rate_limit,
            audio_bitrate_limit,
        )

        execute_ffmpeg_command(command, get_total_frame_count(file_path))
        replace_original_with_resized(file_path, output_file)

    except Exception as e:
        logging.error(f"Error processing {os.path.basename(file_path)}: {e}")
        # Continue with the next file if an error occurs


# Helper: Get the total frame count of a video
def get_total_frame_count(file_path):
    with VideoFileClip(file_path) as video:
        return int(video.fps * video.duration)


# Execute FFMPEG command
def execute_ffmpeg_command(command, total_frames):
    start_time = time.time()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )
    frame_pattern = re.compile(r"frame=\s*(\d+)")

    for line in iter(process.stdout.readline, ""):
        match = frame_pattern.search(line)
        if match:
            current_frame = int(match.group(1))
            progress = (current_frame / total_frames) * 100
            elapsed_time = format_elapsed_time(time.time() - start_time)
            print(
                f"\rProcessing: {progress:.2f}% - Elapsed time: {elapsed_time}", end=""
            )

    process.stdout.close()
    if process.wait() != 0:
        logging.error(f"FFMPEG failed with return code {process.returncode}")
        raise subprocess.CalledProcessError(process.returncode, command)
    print()


# Format time in hh:mm:ss
def format_elapsed_time(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


# Replace original file with resized output
def replace_original_with_resized(original_file, resized_file):
    os.remove(original_file)
    time.sleep(1)
    os.rename(resized_file, original_file)


# Helper: Generate output file path
def get_output_file_path(input_file):
    directory, filename = os.path.split(input_file)
    filename_without_extension, extension = os.path.splitext(filename)
    return os.path.join(directory, f"{filename_without_extension}_resized{extension}")


# Helper to extract limit arguments from argv
def get_limit_from_argv(flag, default_value):
    try:
        if flag in sys.argv:
            return int(sys.argv[sys.argv.index(flag) + 1])
    except (IndexError, ValueError):
        pass
    return default_value


# Process directory
def process_directory(
    directory,
    recursive,
    process_audio,
    process_framerate,
    process_resolution,
    compression,
    compression_factor,
    frame_height_limit,
    frame_rate_limit,
    audio_bitrate_limit,
):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if is_video_file_mimetypes(file_path):
                process_video(
                    file_path,
                    process_audio,
                    process_framerate,
                    process_resolution,
                    compression,
                    compression_factor,
                    frame_height_limit,
                    frame_rate_limit,
                    audio_bitrate_limit,
                )
        if not recursive:
            break


# Check if the file is a video
def is_video_file_mimetypes(filepath):
    mimetype, _ = mimetypes.guess_type(filepath)
    return mimetype is not None and mimetype.startswith("video/")


def main():
    if len(sys.argv) < 2:
        logging.error(
            "Usage: python script.py <path> [--recursive] [--audio] [--video] [--framerate] [--compression] [--compression-factor <factor>] [--height-limit <limit>] [--rate-limit <limit>] [--bitrate-limit <limit>]"
        )
        sys.exit(1)

    path = sys.argv[1]
    recursive = "--recursive" in sys.argv
    process_audio = "--audio" in sys.argv
    process_resolution = "--video" in sys.argv
    process_framerate = "--framerate" in sys.argv
    compression = "--compression" in sys.argv

    # Default processing if no options provided
    if not (process_audio or process_resolution or process_framerate):
        process_audio = process_resolution = process_framerate = True

    # Get limits and overrides
    frame_height_limit = get_limit_from_argv("--height-limit", FRAME_HEIGHT_LIMIT)
    frame_rate_limit = get_limit_from_argv("--rate-limit", FRAME_RATE_LIMIT)
    audio_bitrate_limit = get_limit_from_argv("--bitrate-limit", AUDIO_BITRATE_LIMIT)
    compression_factor = get_limit_from_argv(
        "--compression-factor", CONSTANT_RATE_FACTOR
    )

    # Process files or directories
    if os.path.isfile(path) and is_video_file_mimetypes(path):
        process_video(
            path,
            process_audio,
            process_framerate,
            process_resolution,
            compression,
            compression_factor,
            frame_height_limit,
            frame_rate_limit,
            audio_bitrate_limit,
        )
    elif os.path.isdir(path):
        process_directory(
            path,
            recursive,
            process_audio,
            process_framerate,
            process_resolution,
            compression,
            compression_factor,
            frame_height_limit,
            frame_rate_limit,
            audio_bitrate_limit,
        )
    else:
        logging.error(f"Invalid path or unsupported file format: {path}")


if __name__ == "__main__":
    main()
