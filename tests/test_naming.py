# tests/test_naming.py
import pytest
from src.naming import PASS_REGEX, standardize_filename

# TODO: (TASK-02-01) pytest.mark.parametrize를 사용하여 다양한 PASS/FAIL 케이스 테스트
@pytest.mark.parametrize("filename, expected", [
    ("IMG_1234.jpg", True),
    ("img_1234.jpg", True),
    ("img_1234a.jpg", True),
    ("img_1234ab.JPG", True),
    ("IMG_1.cr3", True),
    ("DSC_0001.jpg", False),
    ("photo.png", False),
    ("IMG-1234.jpg", False), # 하이픈은 허용되지 않음
])
def test_pass_regex(filename, expected):
    """파일명 PASS 정규식이 정확히 동작하는지 테스트합니다."""
    assert bool(PASS_REGEX.match(filename)) == expected

# TODO: (TASK-02-02) img_ -> IMG_ 정규화 테스트
def test_uppercase_regularization(tmp_path):
    """'img_' 접두사가 'IMG_'로 변경되는지 테스트합니다."""
    # - 실제 파일 생성 및 이름 변경 후 확인
    pass

# TODO: (TASK-02-03) 해시 기반 이름 변경 테스트
def test_hash_based_naming(tmp_path):
    """PASS가 아닌 파일이 해시 기반으로 이름 변경되는지 테스트합니다."""
    # - 더미 파일 생성, 해시 이름 생성, 실제 변경 확인
    pass

# TODO: (TASK-02-04) 중복 처리 테스트
def test_duplicate_suffix_logic(tmp_path):
    """이름 충돌 시 언더바 없이 숫자 접미사가 붙는지 테스트합니다."""
    # - 동일한 이름의 파일을 여러 개 생성 시도
    # - ...1, ...2, ...3 과 같이 생성되는지 확인
    pass
