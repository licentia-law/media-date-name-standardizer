# src/orchestrator.py
import os
from collections import defaultdict

from pathlib import Path
import shutil # For file operations like copy2
from typing import Union, cast, TypedDict
from datetime import datetime, timedelta # For date/time manipulation

from .scanner import scan_files, FileInfo, calculate_md5 # Import FileInfo and calculate_md5
from .date_resolver import resolve_date # Assuming resolve_date returns Union[DateInfoFound, DateInfoNotFound]
from .naming import standardize_filename
from .metadata.base import MetadataProcessor, get_metadata_processor
from .logging_i18n import get_log_message, log_error_to_file
from .convert.image_to_jpg import convert_to_jpg # Import the conversion function
from .errors import ExternalToolError, MetadataError

# Minimal type definitions for DateInfoFound and DateInfoNotFound
# These would typically come from date_resolver.py
class DateInfoFound(TypedDict):
    found: bool
    ymd: str
    scope_key: tuple # (date_folder_full_path_str, date_ymd_string)

class DateInfoNotFound(TypedDict):
    found: bool

def create_summary_report(summary):
    """
    처리 요약 보고서를 생성합니다. (TASK-08-03)
    현재는 간단한 문자열을 반환합니다.
    """
    report = "--- 처리 요약 ---\n"
    for key, value in summary.items():
        # Translate internal keys to more user-friendly Korean messages for the report
        if key == 'processed_files': report += f"총 처리 파일 수: {value}\n"
        elif key == 'failed_files': report += f"처리 실패 파일 수: {value}\n"
        elif key == 'copied_files': report += f"원본 복사 파일 수: {value}\n"
        elif key == 'converted_to_jpg': report += f"JPG 변환 파일 수: {value}\n"
        elif key == 'conversion_failed': report += f"변환 실패 파일 수: {value}\n"
        elif key == 'metadata_changed': report += f"메타데이터 변경 파일 수: {value}\n"
        elif key == 'metadata_skipped_no_date': report += f"메타데이터 스킵 (날짜 없음) 파일 수: {value}\n"
        elif key == 'metadata_passed': report += f"메타데이터 유지 파일 수: {value}\n"
        elif key == 'metadata_failed': report += f"메타데이터 수정 실패 파일 수: {value}\n"
        elif key == 'filename_passed': report += f"파일명 유지 파일 수: {value}\n"
        elif key == 'filename_uppercase_normalized': report += f"파일명 대문자 정규화 파일 수: {value}\n"
        elif key == 'filename_hashed': report += f"파일명 해시 변경 파일 수: {value}\n"
        elif key == 'filename_duplicate_suffix': report += f"파일명 중복 접미사 추가 파일 수: {value}\n"
        else: report += f"{key}: {value}\n" # Fallback for unhandled keys
    report += "-----------------\n"
    return report

def process_files(source_root, queue):
    """
    파일 처리의 전체 과정을 총괄하는 메인 함수.
    스캔 -> 정렬 -> 처리 파이프라인 순으로 진행.
    """
    # TODO: (TASK-01-03) 1차 스캔: 대상 파일 목록 및 개수 확보
    file_list = scan_files(source_root)
    total_files = len(file_list)
    queue.put(('log', f"총 {total_files}개의 처리 대상 파일을 찾았습니다."))

    # TODO: (TASK-03-03) 결정적 정렬: 상대 경로 + 파일명 기준
    # FileInfo 객체는 relative_path (Path 객체)와 filename (str)을 가집니다.
    # 정렬 키는 (str(relative_path), filename.lower())로 설정합니다.
    file_list.sort(key=lambda x: (str(x.relative_path), x.filename.lower()))
    queue.put(('log', "파일 목록을 결정적 순서로 정렬했습니다."))

    # TODO: (TASK-03-02) 스코프 카운터 초기화
    time_offset_counters = defaultdict(int)
    queue.put(('log', "스코프 카운터를 초기화했습니다."))

    # TODO: (TASK-08-03) 처리 요약 정보 초기화
    summary = defaultdict(int)
    summary['processed_files'] = 0
    summary['failed_files'] = 0
    summary['copied_files'] = 0
    summary['converted_to_jpg'] = 0
    summary['conversion_failed'] = 0
    summary['metadata_changed'] = 0
    summary['metadata_skipped_no_date'] = 0
    summary['metadata_passed'] = 0
    summary['metadata_failed'] = 0
    summary['filename_passed'] = 0
    summary['filename_uppercase_normalized'] = 0
    summary['filename_hashed'] = 0
    summary['filename_duplicate_suffix'] = 0
    queue.put(('log', "처리 요약 정보를 초기화했습니다."))

    # --- 2차 처리: 파일 단위 파이프라인 ---
    for i, file_info in enumerate(file_list):
        try:
            # 각 파일 처리 시작 로그
            queue.put(('log', f"[{i+1}/{total_files}] 파일 처리 시작: {file_info.filename}"))
            process_single_file(file_info, time_offset_counters, summary, queue)
            summary['processed_files'] += 1
        except Exception as e:
            # TASK-08-02: error.log 기록 (현재는 임시 로그)
            error_message = f"[{i+1}/{total_files}] 파일 처리 중 오류 발생 ({file_info.absolute_path}): {e}"
            queue.put(('log', f"  {get_log_message('CONVERT_FAIL')}")) # Using a generic fail message for now
            log_error_to_file(str(file_info.absolute_path), "MAIN_PIPELINE", e)
            summary['failed_files'] += 1

        progress_val = ((i + 1) / total_files) * 100
        progress_text = f"{i + 1}/{total_files} ({progress_val:.2f}%)"
        queue.put(('progress', progress_val, progress_text))
        # queue.put({'type': 'log', 'message': ...}) # 각 단계에서 로그 전송

    # TASK-08-03: 최종 요약 보고
    final_summary_report = create_summary_report(summary)
    queue.put(('log', final_summary_report))
    queue.put(('done', "모든 파일 처리가 완료되었습니다."))


