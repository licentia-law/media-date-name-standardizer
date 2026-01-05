# src/metadata/raw_exiftool.py
import subprocess
import os
from .base import MetadataProcessor
from ..paths import get_exiftool_path
from ..errors import ExternalToolError, MetadataError

class RawExiftoolProcessor(MetadataProcessor):
    """ExifTool을 사용하여 RAW 파일(예: CR3)의 메타데이터를 처리합니다."""

    def __init__(self):
        self.exiftool_path = get_exiftool_path()
        if not self.exiftool_path or not os.path.exists(self.exiftool_path):
            raise FileNotFoundError(f"ExifTool executable not found at {self.exiftool_path}")

    def read_metadata(self, file_path):
        """ExifTool을 호출하여 DateTimeOriginal을 읽습니다."""
        try:
            # -s3: 값만 출력
            # -d %Y:%m:%d %H:%M:%S: DateTimeOriginal의 출력 형식을 지정 (읽기 시에는 필요 없을 수 있으나 일관성을 위해)
            # -api largefilesupport=1: 대용량 파일 지원
            command = [
                self.exiftool_path,
                "-DateTimeOriginal",
                "-s3",
                str(file_path) # pathlib.Path 객체를 str로 변환
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
            
            datetime_original = result.stdout.strip()
            if datetime_original:
                # "YYYY:MM:DD HH:MM:SS" -> "YYYY-MM-DD"
                return {"ymd": datetime_original.split(' ')[0].replace(':', '-')}
            return None
        except subprocess.CalledProcessError as e:
            raise ExternalToolError(f"ExifTool read failed for {file_path}: {e.stderr}", stdout=e.stdout, stderr=e.stderr)
        except FileNotFoundError:
            raise FileNotFoundError(f"ExifTool executable not found at {self.exiftool_path}")
        except Exception as e:
            raise MetadataError(f"Failed to read metadata from {file_path}: {e}")

    def write_metadata(self, file_path, new_datetime_str):
        """
        ExifTool을 호출하여 주요 날짜/시간 태그를 모두 업데이트합니다.
        (DateTimeOriginal, CreateDate, ModifyDate)
        """
        try:
            # -overwrite_original: 원본 파일을 직접 수정
            # -api largefilesupport=1: 대용량 파일 지원
            command = [
                self.exiftool_path,
                f"-DateTimeOriginal={new_datetime_str}",
                f"-CreateDate={new_datetime_str}",
                f"-ModifyDate={new_datetime_str}",
                "-overwrite_original",
                str(file_path) # pathlib.Path 객체를 str로 변환
            ]
            # stderr를 캡처하여 오류 메시지를 확인
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
            
            # ExifTool은 성공 시 "1 image files updated"와 같은 메시지를 stdout에 출력
            # 오류가 발생하면 stderr에 메시지를 출력하고 non-zero exit code를 반환
            if "1 image files updated" in result.stdout:
                return True
            else:
                # 예상치 못한 성공 메시지 또는 경고가 있을 수 있으므로 로그에 남길 수 있음
                raise ExternalToolError(
                    f"ExifTool write operation for {file_path} did not confirm update. Output: {result.stdout.strip()}",
                    stdout=result.stdout, stderr=result.stderr
                )

        except subprocess.CalledProcessError as e:
            raise ExternalToolError(f"ExifTool write failed for {file_path}: {e.stderr}", stdout=e.stdout, stderr=e.stderr)
        except FileNotFoundError:
            raise FileNotFoundError(f"ExifTool executable not found at {self.exiftool_path}")
        except Exception as e:
            raise MetadataError(f"Failed to write metadata to {file_path}: {e}")