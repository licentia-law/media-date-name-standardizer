# DTL
## MDNS (Media Date & Name Standardizer) 개발 작업 목록 (DTL)
- 버전: DTL-v1.0
- 기준 문서: PRD / DEV_GUIDE / CRG
- 작성일: 2026-01-05
- 대상 독자: 개발 초보자(단계별 체크리스트 중심)

---

## 0. DTL 사용법(필독)

### 0.1 완료 정의(Definition of Done, DoD)
각 작업(Task)은 아래 조건을 만족하면 “완료”로 본다.
- 코드가 **실행**된다(최소 1회 이상).
- 실패 시 **전체 중단 없이** 다음 파일 처리를 계속한다(파일 단위 격리).
- UI(진행률/로그)가 멈추지 않는다(메인 스레드 안전).
- 핵심 규칙(Deterministic/원본 비파괴/한글 로그/중복 suffix 규칙)이 문서대로 동작한다.
- 최소 단위 테스트(해당 모듈) 1개 이상이 통과한다.

### 0.2 작업 순서 원칙
- 아래 DTL은 **의존성 순서**로 정렬되어 있다.
- 초보자 기준으로 “작게 만들고(동작 확인) → 점진 확장” 방식이다.
- 먼저 **v0.1 Skeleton**을 실행 가능한 상태로 만든 후 기능을 붙인다.

---

## 1. 마일스톤(권장 릴리스 단계)

- v0.1: Skeleton + GUI 연결 + 스캔/진행률/로그(더미 처리)
- v0.2: 파일명 표준화(naming) 완성 + 중복 처리
- v0.3: 기준 날짜 탐색(date_resolver) + 스코프 카운터(09:00:00 + 1초) + 결정적 정렬
- v0.4: JPG/JPEG 메타데이터(piexif) PASS/SET/스킵/실패 로깅
- v0.5: PNG/HEIC → JPG 변환 + 변환 후 piexif 메타데이터 적용
- v0.6: CR3 ExifTool 메타데이터 수정
- v0.7: MP4/MOV ffmpeg 메타데이터 수정 + AVI 스킵
- v0.8: 통합 파이프라인 안정화 + error.log + 요약 리포트
- v0.9: PyInstaller 패키징 + 바이너리 번들링(paths.py) + 배포 스모크 테스트
- v1.0: 문서/테스트 정리 + 릴리스 체크

---

## 2. 준비 작업(환경/레포)

### TASK-00-01. 레포 생성 및 기본 폴더 구조 만들기
**목표**: DEV_GUIDE의 폴더 구조대로 “빈 프로젝트”를 만든다.

**작업**
1) 새 폴더 생성: `mdns/`
2) DEV_GUIDE 권장 구조대로 `src/`, `tests/`, `assets/bin/...` 폴더 생성
3) `PRD.md`, `DEV_GUIDE.md`, `CRG.md`를 레포 루트에 배치

**산출물**
- 디렉토리 구조
- 빈 파일(placeholder): `src/main.py`, `src/gui.py` 등

**완료 기준**
- 폴더 구조가 생성되어 있고, git init이 되어 있으면 더 좋다(선택).

---

### TASK-00-02. 파이썬 가상환경(venv) 생성 및 패키지 설치
**목표**: 실행/테스트 가능한 Python 환경을 만든다.

**작업(Windows 기준)**
1) 프로젝트 루트에서:
   - `python -m venv .venv`
2) 가상환경 활성화:
   - `.\.venv\Scriptsctivate`
3) `requirements.txt` 생성(초기 권장):
   - piexif
   - pillow
   - pytest
   - (HEIC 변환용) pillow-heif  ← 설치 실패 가능성이 있으므로 우선은 “옵션”으로 둬도 됨
4) 설치:
   - `pip install -r requirements.txt`

**산출물**
- `.venv/`
- `requirements.txt`

**완료 기준**
- `python -c "import piexif, PIL; print('ok')"` 가 성공한다.
- `pytest -q` 실행 시 “테스트 없음” 정도로라도 실행이 된다.

---

### TASK-00-03. 외부 바이너리 준비(ffmpeg/ffprobe/exiftool)
**목표**: v1 요구 도구를 `assets/bin/`에 배치한다.

**작업**
1) `assets/bin/windows/`에 다음 파일을 준비:
   - `ffmpeg.exe`, `ffprobe.exe`, `exiftool.exe`