def process_single_file(file_info: FileInfo, time_offset_counters: defaultdict, summary: defaultdict, queue):
    """
    단일 파일에 대한 처리 파이프라인.
    """
    # 1. (TASK-03-01) 기준 날짜 탐색
    date_info: Union[DateInfoFound, DateInfoNotFound] = resolve_date(file_info.absolute_path) # Assuming resolve_date returns a dict with 'found' key
    if date_info["found"]:
        date_info = cast(DateInfoFound, date_info) # Explicitly cast for static analysis
        queue.put(('log', f"  기준 날짜 폴더 발견: {date_info['ymd']} (스코프: {date_info['scope_key'][0]})")) # cite: 1
    else:
        queue.put(('log', "  기준 날짜 폴더를 찾지 못했습니다. 메타데이터 수정 스킵."))

    # 2. (TASK-01-03) 결과 디렉토리 생성
    # source_root는 FileInfo 객체에 Path 객체로 저장되어 있음
    result_base_dir = file_info.source_root / "result"
    result_dir = result_base_dir / file_info.relative_path # relative_path는 Path 객체
    os.makedirs(result_dir, exist_ok=True)
    queue.put(('log', f"  결과 디렉토리 생성/확인: {result_dir}"))

    # 3. (v0.5) 결과 파일 생성 (복사 또는 변환)
    result_file_path = handle_conversion_or_copy(file_info, result_dir, summary, queue)
    if not result_file_path:
        return # 변환/복사 실패 시 스킵

    # 4. (v0.4, v0.6, v0.7) 메타데이터 보정
    _handle_metadata(result_file_path, date_info, time_offset_counters, summary, queue)

    # 5. (v0.2) 파일명 표준화
    # 파일의 실제 MD5 해시를 계산합니다.
    content_hash = calculate_md5(result_file_path)
    queue.put(('log', f"  파일 콘텐츠 MD5 해시 계산 완료: {content_hash[:5]}..."))

    # standardize_filename 함수는 파일의 현재 경로, content_hash, summary를 받음 (naming.py에서 summary 업데이트 가정)
    # result_file_path는 이미 result 폴더 내의 파일 경로임
    final_renamed_path = standardize_filename(str(result_file_path), content_hash, summary)
    if final_renamed_path != str(result_file_path):
        queue.put(('log', f"  파일명 표준화: {os.path.basename(result_file_path)} -> {os.path.basename(final_renamed_path)}"))
    else:
        queue.put(('log', f"  파일명 표준화: 변경 없음 ({os.path.basename(result_file_path)})"))

def handle_conversion_or_copy(file_info: FileInfo, result_dir: Path, summary: defaultdict, queue) -> Union[Path, None]:
    """
    파일을 결과 디렉토리로 복사하거나 변환합니다.
    현재는 원본 파일을 복사하는 로직만 구현되어 있습니다.
    (TASK-05-01, TASK-05-02 관련)
    """
    destination_path = result_dir / file_info.filename

    # Handle PNG/HEIC to JPG conversion
    if file_info.extension in ['.png', '.heic']:
        # For conversion, the destination filename should have a .jpg extension
        destination_filename_jpg = file_info.absolute_path.stem + ".jpg"
        destination_path_jpg = result_dir / destination_filename_jpg
        converted_path = convert_to_jpg(file_info.absolute_path, destination_path_jpg, summary, queue)
        if converted_path:
            return converted_path
        else:
            # Conversion failed, return None to skip further processing for this file
            return None

    # If not a PNG/HEIC, or if conversion is not applicable, copy the original file
    try:
        shutil.copy2(file_info.absolute_path, destination_path)
        queue.put(('log', f"  원본 파일 복사: {file_info.absolute_path.name} -> {destination_path.name}")) # DEV_GUIDE 6.2 COPY_TO_RESULT
        summary['copied_files'] += 1
        return destination_path
    except Exception as e:
        queue.put(('log', f"  파일 복사 실패 ({file_info.absolute_path.name}): {e}"))
        # TODO: (TASK-08-02) error.log 기록
        log_error_to_file(str(file_info.absolute_path), "FILE_COPY", e)
        return None

