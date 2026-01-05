# src/date_resolver.py
import os
import re
from pathlib import Path
from typing import TypedDict, Union, Tuple

# DTL TASK-03-01: PRD의 정규식 확정 완료
DATE_FOLDER_REGEX = re.compile(r"^(\d{4}-\d{2}-\d{2})")

class DateInfoFound(TypedDict):
    found: bool
    ymd: str
    scope_key: Tuple[str, str]

class DateInfoNotFound(TypedDict):
    found: bool

def resolve_date(file_path) -> Union[DateInfoFound, DateInfoNotFound]:
    """
    파일 경로로부터 상위로 탐색하며 'YYYY-MM-DD' 형식의 폴더명을 찾아
    기준 날짜 정보를 반환합니다.
    DTL TASK-03-01: 날짜 탐색 로직 구현 완료
    DTL TASK-03-02: 스코프 키 정책 확정 완료
    """
    current_path = Path(file_path).parent
    while current_path != current_path.parent: # 루트에 도달할 때까지
        match = DATE_FOLDER_REGEX.match(current_path.name)
        if match:
            ymd = match.group(1)
            scope_key = (str(current_path), ymd)
            return {
                "found": True,
                "ymd": ymd,
                "scope_key": scope_key
            }
        current_path = current_path.parent

    return {"found": False}
