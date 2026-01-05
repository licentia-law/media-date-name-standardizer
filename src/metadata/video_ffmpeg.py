# src/metadata/video_ffmpeg.py
import subprocess
import os
import json
from datetime import datetime
from pathlib import Path
from .base import MetadataProcessor
from ..paths import get_ffmpeg_path, get_ffprobe_path
from ..errors import ExternalToolError, MetadataError

class VideoFfmpegProcessor(MetadataProcessor):
    """ffmpeg/ffprobe를 사용하여 동영상 파일의 메타데이터를 처리합니다."""

    def __init__(self):
        self.ffmpeg_path = get_ffmpeg_path()
        self.ffprobe_path = get_ffprobe_path()
        
        if not self.ffmpeg_path or not os.path.exists(self.ffmpeg_path):
            raise FileNotFoundError(f"ffmpeg executable not found at {self.ffmpeg_path}")
        if not self.ffprobe_path or not os.path.exists(self.ffprobe_path):
            raise FileNotFoundError(f"ffprobe executable not found at {self.ffprobe_path}")

    def read_metadata(self, file_path):
        """ffprobe를 사용하여 creation_time을 읽습니다."""
        file_extension = Path(file_path).suffix.lower()
        if file_extension == '.avi':
            # DTL TASK-07-02: AVI 스킵. Orchestrator에서 이 반환값을 보고 스킵 처리할 수 있도록 함.
            return {"found": False, "reason": "unsupported_format"}

        try:
            command = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(file_path)
            ]
            # DEV_GUIDE: ffprobe 타임아웃 10초
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=10)
            
            metadata = json.loads(result.stdout)
            creation_time_str = metadata.get('format', {}).get('tags', {}).get('creation_time')

            if creation_time_str:
                # creation_time can be in various formats, e.g., ISO 8601 (2023-10-26T10:30:00.000000Z)
                # or just YYYY-MM-DD HH:MM:SS
                try:
                    # Try parsing as ISO 8601 first
                    dt_object = datetime.fromisoformat(creation_time_str.replace('Z', '+00:00'))
                except ValueError:
                    # Fallback for other common formats, e.g., "YYYY-MM-DD HH:MM:SS"
                    # This might need more robust parsing for all possible formats
                    dt_object = datetime.strptime(creation_time_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                
                return {"ymd": dt_object.strftime('%Y-%m-%d')}
            return None # creation_time tag not found
        except subprocess.CalledProcessError as e:
            raise ExternalToolError(f"ffprobe read failed for {file_path}: {e.stderr}", stdout=e.stdout, stderr=e.stderr)
        except FileNotFoundError:
            raise FileNotFoundError(f"ffprobe executable not found at {self.ffprobe_path}")
        except json.JSONDecodeError:
            raise MetadataError(f"Failed to parse ffprobe JSON output for {file_path}")
        except Exception as e:
            raise MetadataError(f"Failed to read metadata from {file_path}: {e}")

    def write_metadata(self, file_path, new_datetime_str):
        """
        ffmpeg를 사용하여 creation_time 메타데이터를 수정합니다.
        스트림을 재인코딩하지 않고 메타데이터만 변경합니다.
        """
        file_extension = Path(file_path).suffix.lower()
        if file_extension == '.avi':
            # DTL TASK-07-02: AVI 스킵. Orchestrator에서 이 반환값을 보고 스킵 처리할 수 있도록 함.
            return False

        # new_datetime_str is expected in "YYYY:MM:DD HH:MM:SS" format from orchestrator
        # ffmpeg expects ISO 8601 for creation_time, e.g., "YYYY-MM-DDTHH:MM:SSZ"
        try:
            dt_object = datetime.strptime(new_datetime_str, '%Y:%m:%d %H:%M:%S')
            ffmpeg_datetime_str = dt_object.strftime('%Y-%m-%dT%H:%M:%SZ')
        except ValueError as e:
            raise MetadataError(f"Invalid datetime format for writing: {new_datetime_str}. Expected YYYY:MM:DD HH:MM:SS. Error: {e}")

        temp_output_path = Path(file_path).parent / f"temp_{Path(file_path).name}"
        
        try:
            command = [
                self.ffmpeg_path,
                '-i', str(file_path),
                '-c', 'copy', # Copy streams without re-encoding
                '-map_metadata', '0', # Copy all metadata from input to output
                '-metadata', f'creation_time={ffmpeg_datetime_str}',
                '-y', # Overwrite output files without asking
                str(temp_output_path)
            ]
            # DEV_GUIDE: ffmpeg 타임아웃 60초
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=60)
            
            # If ffmpeg command was successful, replace the original file with the temporary one
            os.replace(temp_output_path, file_path)
            return True
        except subprocess.CalledProcessError as e:
            # Clean up temp file if it was created
            if temp_output_path.exists():
                os.remove(temp_output_path)
            raise ExternalToolError(f"ffmpeg write failed for {file_path}: {e.stderr}", stdout=e.stdout, stderr=e.stderr)
        except FileNotFoundError:
            raise FileNotFoundError(f"ffmpeg executable not found at {self.ffmpeg_path}")
        except Exception as e:
            # Clean up temp file if it was created
            if temp_output_path.exists():
                os.remove(temp_output_path)
            raise MetadataError(f"Failed to write metadata to {file_path}: {e}")
