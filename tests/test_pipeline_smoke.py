# tests/test_pipeline_smoke.py
import pytest
import os
import queue
from pathlib import Path
from src.orchestrator import process_files

@pytest.fixture
def sample_input_dir(tmp_path):
    """
    통합 테스트(스모크 테스트)를 위한 샘플 디렉토리 구조와 파일을 생성합니다.
    DTL의 샘플 구조를 참고합니다.
    """
    # TODO: (v0.9) DTL의 샘플 구조를 충실히 재현
    # - 날짜 폴더, 날짜 없는 폴더
    # - JPG(PASS), JPG(해시), PNG(변환), MP4 등
    (tmp_path / "2026-01-05_여행").mkdir()
    (tmp_path / "2026-01-05_여행" / "img_1234a.jpg").write_text("dummy content")
    (tmp_path / "2026-01-05_여행" / "DSC0001.jpg").write_text("another dummy content")
    (tmp_path / "no_date_folder").mkdir()
    (tmp_path / "no_date_folder" / "random.jpg").write_text("random content")
    return tmp_path

@pytest.mark.skip(reason="Orchestrator 및 하위 모듈의 기본 구현이 완료된 후 활성화")
def test_pipeline_smoke(sample_input_dir):
    """
    전체 파이프라인에 대한 스모크 테스트.
    실행 오류가 발생하지 않고, 기본적인 결과물(result 폴더, 로그)이 생성되는지 확인합니다.
    """
    # TODO: (v0.9) 스모크 테스트 로직 구현
    # 1. process_files 실행
    # q = queue.Queue()
    # process_files(str(sample_input_dir), q)

    # 2. 결과 확인
    # result_dir = sample_input_dir / "result"
    # assert result_dir.exists()

    # - img_1234a.jpg -> IMG_1234a.jpg로 변경되었는가
    # - DSC0001.jpg -> IMG_<HASH5>.jpg로 변경되었는가
    # - random.jpg의 메타데이터는 스킵되었는가 (로그 확인)
    # - error.log가 비어있는가

    # 3. 멱등성 테스트 (재실행)
    # - 한 번 더 실행했을 때, 파일명/메타데이터가 더 이상 변경되지 않아야 함
    pass
