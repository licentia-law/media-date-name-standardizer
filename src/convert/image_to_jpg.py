import os
import subprocess
from pathlib import Path
from PIL import Image # For PNG conversion
from typing import Union

from ..paths import get_magick_path # Assuming ImageMagick for HEIC
from ..errors import ExternalToolError, ConversionError
from ..logging_i18n import get_log_message, log_error_to_file

def convert_to_jpg(source_path: Path, destination_path: Path, summary: dict, queue) -> Union[Path, None]:
    """
    PNG 또는 HEIC 파일을 JPG로 변환합니다.
    """
    file_extension = source_path.suffix.lower()
    
    try:
        if file_extension == '.png':
            # PNG to JPG conversion using Pillow
            img = Image.open(source_path)
            if img.mode == 'RGBA':
                # Create a white background for transparent PNGs
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3]) # 3 is the alpha channel
                img = background
            img.save(destination_path, "jpeg")
            queue.put(('log', f"  {get_log_message('CONVERT_PNG_TO_JPG')}"))
            summary['converted_to_jpg'] += 1
            return destination_path
        elif file_extension == '.heic':
            # HEIC to JPG conversion using ImageMagick (magick convert)
            # Requires ImageMagick to be installed and 'magick' command available in PATH
            # Or, get_magick_path() should point to the executable.
            magick_path = get_magick_path()
            if not magick_path or not os.path.exists(magick_path):
                raise FileNotFoundError(f"ImageMagick (magick) executable not found at {magick_path}")

            command = [
                magick_path,
                'convert',
                str(source_path),
                str(destination_path)
            ]
            
            # DEV_GUIDE: ImageMagick 타임아웃 30초
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=30)
            
            if result.returncode == 0:
                queue.put(('log', f"  {get_log_message('CONVERT_HEIC_TO_JPG')}"))
                summary['converted_to_jpg'] += 1
                return destination_path
            else:
                raise ExternalToolError(f"ImageMagick conversion failed for {source_path}", stdout=result.stdout, stderr=result.stderr)
        else:
            # Should not happen if called correctly, but as a safeguard
            queue.put(('log', f"  {get_log_message('CONVERT_FAIL')} (Unsupported extension for conversion: {file_extension})"))
            summary['conversion_failed'] += 1
            return None
    except (ExternalToolError, ConversionError) as e:
        queue.put(('log', f"  {get_log_message('CONVERT_FAIL')} ({source_path.name})"))
        log_error_to_file(str(source_path), "CONVERSION", e)
        summary['conversion_failed'] += 1
        return None
    except FileNotFoundError as e:
        queue.put(('log', f"  {get_log_message('CONVERT_FAIL')} (External tool not found: {e}) ({source_path.name})"))
        log_error_to_file(str(source_path), "CONVERSION", e)
        summary['conversion_failed'] += 1
        return None
    except Exception as e:
        queue.put(('log', f"  {get_log_message('CONVERT_FAIL')} ({source_path.name})"))
        log_error_to_file(str(source_path), "CONVERSION", e)
        summary['conversion_failed'] += 1
        return None