2) 아직 도구를 구하지 못했다면:
   - 지금 단계에서는 “더미 경로”만 만들고, v0.7/v0.6에서 실제 동작 확인할 때 채운다.

**완료 기준**
- 폴더와 파일명이 DEV_GUIDE와 일치한다(또는 추후에 확정해도 됨).

---

### TASK-00-04. 테스트용 샘플 데이터 폴더 준비
**목표**: 기능을 눈으로 검증할 수 있는 샘플 폴더 트리를 만든다.

**권장 샘플 구조**
- `sample_input/`
  - `2026-01-05_여행/`
    - `IMG_1234.jpg` (PASS)
    - `img_1234a.jpg` (PASS + IMG_로 정규화)
    - `DSC0001.jpg` (해시로 변경)
    - `photo.png` (PNG→JPG 변환 대상)
    - `clip.mp4` (영상)
  - `no_date_folder/`
    - `random.jpg` (메타데이터 스킵 대상)
  - `2026-01-06/inner/`
    - `x.jpg` (상위 탐색으로 날짜 찾는 케이스)

**완료 기준**
- 최소 JPG 2개, 날짜 폴더/날짜 없는 폴더 케이스를 준비했다.

---

## 3. v0.1 Skeleton: GUI + 스캔 + 진행률 + 로그(더미 처리)

### TASK-01-01. GUI 골격 만들기(gui.py)
**목표**: 소스 폴더 선택, 변환 시작 버튼, 로그창, 진행률바가 동작한다.

**작업**
1) tkinter로 다음 UI 구성:
   - 소스 폴더 선택(Entry + Browse 버튼)
   - 변환 시작(Start) 버튼
   - 진행률(Progressbar)
   - 로그(Text 위젯 또는 ScrolledText)
   - 완료 후 “결과 폴더 열기” 버튼(초기 비활성)
2) Start 클릭 시 워커 스레드 시작(실제 처리는 더미로)

**완료 기준**
- 폴더 선택 → Start 클릭 → 로그에 “시작” 표시 → Progressbar가 0→100 변화(더미라도)

---

### TASK-01-02. 워커 스레드 + Queue + after() 기반 UI 갱신
**목표**: CRG의 “Tkinter 메인 스레드 안전” 준수.

**작업**
1) `queue.Queue()` 생성
2) 워커 스레드는 처리 이벤트를 큐에 push
   - 예: `(type='log', message='...')`, `(type='progress', value=...)`
3) GUI는 `root.after(50, poll_queue)`로 큐를 주기적으로 비우며 UI 업데이트

**완료 기준**
- 대량(예: 더미 500회 loop) 이벤트에서도 GUI가 멈추지 않는다.

---

### TASK-01-03. scanner.py: 파일 수집(확장자 필터) + total_files 계산
**목표**: 지원 확장자만 재귀적으로 수집하고 개수를 계산한다.

**작업**
1) 지원 확장자 집합 정의:
   - 이미지: .jpg .jpeg .png .heic .cr3
   - 동영상: .mp4 .mov .avi
2) `os.walk()` 또는 `pathlib.Path.rglob()` 사용
3) 결과는 “절대경로 리스트”와 “relative path” 계산 가능하도록 구조화

**완료 기준**
- sample_input 기준으로 “대상 파일 수”가 로그에 정확히 출력된다.

---

## 4. v0.2 파일명 표준화(naming.py) 완성

### TASK-02-01. PASS 판정 함수 구현
**목표**: `IMG_1234`, `img_1234`, `IMG_1234a`, `img_1234ab` 모두 PASS.

**작업**
1) 정규식 구현(대소문자 무관):
   - 예: `^(?i)img_\d+[a-z]*$`
   - 필요하면 suffix 대문자도 허용하도록 `[a-zA-Z]*`
2) 단위 테스트 작성:
   - PASS 케이스 4개 이상
   - FAIL 케이스도 2개 이상(예: IMG-1234, IMAGE_1234 등)

**완료 기준**
- `pytest -q` 통과

---

### TASK-02-02. img_ → IMG_ 대문자 정규화 리네임 구현
**목표**: PASS이지만 `img_`인 파일은 `IMG_`로 변경(식별자는 유지).

