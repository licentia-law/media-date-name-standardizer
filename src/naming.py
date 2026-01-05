# src/naming.py
import os
import re
import hashlib

# TODO: (TASK-02-01) PRD의 PASS 정규식 확정 (대소문자 무관)
# PASS 판정 정규식(대소문자 무관): ^img_\d+[a-zA-Z]*\..+$
# DEV_GUIDE: suffix: 영문 0개 이상(대/소문자 모두 허용)
PASS_REGEX = re.compile(r"^img_\d+[a-zA-Z]*\..+$", re.IGNORECASE)

def is_pass_filename(filename):
    """
    주어진 파일명이 MDNS의 PASS 패턴에 맞는지 확인합니다.
    """
    return bool(PASS_REGEX.match(filename))

def standardize_filename(file_path, content_hash_or_original, summary):
    """
    파일명을 표준 규칙(PASS/해시)에 따라 변경합니다.
    - PASS: `img_` 접두사를 `IMG_`로 정규화.
    - 해시: `IMG_<HASH5>` 형식으로 변경.
    - 중복 처리: `...1`, `...2` 와 같이 숫자 접미사 추가.

    Args:
        file_path (str): 현재 파일의 전체 경로 (result 폴더 내).
        content_hash (str): PASS가 아닌 경우 사용할 파일 내용의 MD5 해시 (5자리 이상).
        summary (dict): 처리 결과를 기록할 요약 딕셔너리.

    Returns:
        str: 최종적으로 변경된 파일의 전체 경로.
    """
    current_filename = os.path.basename(file_path)
    new_filename_base = ""

    is_pass = is_pass_filename(current_filename)

    if is_pass:
        # 2. (TASK-02-02) img_ -> IMG_ 정규화
        new_filename_base = handle_pass_regularization(current_filename, summary)
        if new_filename_base == current_filename:
            # If no change, it means it was already IMG_ or not starting with img_ but still PASS
            summary["NAME_PASS"] = summary.get("NAME_PASS", 0) + 1
    else:
        # 3. (TASK-02-03) 해시 기반 이름 생성
        new_filename_base = generate_hash_name(current_filename, content_hash_or_original, summary)

    # 4. (TASK-02-04) 중복 처리 및 최종 rename
    final_path = handle_duplicates_and_rename(file_path, new_filename_base, summary)
    return final_path


def handle_pass_regularization(file_path, summary):
    """
    PASS 패턴 파일의 `img_` 접두사를 `IMG_`로 변경합니다.
    Args:
        file_path (str): 현재 파일명 (확장자 포함).
        summary (dict): 처리 결과를 기록할 요약 딕셔너리.
    Returns:
        str: 정규화된 파일명. 변경이 없으면 원본 파일명 반환.
    """
    # Check if it starts with 'img_' (case-insensitive)
    if file_path.lower().startswith("img_"):
        # Check if it's already "IMG_" (case-sensitive)
        if not file_path.startswith("IMG_"):
            new_name = "IMG_" + file_path[4:]
            summary["NAME_SET_UPPERCASE"] = summary.get("NAME_SET_UPPERCASE", 0) + 1
            return new_name
    return file_path # 변경할 필요가 없는 경우 (이미 IMG_ 이거나 img_로 시작하지 않음)

def generate_hash_name(current_filename, content_hash, summary):
    """
    해시 기반의 새 파일명을 생성합니다: IMG_<HASH5>.<ext>
    Args:
        current_filename (str): 현재 파일명 (확장자 포함).
        content_hash (str): 파일 내용의 MD5 해시 (최소 5자리 이상).
        summary (dict): 처리 결과를 기록할 요약 딕셔너리.
    Returns:
        str: 해시 기반으로 생성된 파일명.
    """
    hash5 = content_hash[:5].upper()
    extension = os.path.splitext(current_filename)[1] # result 폴더 내 파일의 확장자를 사용
    new_name = f"IMG_{hash5}{extension}"
    summary["NAME_SET_HASH"] = summary.get("NAME_SET_HASH", 0) + 1
    return new_name


def handle_duplicates_and_rename(current_full_path, desired_new_filename, summary):
    """
    중복을 처리하고 실제 파일명을 변경합니다.
    Args:
        current_full_path (str): 현재 파일의 전체 경로 (result 폴더 내).
        desired_new_filename (str): 중복 처리 전 원하는 새 파일명 (확장자 포함).
        summary (dict): 처리 결과를 기록할 요약 딕셔너리.
    Returns:
        str: 최종적으로 변경된 파일의 전체 경로.
    """
    parent_dir = os.path.dirname(current_full_path)
    base_name, ext = os.path.splitext(desired_new_filename)
    
    final_new_full_path = os.path.join(parent_dir, desired_new_filename)
    
    counter = 0
    
    # Loop while a file with the desired name (or suffixed name) already exists
    # AND it's not the file we are currently processing.
    # This prevents infinite loops if the file already has its final desired name.
    while os.path.exists(final_new_full_path) and final_new_full_path != current_full_path:
        counter += 1
        # DTL TASK-02-04: 언더바 없이 숫자 suffix
        final_new_filename = f"{base_name}{counter}{ext}"
        final_new_full_path = os.path.join(parent_dir, final_new_filename)
        
        # Only increment NAME_DUPLICATE_SUFFIX once for the first collision
        if counter == 1:
            summary["NAME_DUPLICATE_SUFFIX"] = summary.get("NAME_DUPLICATE_SUFFIX", 0) + 1
    
    # If the file already has the final desired name (no collision or it's its own final name),
    # then no rename operation is needed.
    if current_full_path == final_new_full_path:
        return current_full_path
    
    os.rename(current_full_path, final_new_full_path)
    return final_new_full_path