def _handle_metadata(result_file_path: Path, date_info: Union[DateInfoFound, DateInfoNotFound], time_offset_counters: defaultdict, summary: defaultdict, queue):
    """
    파일의 메타데이터를 보정합니다.
    (TASK-04, TASK-06, TASK-07 관련)
    """
    file_extension = result_file_path.suffix.lower()
    processor = get_metadata_processor(file_extension)

    # 1. 기준 날짜 정보가 없는 경우 처리
    if not date_info["found"]:
        if date_info.get("reason") == "unsupported_format":
            queue.put(('log', f"  {get_log_message('META_FAIL_UNSUPPORTED')} ({result_file_path.name})"))
        else:
            queue.put(('log', f"  {get_log_message('META_SKIP_NO_DATE')} ({result_file_path.name})"))
        summary['metadata_skipped_no_date'] += 1
        return

    # date_info가 DateInfoFound 타입임을 명시적으로 캐스팅
    date_info = cast(DateInfoFound, date_info)
    folder_ymd = date_info['ymd']
    scope_key = date_info['scope_key']
    current_offset_seconds = time_offset_counters[scope_key]

    # 기준 날짜 + 오프셋으로 최종 목표 날짜/시간 생성
    base_datetime_str = f"{folder_ymd} 09:00:00" # 09:00:00부터 시작하여 1초씩 증가
    target_datetime_obj = datetime.strptime(base_datetime_str, '%Y-%m-%d %H:%M:%S') + timedelta(seconds=current_offset_seconds)
    target_datetime_str_for_write = target_datetime_obj.strftime('%Y:%m:%d %H:%M:%S') # Exif/FFmpeg write format
    target_ymd_for_compare = target_datetime_obj.strftime('%Y-%m-%d') # For comparison with read YMD

    # 2. 프로세서가 없는 경우 (지원하지 않는 파일 형식)
    if processor is None:
        queue.put(('log', f"  {get_log_message('META_FAIL_UNSUPPORTED')} ({result_file_path.name})"))
        summary['metadata_skipped_no_date'] += 1 # Or a new category for unsupported format
        return

    read_ymd = None
    try:
        read_result = processor.read_metadata(str(result_file_path))
        if read_result and read_result.get("ymd"):
            read_ymd = read_result["ymd"]
    except (ExternalToolError, MetadataError) as e:
        queue.put(('log', f"  {get_log_message('META_FAIL_READ')} ({result_file_path.name})"))
        log_error_to_file(str(result_file_path), "METADATA_READ", e)
        summary['metadata_failed'] += 1
        return
    except Exception as e:
        queue.put(('log', f"  {get_log_message('META_FAIL_READ')} ({result_file_path.name})"))
        log_error_to_file(str(result_file_path), "METADATA_READ", e)
        summary['metadata_failed'] += 1
        return

    # 3. 메타데이터가 이미 일치하는 경우
    if read_ymd == target_ymd_for_compare:
        queue.put(('log', f"  {get_log_message('META_PASS')} ({result_file_path.name})"))
        summary['metadata_passed'] += 1
    # 4. 메타데이터를 수정해야 하는 경우
    else:
        try:
            success = processor.write_metadata(str(result_file_path), target_datetime_str_for_write)
            if success:
                queue.put(('log', f"  {get_log_message('META_SET', time=target_datetime_str_for_write)} ({result_file_path.name})"))
                summary['metadata_changed'] += 1
                time_offset_counters[scope_key] += 1 # Increment offset for the next file in the same scope
            else:
                # This path might be less common if write_metadata raises exceptions on failure
                queue.put(('log', f"  {get_log_message('META_FAIL_WRITE')} ({result_file_path.name})"))
                log_error_to_file(str(result_file_path), "METADATA_WRITE", Exception("Metadata write failed without specific exception."))
                summary['metadata_failed'] += 1
        except (ExternalToolError, MetadataError) as e:
            queue.put(('log', f"  {get_log_message('META_FAIL_WRITE')} ({result_file_path.name})"))
            log_error_to_file(str(result_file_path), "METADATA_WRITE", e)
            summary['metadata_failed'] += 1
        except Exception as e:
            queue.put(('log', f"  {get_log_message('META_FAIL_WRITE')} ({result_file_path.name})"))
            log_error_to_file(str(result_file_path), "METADATA_WRITE", e)
            summary['metadata_failed'] += 1
