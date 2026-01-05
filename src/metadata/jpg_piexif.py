# src/metadata/jpg_piexif.py
import piexif
from .base import MetadataProcessor
from ..errors import MetadataError

class JpgPiexifProcessor(MetadataProcessor):
    """piexif를 사용하여 JPG/JPEG 파일의 Exif 메타데이터를 처리합니다."""

    def read_metadata(self, file_path):
        """
        DateTimeOriginal 태그를 읽어 YYYY-MM-DD 형식으로 반환합니다.
        """
        try:
            exif_dict = piexif.load(file_path)
            datetime_original = exif_dict.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
            if datetime_original:
                # "YYYY:MM:DD HH:MM:SS" -> "YYYY-MM-DD"
                return {"ymd": datetime_original.decode('utf-8').split(' ')[0].replace(':', '-')}
        except Exception as e:
            raise MetadataError(f"Failed to read EXIF from {file_path}: {e}")
        # return None # 읽기 실패 시 날짜 정보 없음으로 간주 (이제 예외를 발생시키므로 필요 없음)
        return None

    def write_metadata(self, file_path, new_datetime_str):
        """
        DateTimeOriginal 태그에 새 날짜/시간을 기록합니다.
        재인코딩 없이 Exif 데이터만 삽입합니다.
        """
        # TODO: (TASK-04-02) DateTimeOriginal 쓰기 구현
        # - piexif.load, piexif.insert
        # - DEV_GUIDE에 따라 다른 날짜/시간 태그도 업데이트할지 결정 (v1.1)
        try:
            exif_dict = piexif.load(file_path)
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = new_datetime_str.encode('utf-8')
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, file_path)
            return True
        except Exception as e:
            raise MetadataError(f"Failed to write EXIF to {file_path}: {e}")
        # return False (이제 예외를 발생시키므로 필요 없음)
