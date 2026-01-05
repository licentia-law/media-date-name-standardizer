# src/main.py
import tkinter as tk
from .gui import MainApplication

def main():
    """
    프로젝트의 메인 엔트리포인트.
    Tkinter 루트 윈도우를 생성하고, MainApplication을 시작합니다.
    """
    # TODO: (v0.9) PyInstaller 환경과 소스 실행 환경에 따른 초기화 코드 추가
    # 예: paths.py를 이용한 바이너리 경로 설정 확인
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()

if __name__ == "__main__":
    main()
