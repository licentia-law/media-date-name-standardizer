# src/gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.ttk import Progressbar
import threading
import queue # Keep queue for inter-thread communication
import os # For os.startfile or webbrowser.open

# TODO: (v0.1) orchestrator 모듈 임포트
# from .orchestrator import process_files

class Worker(threading.Thread):
    """
    백그라운드에서 실제 작업을 수행하는 워커 스레드입니다.
    GUI 스레드에 이벤트를 전달하기 위해 gui_queue를 사용합니다.
    """
    def __init__(self, gui_queue, source_path, orchestrator_process_files):
        super().__init__()
        self.gui_queue = gui_queue
        self.source_path = source_path
        self.orchestrator_process_files = orchestrator_process_files
        self.running = True

    def run(self):
        self.gui_queue.put(('log', f"워커 스레드 시작. 소스: {self.source_path}"))        
        # Call the actual orchestrator process_files function
        self.orchestrator_process_files(self.source_path, self.gui_queue)
        # The orchestrator will send 'done' message when finished
        self.gui_queue.put(('log', "워커 스레드 종료."))

    def stop(self):
        """워커 스레드를 안전하게 중단하기 위한 메서드."""
        self.running = False

class MainApplication:
    """
    메인 GUI 애플리케이션 클래스.
    UI 요소 생성, 이벤트 핸들링, 워커 스레드와의 통신을 담당합니다.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("MDNS - Media Date & Name Standardizer")
        self.root.geometry("800x650")

        self.result_folder_path = None # To store the path of the result folder
        self.source_dir = tk.StringVar()
        self.queue = queue.Queue()
        self.worker_thread = None # Keep track of the worker thread

        self._init_widgets()

        # TODO: (TASK-01-01) UI 레이아웃 완성
        # - 프레임 사용하여 위젯 그룹화
        # - 스타일 적용

    def _init_widgets(self):
        """UI 위젯을 초기화하고 배치합니다."""
        # --- 소스 폴더 선택 ---
        tk.Label(self.root, text="소스 폴더:").pack(pady=5)
        entry = tk.Entry(self.root, textvariable=self.source_dir, width=80)
        entry.pack(pady=5)
        browse_button = tk.Button(self.root, text="폴더 선택", command=self.browse_folder)
        browse_button.pack(pady=5)

        # --- 변환 시작 버튼 ---
        self.start_button = tk.Button(self.root, text="변환 시작", command=self.start_processing)
        self.start_button.pack(pady=20)

        # --- 진행률 바 ---
        self.progress = Progressbar(self.root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(pady=10)
        self.progress_label = tk.Label(self.root, text="0/0 (0.00%)")
        self.progress_label.pack()

        # --- 로그 창 ---
        self.log_area = scrolledtext.ScrolledText(self.root, width=100, height=25)
        self.log_area.pack(pady=10)

        # --- 결과 폴더 열기 버튼 ---
        self.open_result_button = tk.Button(self.root, text="결과 폴더 열기", state=tk.DISABLED, command=self.open_result_folder)
        self.open_result_button.pack(pady=10)

    def browse_folder(self):
        """'폴더 선택' 대화상자를 열어 소스 디렉토리를 설정합니다."""
        directory = filedialog.askdirectory()
        if directory:
            self.source_dir.set(directory)
            self.log("소스 폴더 선택: " + directory)

    def start_processing(self):
        """'변환 시작' 버튼 클릭 시 워커 스레드를 시작합니다."""
        source_path = self.source_dir.get()
        if not source_path:
            messagebox.showerror("오류", "소스 폴더를 선택하세요.")
            return

        self.log("변환 작업을 시작합니다...")
        self.start_button.config(state=tk.DISABLED)
        self.open_result_button.config(state=tk.DISABLED)

        # Clear log area for new processing
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

        # TASK-01-02: 워커 스레드 생성 및 시작
        from .orchestrator import process_files # Import here to avoid circular dependency if orchestrator imports gui
        self.worker_thread = Worker(self.queue, source_path, process_files)
        self.worker_thread.start()

        # TASK-01-02: 주기적으로 큐를 확인하는 after() 메서드 호출
        self.root.after(100, self.poll_queue)

        self.log("오케스트레이터 스레드를 시작했습니다.")

    def poll_queue(self):
        """주기적으로 큐를 확인하여 UI를 업데이트합니다."""
        try:
            while True:
                event_type, *values = self.queue.get_nowait() # Unpack event type and values
                self.handle_message(event_type, *values)
                self.queue.task_done() # Mark the task as done
        except queue.Empty:
            pass
        finally:
            # 워커 스레드가 살아있으면 계속 폴링
            if self.worker_thread and self.worker_thread.is_alive():
                self.root.after(100, self.poll_queue)

    def handle_message(self, event_type, *args):
        """
        워커 스레드로부터 받은 메시지를 처리하여 UI를 업데이트합니다.
        """
        if event_type == 'log':
            self.log(args[0])
        elif event_type == 'progress':
            self.progress['value'] = args[0]
            self.progress_label.config(text=args[1])
        elif event_type == 'done':
            self.log(args[0]) # "모든 파일 처리가 완료되었습니다."
            messagebox.showinfo("처리 완료", "모든 파일 처리가 완료되었습니다. 로그를 확인해주세요.")
            self.start_button.config(state=tk.NORMAL)
            # 결과 폴더 경로 설정 및 버튼 활성화
            source_path = self.source_dir.get()
            if source_path:
                self.result_folder_path = os.path.join(source_path, "result")
                self.open_result_button.config(state=tk.NORMAL)
            else:
                self.open_result_button.config(state=tk.DISABLED)
            # 요약 보고서는 orchestrator에서 'log' 메시지로 이미 전송됨

    def log(self, message):
        """로그 창에 메시지를 추가합니다."""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def open_result_folder(self):
        """'결과 폴더 열기' 기능을 구현합니다."""
        if self.result_folder_path and os.path.exists(self.result_folder_path):
            try:
                os.startfile(self.result_folder_path) # Windows 전용. 다른 OS는 subprocess.Popen 사용
                self.log(f"결과 폴더 열기: {self.result_folder_path}")
            except Exception as e:
                self.log(f"결과 폴더를 여는 데 실패했습니다: {e}")
                messagebox.showerror("오류", f"결과 폴더를 여는 데 실패했습니다: {e}")
        else:
            self.log("결과 폴더를 찾을 수 없습니다.")
            messagebox.showwarning("경고", "처리된 결과 폴더를 찾을 수 없습니다.")