**작업**
1) “prefix만” 변경하는 함수 구현
2) 실제 파일 리네임은 result 폴더 내에서만 수행
3) 로그 이벤트:
   - “파일명: 소문자 img_ → 대문자 IMG_로 변경”

**완료 기준**
- `img_1234a.jpg`가 `IMG_1234a.jpg`로 바뀐다.

---

### TASK-02-03. 해시 기반 이름 생성(MD5 5자리) 구현
**목표**: PASS가 아닌 파일은 `IMG_<HASH5>`로 변경.

**작업**
1) MD5 계산:
   - v1 단순 구현: 파일 전체 읽기 → md5 → 앞 5자리 → upper
2) 단위 테스트:
   - 같은 파일은 같은 hash5
   - 다른 파일은 대체로 다른 hash5(테스트는 “다르면 좋다” 수준)

**완료 기준**
- `DSC0001.jpg` 같은 파일이 `IMG_XXXXX.jpg`로 바뀐다.

---

### TASK-02-04. 중복 처리(언더바 없이 숫자 suffix) 구현
**목표**: `IMG_A1B2C.jpg`가 존재하면 `IMG_A1B2C1.jpg`로 생성.

**작업**
1) “목표 파일명”이 이미 존재하면:
   - base 뒤에 숫자 1부터 증가
2) 단위 테스트:
   - 파일 3개가 같은 base에 충돌할 때 1,2 suffix가 붙는지 확인

**완료 기준**
- 언더바 없이 suffix가 붙는다.

---

## 5. v0.3 기준 날짜 탐색 + 스코프 카운터 + 결정적 정렬

### TASK-03-01. date_resolver.py: 상위로 올라가며 YYYY-MM-DD 폴더 찾기
**목표**: 파일 경로에서 가장 가까운 날짜 폴더를 찾는다.

**작업**
1) 시작 폴더: 파일의 parent
2) while parent exists:
   - 폴더명에서 정규식 `^(\d{4}-\d{2}-\d{2})` 매칭
   - 매칭되면 return ymd, date_folder_path
3) 루트까지 못 찾으면 found=False

**완료 기준**
- `2026-01-06/inner/x.jpg`는 2026-01-06을 찾는다.
- `no_date_folder/random.jpg`는 found=False

---

### TASK-03-02. orchestrator: 스코프 카운터(09:00:00 + 1초)
**목표**: 같은 날짜 폴더 스코프에서 처리 순서대로 초가 증가한다.

**작업**
1) 스코프 키: `(date_folder_full_path, ymd)`
2) dict로 카운터 보관:
   - 처음 등장 시 0
   - 파일 처리 시 1 증가 → `09:00:00 + counter_seconds`
3) 문자열 포맷:
   - Exif: `YYYY:MM:DD HH:MM:SS`

**완료 기준**
- 같은 스코프에서 파일 3개 처리 시 시간이 09:00:00, 09:00:01, 09:00:02로 부여된다(메타데이터 모듈 적용 전에는 “계산값 로그”로 검증).

---

### TASK-03-03. 결정적 정렬(Deterministic ordering) 적용
**목표**: 재실행 시 결과가 동일하게 나오도록 정렬을 고정한다.

**작업**
1) 스캔 결과(파일 리스트)를 처리 전에 정렬
2) 정렬 키:
   - relative_path (parent 포함) + filename
   - 대소문자 무시 정렬 권장(예: `.lower()`)
3) 테스트:
   - 동일 입력 2번 실행 시, 로그의 “처리 순서”가 동일한지 확인

**완료 기준**
- 같은 입력에 대해 처리 순서가 변하지 않는다.

---

## 6. v0.4 JPG/JPEG 메타데이터(piexif) PASS/SET

### TASK-04-01. metadata/jpg_piexif.py: DateTimeOriginal 읽기
**목표**: JPG/JPEG에서 촬영일을 읽어 YMD를 비교한다.

**작업**
1) piexif로 Exif 로드
2) DateTimeOriginal 추출(없으면 None)
3) 값 파싱:
   - "YYYY:MM:DD HH:MM:SS" → YMD 비교용 "YYYY-MM-DD"

**완료 기준**
- DateTimeOriginal이 있는 파일은 PASS/SET 판단이 가능하다.

---

### TASK-04-02. DateTimeOriginal 쓰기(SET)
**목표**: 기준 날짜가 다르거나 없으면 새 값을 기록한다.

