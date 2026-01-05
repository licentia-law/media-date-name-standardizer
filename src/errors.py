# src/errors.py

class MDNSError(Exception):
    """이 프로젝트의 기본 예외 클래스입니다."""
    pass

class ConversionError(MDNSError):
    """파일 변환 중 발생하는 오류입니다."""
    pass

class MetadataError(MDNSError):
    """메타데이터 처리 중 발생하는 오류입니다."""
    pass

class FileOperationError(MDNSError):
    """파일 복사, 이동, 이름 변경 등 파일 시스템 작업 중 발생하는 오류입니다."""
    pass

class ExternalToolError(MDNSError):
    """ffmpeg, ExifTool 등 외부 도구 실행 중 발생하는 오류입니다."""
    def __init__(self, message, stdout=None, stderr=None):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return f"{super().__str__()}\nSTDOUT: {self.stdout}\nSTDERR: {self.stderr}"

# TODO: (v0.1) 필요에 따라 더 구체적인 예외 타입 추가
