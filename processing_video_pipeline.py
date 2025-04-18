#!/usr/bin/env python3
import os
import argparse
import subprocess
import glob
import sys
import re
import json
from pathlib import Path


def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command execution error: {e}")
        print(f"Error output: {e.stderr}")
        return None


def process_single_file(video_path, args):
    video_filename = os.path.basename(video_path)
    base_name = os.path.splitext(video_filename)[0]

    print(f"\n{'=' * 50}")
    print(f"Processing file: {video_filename}")
    print(f"{'=' * 50}")

    # Step 1: Extract audio
    print(f"\n[Step 1/6] Extracting audio from video {video_filename}...")
    extract_cmd = [sys.executable, "cli.py", "extract_audio", "--input", video_path]
    extract_output = run_command(extract_cmd)

    # Parse the output to get the audio file path
    audio_path = None
    if extract_output:
        match = re.search(r"saved in file: (.*?)$", extract_output, re.MULTILINE)
        if match:
            audio_path = match.group(1).strip()
        else:
            match = re.search(r"Audio successfully extracted: (.*?)$", extract_output, re.MULTILINE)
            if match:
                audio_path = match.group(1).strip()

    if not audio_path or not os.path.exists(audio_path):
        print(f"Error: Audio file was not created or not found.")
        return False

    print(f"Audio file created: {audio_path}")

    # Step 2: Transcription
    print(f"\n[Step 2/6] Transcribing audio {os.path.basename(audio_path)}...")
    transcribe_cmd = [sys.executable, "cli.py", "transcribe", "--input", audio_path]
    transcribe_output = run_command(transcribe_cmd)

    transcription_path = None
    if transcribe_output:
        match = re.search(r"saved in file: (.*?)$", transcribe_output, re.MULTILINE)
        if match:
            transcription_path = match.group(1).strip()
        else:
            match = re.search(r"Result: (.*?)$", transcribe_output, re.MULTILINE)
            if match:
                transcription_path = match.group(1).strip()

    if not transcription_path or not os.path.exists(transcription_path):
        print(f"Error: Transcription file was not created or not found.")
        return False

    print(f"Transcription file created: {transcription_path}")

    print(f"\n[Step 3/6] Structuring transcription {os.path.basename(transcription_path)}...")
    correct_cmd = [sys.executable, "cli.py", "correct", "--input", transcription_path]

    if args.start_timestamp is not None:
        correct_cmd.extend(["--start_timestamp", str(args.start_timestamp)])

    correct_output = run_command(correct_cmd)

    # Parse the output to get the corrected file path
    corrected_path = None
    if correct_output:
        match = re.search(r"saved in file: (.*?)$", correct_output, re.MULTILINE)
        if match:
            corrected_path = match.group(1).strip()

    if not corrected_path or not os.path.exists(corrected_path):
        print(f"Error: Corrected transcription file was not created or not found.")
        return False

    print(f"Corrected transcription file created: {corrected_path}")

    # Step 4: Clean transcription
    print(f"\n[Step 4/6] Cleaning transcription {os.path.basename(corrected_path)}...")
    cleanup_cmd = [sys.executable, "cli.py", "cleanup", "--input", corrected_path]
    cleanup_output = run_command(cleanup_cmd)

    cleaned_path = None
    if cleanup_output:
        match = re.search(r"saved in file: (.*?)$", cleanup_output, re.MULTILINE)
        if match:
            cleaned_path = match.group(1).strip()

    if not cleaned_path or not os.path.exists(cleaned_path):
        print(f"Error: Cleaned transcription file was not created or not found.")
        return False

    print(f"Cleaned transcription file created: {cleaned_path}")

    # Step 5: Optimize segments
    print(f"\n[Step 5/6] Optimizing segments in transcription {os.path.basename(cleaned_path)}...")
    optimize_cmd = [sys.executable, "cli.py", "optimize-segments", "--input", cleaned_path]
    optimize_output = run_command(optimize_cmd)

    optimized_path = None
    if optimize_output:
        match = re.search(r"saved in file: (.*?)$", optimize_output, re.MULTILINE)
        if match:
            optimized_path = match.group(1).strip()

    if not optimized_path or not os.path.exists(optimized_path):
        print(f"Error: Optimized transcription file was not created or not found.")
        return False

    print(f"Optimized transcription file created: {optimized_path}")

    # Step 6: Adjust timing
    print(f"\n[Step 6/6] Adjusting segment timing in transcription {os.path.basename(optimized_path)}...")
    adjust_cmd = [sys.executable, "cli.py", "adjust_timing", "--input", optimized_path]
    adjust_output = run_command(adjust_cmd)

    adjusted_path = None
    if adjust_output:
        match = re.search(r"saved in file: (.*?)$", adjust_output, re.MULTILINE)
        if match:
            adjusted_path = match.group(1).strip()

    if not adjusted_path or not os.path.exists(adjusted_path):
        print(f"Error: Adjusted transcription file was not created or not found.")
        return False

    print(f"Adjusted transcription file created: {adjusted_path}")

    print(f"\nProcessing of file {video_filename} completed successfully!")
    print(f"Final result saved to {adjusted_path}")
    print(f"To translate, use the command:")
    print(f"python cli.py translate --input {adjusted_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Automatic video processing (first 6 stages): "
                                                 "audio extraction, transcription, correction, cleaning, "
                                                 "optimization, and timing adjustment")

    parser.add_argument("--input", "-i", help="Path to video file or directory with videos")
    parser.add_argument("--start_timestamp", "-st", type=float,
                        help="Set start time for the first segment (e.g., 0.0)")

    args = parser.parse_args()

    # If path is not specified, use "video_input" directory
    if not args.input:
        args.input = "video_input"

    # Determine if a file or directory is specified
    if os.path.isdir(args.input):
        print(f"Processing all videos in directory: {args.input}")
        video_files = []
        for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.3gp', '.m4v']:
            video_files.extend(glob.glob(os.path.join(args.input, f"*{ext}")))
            video_files.extend(glob.glob(os.path.join(args.input, f"*{ext.upper()}")))

        if not video_files:
            print(f"No video files found in directory {args.input}.")
            return

        print(f"Found {len(video_files)} video files.")

        success_count = 0
        for video_path in video_files:
            if process_single_file(video_path, args):
                success_count += 1

        print(f"\nProcessing completed. Successfully processed {success_count} of {len(video_files)} files.")

        if success_count > 0:
            print("\nTo translate files, run the command with the appropriate adjusted file path:")
            print(f"python cli.py translate --input /path/to/adjusted_file.json")

    elif os.path.isfile(args.input):
        success = process_single_file(args.input, args)
        if not success:
            print(f"Failed to process file {args.input}")

    else:
        print(f"Error: Path {args.input} does not exist.")


if __name__ == "__main__":
    main()