**작업**
1) SET 값 생성:
   - 기준 날짜 + 09:00:SS (스코프 카운터 기반)
2) piexif insert로 Exif만 수정(재인코딩 금지)
3) 로그:
   - PASS: “메타데이터: 날짜 일치(변경 없음)”
   - SET: “메타데이터: 폴더 날짜로 설정(09:00:SS)”
   - 기준 날짜 없음: “메타데이터: 기준 날짜 폴더를 찾지 못해 건너뜀”

**완료 기준**
- JPG 파일의 DateTimeOriginal이 실제로 바뀐다(ExifTool/뷰어로 확인 가능).

---

## 7. v0.5 PNG/HEIC → JPG 변환 + 변환 후 메타데이터

### TASK-05-01. convert/image_to_jpg.py: PNG → JPG 변환(알파 처리 포함)
**목표**: PNG를 JPG로 변환하여 result에 생성한다.

**작업**
1) Pillow로 PNG 로드
2) 알파가 있으면 흰색 배경 합성 후 RGB로 변환
3) JPG 저장(quality=95, optimize=True)
4) 로그: “변환: PNG → JPG 변환”

**완료 기준**
- PNG 입력이 result에서 JPG로 생성된다.

---

### TASK-05-02. HEIC → JPG 변환(라이브러리 적용)
**목표**: HEIC를 JPG로 변환하여 result에 생성한다.

**작업**
1) pillow-heif 사용 시:
   - import 및 open → Pillow Image로 변환
2) 저장은 JPG로(quality=95)
3) 실패 시:
   - “변환: 실패(오류 로그 확인)” + error.log 기록
   - 이후 파일명 처리 계속(단, 변환 실패하면 대상 파일 자체가 없으므로 정책 결정 필요: v1에서는 “해당 파일 스킵” 권장)

**완료 기준**
- HEIC 샘플이 result에 JPG로 생성된다(가능한 환경에서).

---

### TASK-05-03. PNG/HEIC 변환 결과 JPG에 piexif 메타데이터 적용
**목표**: 변환된 JPG에 DateTimeOriginal을 PASS/SET 규칙대로 적용한다.

**작업**
1) 변환 후 결과 파일을 “JPG 처리 파이프라인”에 동일하게 태운다.
2) PASS/SET 로직은 JPG와 동일
3) 파일명 규칙:
   - 변환 결과는 확장자 `.jpg`로 고정

**완료 기준**
- 변환된 JPG에 촬영일이 주입된다.

---

## 8. v0.6 CR3 메타데이터(ExifTool)

### TASK-06-01. paths.py: ExifTool 경로 해석(sys._MEIPASS 포함)
**목표**: 개발 실행/배포 실행에서 exiftool 경로를 안정적으로 찾는다.

**작업**
1) PyInstaller 실행 시: `sys._MEIPASS` 사용
2) 소스 실행 시: 프로젝트 루트 기준 경로 사용
3) 미존재 시:
   - UI에 안내 로그 + error.log 기록 + 해당 파일은 메타데이터 스킵

**완료 기준**
- 소스 실행에서도 경로를 찾고, 배포 환경에서도 동일 로직을 쓰도록 준비된다.

---

### TASK-06-02. metadata/raw_exiftool.py: CR3 촬영일 읽기/쓰기
**목표**: CR3에 촬영일 태그를 SET한다(없거나 다르면).

**작업**
1) subprocess로 exiftool 호출(리스트 인자 방식)
2) 읽기:
   - DateTimeOriginal을 우선 조회(없으면 None)
3) 쓰기(권장 최소 태그):
   - DateTimeOriginal, CreateDate, ModifyDate를 동일 값으로
4) 실패 처리:
   - error.log에 stdout/stderr 기록
   - UI에는 “메타데이터: 수정 실패(오류 로그 확인)”

**완료 기준**
- CR3 샘플에서 태그가 변경된다(가능하면 ExifTool로 재확인).

---

## 9. v0.7 MP4/MOV 메타데이터(ffmpeg)

### TASK-07-01. paths.py: ffmpeg/ffprobe 경로 해석
**목표**: ffmpeg/ffprobe 실행 경로를 통일한다.

**완료 기준**
- ffprobe를 호출해 버전 출력(또는 간단 명령)이 실행된다.

---

