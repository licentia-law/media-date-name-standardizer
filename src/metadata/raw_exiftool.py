# src/metadata/raw_exiftool.py
import subprocess
import os
import json
from .base import MetadataProcessor
from ..paths import get_exiftool_path
from ..errors import ExternalToolError, MetadataError

class RawExiftoolProcessor(MetadataProcessor):
    """ExifTool을 사용하여 RAW 파일(예: CR3)의 메타데이터를 처리합니다."""

    def __init__(self):
        self.exiftool_path = get_exiftool_path()
        if not self.exiftool_path or not os.path.exists(self.exiftool_path):
            raise FileNotFoundError(f"ExifTool executable not found at {self.exiftool_path}")

    def _to_ymd(self, value: str) -> str:
        return value.split(' ')[0].replace(':', '-')

    def read_metadata(self, file_path) -> dict[str, str] | None:
        """ExifTool을 호출하여 주요 날짜 태그를 읽습니다."""
        try:
            # -d %Y:%m:%d %H:%M:%S: 날짜 태그 출력 형식 지정
            # -api largefilesupport=1: 대용량 파일 지원
            command = [
                self.exiftool_path,
                "-api", "largefilesupport=1",
                "-d", "%Y:%m:%d %H:%M:%S",
                "-DateTimeOriginal",
                "-CreateDate",
                "-ModifyDate",
                "-j",
                str(file_path) # pathlib.Path 객체를 str로 변환
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')

            try:
                exif_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise MetadataError(f"ExifTool JSON parse failed for {file_path}: {e}")

            if not exif_data or not isinstance(exif_data, list):
                return None

            tags = exif_data[0]
            datetime_original = tags.get("DateTimeOriginal")

            if not datetime_original:
                # DateTimeOriginal이 없으면 None을 반환하여, 호출하는 쪽에서 날짜가 없음을 인지하고
                # 필요한 경우 write_metadata를 호출하도록 유도합니다.
                # DTL: DateTimeOriginal이 없으면 CreateDate, ModifyDate 순으로 대체 날짜를 찾습니다.
                create_date = tags.get("CreateDate")
                if create_date:
                    return {"ymd": self._to_ymd(create_date)}
                
                modify_date = tags.get("ModifyDate")
                if modify_date:
                    return {"ymd": self._to_ymd(modify_date)}
                
                return None # 모든 날짜 태그를 찾지 못함

            ymd_original = self._to_ymd(datetime_original)
            return {"ymd": ymd_original}
        except subprocess.CalledProcessError as e:
            raise ExternalToolError(f"ExifTool read failed for {file_path}: {e.stderr}", stdout=e.stdout, stderr=e.stderr)
        except FileNotFoundError:
            raise FileNotFoundError(f"ExifTool executable not found at {self.exiftool_path}")
        except Exception as e:
            raise MetadataError(f"Failed to read metadata from {file_path}: {e}")

    def write_metadata(self, file_path, new_datetime_str) -> bool:
        """
        ExifTool을 호출하여 주요 날짜/시간 태그를 모두 업데이트합니다.
        (DateTimeOriginal, CreateDate, ModifyDate)
        .CR3 파일에 대한 쓰기 문제를 해결하기 위해 -overwrite_original 플래그를 사용하지 않고,
        대신 ExifTool이 생성하는 원본 백업 파일을 직접 삭제합니다.
        """
        original_file_backup = f"{file_path}_original"

        try:
            # -overwrite_original 플래그 제거
            command = [
                self.exiftool_path,
                f"-DateTimeOriginal={new_datetime_str}",
                f"-CreateDate={new_datetime_str}",
                f"-ModifyDate={new_datetime_str}",
                str(file_path) # pathlib.Path 객체를 str로 변환
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')

            # ExifTool은 성공 시 백업 파일을 생성하고 "1 image files updated" 메시지를 출력
            if "1 image files updated" in result.stdout:
                # 성공적으로 실행되면, ExifTool이 남긴 원본 백업 파일을 삭제
                if os.path.exists(original_file_backup):
                    os.remove(original_file_backup)
                return True
            else:
                # 업데이트가 확인되지 않은 경우, 생성되었을 수 있는 새 파일과 백업 파일을 정리
                if os.path.exists(original_file_backup):
                     os.remove(original_file_backup)
                raise ExternalToolError(
                    f"ExifTool write operation for {file_path} did not confirm update. Output: {result.stdout.strip()}",
                    stdout=result.stdout, stderr=result.stderr
                )

        except subprocess.CalledProcessError as e:
            # 오류 발생 시, ExifTool이 .CR3 파일에 대해 새 파일을 만들지 않고 실패하는 경우가 많지만,
            # 만약을 위해 백업 파일이 남아있다면 삭제
            if os.path.exists(original_file_backup):
                os.remove(original_file_backup)
            raise ExternalToolError(f"ExifTool write failed for {file_path}: {e.stderr}", stdout=e.stdout, stderr=e.stderr)
        except FileNotFoundError:
            raise FileNotFoundError(f"ExifTool executable not found at {self.exiftool_path}")
        except Exception as e:
            if os.path.exists(original_file_backup):
                os.remove(original_file_backup)
            raise MetadataError(f"Failed to write metadata to {file_path}: {e}")
