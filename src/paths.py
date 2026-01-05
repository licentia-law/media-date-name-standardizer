# src/paths.py
import sys
import os
from pathlib import Path

def get_resource_path(relative_path):
    """
    개발 환경과 PyInstaller 번들 환경 모두에서 리소스 파일의 절대 경로를 반환합니다.
    relative_path는 'windows/ffmpeg.exe'와 같이 assets/bin/ 이후의 상대 경로 문자열입니다.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller 번들일 경우
        base_path = Path(sys._MEIPASS)
    else:
        # 일반 소스 실행일 경우 (프로젝트 루트를 기준으로)
        # src/paths.py -> src/ -> mdns/
        base_path = Path(__file__).parent.parent # Go up two levels from paths.py to mdns/

    # Construct the full path
    return str(base_path / "assets" / "bin" / relative_path)

def get_platform_bin_dir():
    """현재 운영체제에 맞는 바이너리 디렉토리 이름을 반환합니다."""
    if sys.platform.startswith('win'):
        return "windows"
    elif sys.platform == 'darwin':
        return "macos"
    elif sys.platform.startswith('linux'):
        return "linux"
    else:
        # 지원하지 않는 플랫폼의 경우, 기본값 또는 오류 처리를 고려할 수 있습니다.
        # 현재는 "linux"를 기본값으로 반환합니다.
        return "linux"

def get_ffmpeg_path():
    """ffmpeg 바이너리 경로를 반환합니다."""
    platform_dir = get_platform_bin_dir()
    if platform_dir == "windows":
        return get_resource_path(os.path.join(platform_dir, "ffmpeg.exe"))
    else:
        return get_resource_path(os.path.join(platform_dir, "ffmpeg"))

def get_ffprobe_path():
    """ffprobe 바이너리 경로를 반환합니다."""
    platform_dir = get_platform_bin_dir()
    if platform_dir == "windows":
        return get_resource_path(os.path.join(platform_dir, "ffprobe.exe"))
    else:
        return get_resource_path(os.path.join(platform_dir, "ffprobe"))

def get_exiftool_path():
    """ExifTool 바이너리 경로를 반환합니다."""
    platform_dir = get_platform_bin_dir()
    if platform_dir == "windows":
        return get_resource_path(os.path.join(platform_dir, "exiftool.exe"))
    else:
        return get_resource_path(os.path.join(platform_dir, "exiftool"))

def get_magick_path():
    """ImageMagick 'magick' 바이너리 경로를 반환합니다."""
    platform_dir = get_platform_bin_dir()

    if platform_dir == "windows":
        return get_resource_path(
            os.path.join(platform_dir, "imagemagick", "magick.exe")
        )
    else:
        return get_resource_path(
            os.path.join(platform_dir, "imagemagick", "magick")
        )

def check_binaries():
    """필수 바이너리가 모두 존재하는지 확인합니다."""
    binary_paths = {
        "ffmpeg": get_ffmpeg_path(),
        "ffprobe": get_ffprobe_path(),
        "exiftool": get_exiftool_path(),
        "magick": get_magick_path()
    }
    missing_binaries = []
    for name, path in binary_paths.items():
        if not Path(path).is_file():
            missing_binaries.append(name)
    return missing_binaries