### TASK-07-02. metadata/video_ffmpeg.py: MP4/MOV creation_time 읽기/쓰기
**목표**: 기준 날짜와 비교 후 PASS/SET.

**작업**
1) ffprobe로 creation_time 추출(없으면 None)
2) PASS 조건: YMD 동일
3) SET: 기준 날짜 + 09:00:SS
4) AVI:
   - 메타데이터 수정 스킵
   - 로그: “메타데이터: 지원하지 않는 형식이라 건너뜀”

**완료 기준**
- mp4/mov 샘플의 creation_time이 변경된다(가능하면 ffprobe로 재확인).

---

## 10. v0.8 통합 안정화(로그/에러/요약)

### TASK-08-01. logging_i18n.py: 내부 이벤트코드 → 한글 메시지 매핑
**목표**: UI에는 한글 로그만 노출.

**작업**
1) 이벤트 코드 enum/상수 정의
2) 코드→메시지 dict 작성
3) UI는 항상 메시지를 받아 출력(코드는 내부 기록용으로만 사용 가능)

**완료 기준**
- UI 로그가 한글만 출력된다.

---

### TASK-08-02. error.log 구현(파일 단위 격리)
**목표**: 실패 원인 추적 가능.

**작업**
1) error.log 기록 함수(append) 작성
2) 포함 내용(최소):
   - timestamp, file_path, stage, exception, stacktrace, stdout/stderr(외부도구)
3) 워커가 예외를 잡아 기록하고 계속 진행

**완료 기준**
- 일부 파일을 고의로 실패시키고도 전체 처리가 끝난다.

---

### TASK-08-03. 처리 요약 리포트(완료 팝업에 요약 표시)
**목표**: 총 처리 수/성공/실패/스킵/변환수 등을 보여준다.

**완료 기준**
- 완료 시 요약이 로그/팝업에 나온다(간단해도 됨).

---

## 11. v0.9 패키징(PyInstaller) + 바이너리 번들링

### TASK-09-01. PyInstaller로 실행 파일 생성(개발 PC 기준)
**목표**: exe 형태로 실행 가능하게 만든다.

**작업**
1) PyInstaller 설치: `pip install pyinstaller`
2) 빌드 실행(예):
   - `pyinstaller --noconsole --onefile src/main.py`
3) assets/bin 동봉 필요:
   - --add-binary 또는 spec 파일에서 포함 처리

**완료 기준**
- exe 실행 시 GUI가 뜬다.

---

### TASK-09-02. sys._MEIPASS 기반 바이너리 접근 검증
**목표**: exe 환경에서 ffmpeg/exiftool을 찾고 실행한다.

**완료 기준**
- exe로 실행한 상태에서 mp4/mov/cr3 처리(또는 최소 “바이너리 탐색”)가 성공한다.

---

## 12. v1.0 릴리스 체크

### TASK-10-01. 회귀 테스트(핵심 규칙 확인)
**체크리스트**
- 원본 비파괴: 원본 폴더 파일이 변경되지 않았는가
- result 구조 유지: 상대 경로가 그대로 재현되는가
- 기준 날짜 상위 탐색: 날짜 폴더 없는 경우 스킵 되는가
- 09:00:00+1초: 스코프 단위로 증가하는가
- img_ → IMG_: prefix만 대문자로 바뀌는가
- 해시 5자리: PASS가 아닌 파일이 IMG_XXXXX로 바뀌는가
- 중복 suffix: 언더바 없이 1,2가 붙는가
- 한글 로그: UI 로그가 한글만 출력되는가
- error.log: 실패 원인을 추적할 수 있는가

**완료 기준**
- sample_input에서 위 규칙이 모두 확인된다.

---

## 13. 오픈 이슈/결정 필요(문서에 남길 것)

1) HEIC 변환 라이브러리 확정
- pillow-heif 설치/동작이 환경에 따라 실패할 수 있음
- v1에서 “HEIC 변환 실패 시 정책”을 명확히 해야 함(스킵/중단/원본 복사 등)

2) PNG 투명 처리 정책 고정
- 흰색 배경 합성(권장)으로 고정할지
- 검정/사용자 선택 옵션은 v1 범위 밖

3) 영상 creation_time 적용 범위
- v1은 대표 creation_time만 변경(DEV_GUIDE 기준)
- 트랙/미디어 단위 동기화는 v1.1 이후

---
