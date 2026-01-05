# src/logging_i18n.py

import traceback
from datetime import datetime
import os
from .errors import ExternalToolError, MDNSError # Import base error for general handling

# DTL TASK-08-01: DEV_GUIDE에 정의된 모든 이벤트 코드와 한글 메시지 매핑
LOG_MESSAGES = {
    # 메타데이터
    "META_PASS": "메타데이터: 날짜 일치(변경 없음)",
    "META_SET": "메타데이터: 폴더 날짜로 설정({time})", # Placeholder for time
    "META_SKIP_NO_DATE": "메타데이터: 기준 날짜 폴더를 찾지 못해 건너뜀",
    "META_FAIL_UNSUPPORTED": "메타데이터: 지원하지 않는 형식이라 건너뜀",
    "META_FAIL_READ": "메타데이터: 읽기 실패(오류 로그 확인)",
    "META_FAIL_WRITE": "메타데이터: 수정 실패(오류 로그 확인)",

    # 파일명
    "NAME_PASS": "파일명: 표준 형식 확인(유지)",
    "NAME_SET_UPPERCASE": "파일명: 소문자 img_ → 대문자 IMG_로 변경",
    "NAME_SET_HASH": "파일명: 해시 기반으로 변경({new_name})", # Placeholder for new_name
    "NAME_DUPLICATE_SUFFIX": "파일명: 중복 발생 → 숫자 접미사 추가({new_name})", # Placeholder for new_name

    # 변환
    "CONVERT_PNG_TO_JPG": "변환: PNG → JPG 변환",
    "CONVERT_HEIC_TO_JPG": "변환: HEIC → JPG 변환",
    "CONVERT_FAIL": "변환: 실패(오류 로그 확인)",

    # 복사
    "COPY_TO_RESULT": "복사: result 폴더로 복사",
    "COPY_FAIL": "복사: 실패(오류 로그 확인)",

    # 외부 도구 (DEV_GUIDE 6.2에는 없지만, ExternalToolError 발생 시 유용)
    "EXTERNAL_TOOL_NOT_FOUND": "외부 도구({tool_name})를 찾을 수 없습니다.",
    "EXTERNAL_TOOL_ERROR": "외부 도구({tool_name}) 실행 실패(오류 로그 확인)",

    # 복사
}

def get_log_message(event_code, **kwargs):
    """
    이벤트 코드에 해당하는 한글 로그 메시지를 반환합니다.
    kwargs를 사용하여 메시지 템플릿을 포맷팅할 수 있습니다.
    """
    message = LOG_MESSAGES.get(event_code, f"정의되지 않은 로그: {event_code}")
    try:
        return message.format(**kwargs)
    except KeyError:
        # 포맷팅에 필요한 인자가 누락된 경우
        return f"{message} (포맷팅 인자 오류)"

ERROR_LOG_FILENAME = "error.log"

def log_error_to_file(file_path, stage, exception_obj):
    """
    DTL TASK-08-02: error.log 파일에 상세 오류 정보를 기록합니다.
    Args:
        file_path (str): 오류가 발생한 파일의 경로.
        stage (str): 오류가 발생한 처리 단계 (예: "CONVERSION", "METADATA_READ", "NAMING").
        exception_obj (Exception): 발생한 예외 객체.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_message = f"[{timestamp}] File: {file_path}\n"
    error_message += f"  Stage: {stage}\n"
    error_message += f"  Exception Type: {type(exception_obj).__name__}\n"
    error_message += f"  Message: {exception_obj}\n"

    # Add stack trace
    error_message += "  Stacktrace:\n"
    error_message += "".join(traceback.format_exception(type(exception_obj), exception_obj, exception_obj.__traceback__))

    # Add stdout/stderr for ExternalToolError
    if isinstance(exception_obj, ExternalToolError):
        if exception_obj.stdout:
            error_message += f"  STDOUT: {exception_obj.stdout}\n"
        if exception_obj.stderr:
            error_message += f"  STDERR: {exception_obj.stderr}\n"
    
    error_message += "-" * 50 + "\n\n" # Separator for readability

    # Determine the path for error.log.
    # It should be in a 'logs' subdirectory relative to the current working directory.
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, ERROR_LOG_FILENAME)

    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(error_message)
    except Exception as e:
        # Fallback if logging to file fails
        print(f"CRITICAL ERROR: Failed to write to error log file {log_file_path}: {e}")
        print(error_message) # Print to console as a last resort
