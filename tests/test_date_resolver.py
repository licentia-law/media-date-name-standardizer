# tests/test_date_resolver.py
import pytest
from pathlib import Path
from src.date_resolver import resolve_date

@pytest.fixture
def test_dir(tmp_path):
    """테스트용 디렉토리 구조를 생성합니다."""
    # TODO: (TASK-03-01) DTL의 샘플 구조와 유사하게 생성
    (tmp_path / "2026-01-05_trip" / "inner").mkdir(parents=True)
    (tmp_path / "no_date_folder").mkdir()
    (tmp_path / "2026-01-05_trip" / "photo.jpg").touch()
    (tmp_path / "2026-01-05_trip" / "inner" / "video.mp4").touch()
    (tmp_path / "no_date_folder" / "random.jpg").touch()
    return tmp_path

def test_resolve_date_direct_parent(test_dir):
    """파일의 부모 폴더에 날짜가 있는 경우"""
    # TODO: (TASK-03-01) 테스트 케이스 구현
    file_path = test_dir / "2026-01-05_trip" / "photo.jpg"
    result = resolve_date(str(file_path))
    assert result["found"] is True
    assert result["ymd"] == "2026-01-05"

def test_resolve_date_grandparent(test_dir):
    """파일의 상위 폴더 (부모의 부모)에 날짜가 있는 경우"""
    # TODO: (TASK-03-01) 테스트 케이스 구현
    file_path = test_dir / "2026-01-05_trip" / "inner" / "video.mp4"
    result = resolve_date(str(file_path))
    assert result["found"] is True
    assert result["ymd"] == "2026-01-05"

def test_resolve_date_not_found(test_dir):
    """날짜 폴더를 찾을 수 없는 경우"""
    # TODO: (TASK-03-01) 테스트 케이스 구현
    file_path = test_dir / "no_date_folder" / "random.jpg"
    result = resolve_date(str(file_path))
    assert result["found"] is False
