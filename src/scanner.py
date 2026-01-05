# src/scanner.py
import os
import hashlib
from pathlib import Path
SUPPORTED_EXTENSIONS = {
    # 이미지
    '.jpg', '.jpeg', '.png', '.heic', '.cr3',
    # 동영상
    '.mp4', '.mov', '.avi'
}

class FileInfo:
    """파일 정보를 담는 데이터 클래스"""
    def __init__(self, absolute_path, source_root):
        self.absolute_path = Path(absolute_path)
        self.source_root = Path(source_root)
        self.filename = self.absolute_path.name
        # TODO: (TASK-03-03) 결정적 정렬을 위해 relative_path를 pathlib.Path 객체로 저장
        self.relative_path = self.absolute_path.relative_to(self.source_root).parent
        self.extension = self.absolute_path.suffix.lower()

    # TODO: (v0.2) 해시 계산을 위한 속성 추가
    # self.content_hash_or_original = None

def scan_files(source_root):
    """
    주어진 소스 루트에서 지원하는 확장자를 가진 모든 파일을 재귀적으로 찾습니다.
    """
    # DTL TASK-01-03: 파일 스캔 로직 구현 완료
    # FileInfo 객체 리스트를 반환하며, 각 파일에 대한 절대 경로와 상대 경로를 포함합니다.
    file_list = []
    for root, _, files in os.walk(source_root):
        for file in files:
            if Path(file).suffix.lower() in SUPPORTED_EXTENSIONS:
                abs_path = os.path.join(root, file)
                file_list.append(FileInfo(abs_path, source_root))
    return file_list

def calculate_md5(file_path: Path, chunk_size: int = 8192) -> str:
    """
    파일의 MD5 해시를 계산합니다. 대용량 파일 처리를 위해 스트리밍 방식을 사용합니다.
    
    Args:
        file_path (Path): 해시를 계산할 파일의 경로.
        chunk_size (int): 파일을 읽을 청크 크기 (바이트).
        
    Returns:
        str: 파일의 MD5 해시 문자열.
    """
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()
