import csv
import subprocess
import argparse
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_text_file(file_path: str) -> list:
    """
    Parse the text file containing text overlay instructions for the video.

    :param file_path: Path to the text file with instructions.
    :return: List of dictionaries containing text overlay parameters.
    """
    logging.info(f"Parsing text file: {file_path}")
    texts = []
    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file, delimiter=',', quotechar='"', skipinitialspace=True)
            for row in reader:
                logging.debug(f"Parsing line: {row}")
                if row[0].startswith('#') or not row:
                    continue
                time, end_time, text, x, y, font, size = row
                texts.append({
                    'start_time': time,
                    'end_time': end_time,
                    'text': text,
                    'position': (int(x), int(y)),
                    'font': font,
                    'font_size': int(size)
                })
    except Exception as e:
        logging.error(f"Failed to parse text file: {e}")
        raise RuntimeError(f"Error parsing text file: {e}")
    return texts

def generate_ffmpeg_command(input_video: str, text_file: str, text_dict: dict, output_video: str) -> str:
    """
    Generate an FFmpeg command string to add a single text overlay to a video using a text file.

    :param input_video: Path to the input video file.
    :param text_file: Path to the temporary text file containing the overlay text.
    :param text_dict: Dictionary containing text overlay parameters.
    :param output_video: Path for the output video file.
    :return: A string representing the FFmpeg command.
    """
    start_time_seconds = convert_to_seconds(text_dict['start_time'])
    end_time_seconds = convert_to_seconds(text_dict['end_time'])

    filter_string = (
        f"drawtext=fontfile=/usr/share/fonts/truetype/{text_dict['font']}.ttf: "
        f"textfile='{text_file}': x={text_dict['position'][0]}: y={text_dict['position'][1]}: "
        f"fontsize={text_dict['font_size']}: fontcolor=white: "
        f"enable='between(t,{start_time_seconds},{end_time_seconds})'"
    )

    command = (
        f"ffmpeg -i {input_video} -filter:v \"{filter_string}\" "
        f"-codec:a copy {output_video}"
    )
    return command

def convert_to_seconds(time_str: str) -> float:
    """
    Convert a time string in the format HH:MM:SS or MM:SS to seconds.

    :param time_str: Time string to convert.
    :return: Time in seconds.
    """
    parts = time_str.split(':')
    parts = [float(part) for part in parts]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    else:
        return parts[0]

def run_ffmpeg(command: str):
    """
    Execute the FFmpeg command.

    :param command: The FFmpeg command string to execute.
    """
    logging.info(f"Running FFmpeg command: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
        logging.info("FFmpeg command executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg command failed with error: {e}")
        raise RuntimeError(f"FFmpeg command failed: {e}")

def main():
    logging.info("Starting video processing.")
    parser = argparse.ArgumentParser(description="Add text overlays to a video sequentially.")
    parser.add_argument("input_video", help="Path to the input video file.")
    parser.add_argument("text_file", help="Path to the text file with overlay instructions.")
    parser.add_argument("output_video", help="Path for the final output video file.")
    args = parser.parse_args()

    try:
        texts = parse_text_file(args.text_file)
    except RuntimeError as e:
        logging.error(e)
        return

    with tempfile.TemporaryDirectory() as tmpdirname:
        logging.debug(f"Created temporary directory: {tmpdirname}")
        temp_video = os.path.join(tmpdirname, "temp.mp4")
        try:
            subprocess.run(f"cp {args.input_video} {temp_video}", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to copy input video: {e}")
            raise RuntimeError(f"Failed to copy input video: {e}")

        for idx, text in enumerate(texts):
            logging.debug(f"Processing text overlay {idx}: {text['text']}")
            text_file_path = os.path.join(tmpdirname, f"text_{idx}.txt")
            with open(text_file_path, 'w') as text_file:
                text_file.write(text['text'])
            logging.debug(f"Created temporary text file: {text_file_path}")

            command = generate_ffmpeg_command(temp_video, text_file_path, text, f"{tmpdirname}/temp_{idx}.mp4")
            try:
                run_ffmpeg(command)
            except RuntimeError as e:
                logging.error(e)
                return
            
            temp_video = f"{tmpdirname}/temp_{idx}.mp4"

        try:
            subprocess.run(f"cp {temp_video} {args.output_video}", shell=True, check=True)
            logging.info(f"Output video saved to: {args.output_video}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to save output video: {e}")
            raise RuntimeError(f"Failed to save output video: {e}")

    logging.info("Video processing completed successfully.")

if __name__ == "__main__":
    main()
