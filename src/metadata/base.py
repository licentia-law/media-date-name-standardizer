# src/metadata/base.py
from abc import ABC, abstractmethod
from typing import Union


class MetadataProcessor(ABC):
    """
    메타데이터 처리를 위한 추상 기반 클래스(ABC).
    모든 포맷별 메타데이터 프로세서는 이 클래스를 상속받아야 합니다.
    """
    @abstractmethod
    def read_metadata(self, file_path):
        """
        파일에서 메타데이터를 읽습니다.
        :return: {'ymd': 'YYYY-MM-DD'} 또는 날짜 정보가 없으면 None
        """
        pass

    @abstractmethod
    def write_metadata(self, file_path, new_datetime_str):
        """
        파일에 새로운 날짜/시간 메타데이터를 씁니다.
        :param new_datetime_str: "YYYY:MM:DD HH:MM:SS" 형식의 문자열
        :return: 성공 시 True, 실패 시 False
        """
        pass

def get_metadata_processor(file_extension: str) -> Union[MetadataProcessor, None]:
    """
    파일 확장자에 따라 적절한 메타데이터 프로세서 인스턴스를 반환하는 팩토리 함수.
    """
    from .jpg_piexif import JpgPiexifProcessor
    from .video_ffmpeg import VideoFfmpegProcessor
    from .raw_exiftool import RawExiftoolProcessor

    ext = file_extension.lower()
    if ext in ['.jpg', '.jpeg']:
        return JpgPiexifProcessor()
    elif ext in ['.mp4', '.mov', '.avi']: # AVI is handled internally by VideoFfmpegProcessor to skip
        return VideoFfmpegProcessor()
    elif ext == '.cr3':
        return RawExiftoolProcessor()
    else:
        return None # 지원하지 않는 형식
