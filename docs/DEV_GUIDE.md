# DEV_GUIDE
## MDNS (Media Date & Name Standardizer) 개발 가이드

본 문서는 PRD 요구사항을 “구현 가능한 수준”으로 구체화한 개발자용 가이드다.
목표는 결정적(Deterministic) 처리, 원본 비파괴, 대량 처리 안정성, 패키징 일관성이다.

---

## 1. 레포/모듈 구조(권장)

아래 구조는 “GUI는 얇게(thin), 처리 로직은 두껍게(thick)”를 전제로 한다.

    mdns/
      src/
        main.py                 # 엔트리포인트 (GUI 실행)
        gui.py                  # Tkinter UI (기존 레이아웃 최대 유지)
        orchestrator.py         # 스캔/정렬/스코프 카운터/파이프라인 총괄
        scanner.py              # 파일 수집, 지원 확장자 필터링, result 경로 계산
        date_resolver.py        # 기준 날짜 폴더 탐색(상위로 올라감)
        naming.py               # 파일명 PASS/정규화/해시/중복처리
        logging_i18n.py         # 내부 이벤트코드 -> 한글 메시지 매핑
        paths.py                # 번들링 바이너리 경로 해석(Exe/소스 모두)
        errors.py               # 예외 타입 정의
        metadata/
          base.py               # 메타데이터 공통 인터페이스/결과 타입
          jpg_piexif.py         # JPG/JPEG: piexif read/write
          video_ffmpeg.py       # MP4/MOV: ffmpeg/ffprobe read/write
          raw_exiftool.py       # CR3: exiftool read/write
        convert/
          image_to_jpg.py       # PNG/HEIC -> JPG 변환
      assets/
        bin/
          windows/
            ffmpeg.exe
            ffprobe.exe
            exiftool.exe
          macos/
            ffmpeg
            ffprobe
            exiftool
          linux/
            ffmpeg
            ffprobe
            exiftool
      tests/
        test_date_resolver.py
        test_naming.py
        test_duplicate_suffix.py
        test_pipeline_smoke.py
      README.md
      PRD.md

핵심 원칙:
- GUI는 이벤트/표시 중심(얇게), 처리 로직은 모듈화(두껍게)
- 결과물은 항상 [Source]/result/ 이하에서만 생성/수정(원본 비파괴)

---

## 2. 요구사항을 코드로 고정해야 하는 정책

### 2.1 기준 날짜 탐색 규칙(상위 탐색)
- 시작점: 파일이 위치한 폴더
- 탐색: 부모 폴더로 올라가며 폴더명 prefix에서 날짜 추출
- 정규식: ^(\d{4}-\d{2}-\d{2})
- 가장 가까운(가장 하위) 날짜 폴더를 기준으로 사용
- 없으면:
  - 메타데이터 수정: 스킵
  - 파일명 표준화: 계속 수행

### 2.2 “기준 날짜 스코프”와 1초 증가 카운터
- 카운터 시작: 09:00:00
- 동일 스코프 내 파일마다 +1초
- 스코프 키(권장):
  - scope_key = (date_folder_full_path, date_ymd_string)
  - 동일 날짜라도 서로 다른 날짜 폴더 경로면 카운터를 분리하여 예측 가능성을 높인다.

### 2.3 처리 순서(결정성)
- 전체 대상 파일 목록은 처리 전 정렬한다.
- 정렬 키(권장):
  1) relative_path 오름차순
  2) filename 오름차순(대/소문자 무시 정렬)
- 이 정렬이 고정되어야 “시간 부여” 및 “중복 suffix”가 재실행 시 동일하게 나온다.

---

## 3. 전체 파이프라인(End-to-End)

### 3.1 2-pass 구조(진행률 정확도)
1) 1차 스캔: 대상 파일 목록 수집 + total_files 계산
2) 2차 처리: 정렬된 목록 순차 처리

### 3.2 파일 단위 처리 시퀀스(원본 비파괴)
각 파일 처리 흐름:

1) 기준 날짜 탐색
   - date_info = resolve_date(file_abs_path)
   - 결과: {found: bool, ymd: "YYYY-MM-DD", scope_key: ...}

2) 결과 디렉토리 계산
   - result_dir = source_root / "result" / relative_path_parent
   - 필요한 경우 mkdir(parents=True, exist_ok=True)

3) 결과 파일 생성(포맷별)
   - JPG/JPEG/MP4/MOV/AVI/CR3: 원본을 result로 복사(copy2 권장)
   - PNG/HEIC: result에 JPG로 변환해 생성(복사 대신 변환 생성)
     - 결과 확장자: .jpg (소문자 권장)

4) 메타데이터 보정
   - date_info 없으면: 스킵(로그)
   - 있으면: 현재 촬영일 YMD와 비교 후 PASS/SET 결정
   - SET이면: 해당 스코프 카운터값으로 YYYY:MM:DD 09:00:SS 부여

5) 파일명 표준화
   - PASS 패턴(대소문자 무관): IMG_1234, img_1234, IMG_1234a, img_1234ab
     - 다만 img_ prefix는 IMG_로 대문자 정규화 리네임
   - PASS가 아니면:
     - `MD5(file_content)[:5].upper() → IMG_<HASH5>`로 리네임
   - 중복 충돌 시:
     - 언더바 없이 숫자를 바로 붙임
       예: IMG_A1B2C.jpg 존재 → IMG_A1B2C1.jpg → IMG_A1B2C2.jpg

6) UI 로그/진행률 갱신(한글 로그)

7) 예외 발생 시
   - 파일 단위로 error.log 기록 후 다음 파일 진행(전체 중단 금지)

---

## 4. 포맷별 구현 가이드(실전 기준)

### 4.1 JPG/JPEG 메타데이터(piexif)
- Read 우선순위:
  - DateTimeOriginal 우선(없으면 “없음” 처리)
- Write 형식:
  - "YYYY:MM:DD HH:MM:SS" (Exif 표준)
- 재인코딩 금지:
  - 이미지 데이터를 다시 저장(재압축)하는 방식은 금지
  - piexif insert 방식으로 Exif만 수정

권장 태그(최소):
- 0th/Exif IFD의 DateTimeOriginal 중심
- v1에서는 “DateTimeOriginal 1개를 확실히”를 우선 목표로 두고, CreateDate/ModifyDate 동기화는 v1.1로 미룸

### 4.2 PNG/HEIC → JPG 변환 후 메타데이터 처리
- 목적:
  - result에 JPG 결과물 생성
  - 생성된 JPG에 piexif로 촬영일 설정
- 변환 라이브러리 권장:
  - PNG: Pillow
  - HEIC: pillow-heif(권장) 또는 heif 지원 모듈
- PNG 투명(알파) 처리:
  - JPEG는 투명 불가
  - 정책(권장): 흰색 배경으로 합성 후 저장
- JPG 저장 품질(권장 고정값):
  - quality=95, optimize=True
  - v1에서는 옵션화하지 않고 고정(추후 옵션)

### 4.3 CR3 메타데이터(ExifTool)
- ExifTool 번들링을 전제로 한다.
- Read:
  - DateTimeOriginal 계열을 읽되, 실패는 “없음”으로 처리
- Write(권장 최소 세트):
  - DateTimeOriginal, CreateDate, ModifyDate를 동일 값으로 설정
- 실행 방식:
  - subprocess는 리스트 인자 방식(쉘 금지)
  - 파일 경로 공백/특수문자 대비
- 실패 시:
  - 메타데이터 수정 실패 로그 + error.log 기록
  - 파일명 표준화는 계속 진행

### 4.4 MP4/MOV 메타데이터(ffmpeg/ffprobe)
- ffprobe로 현재 creation_time 조회
- ffmpeg로 creation_time 변경
- v1 범위:
  - MP4/MOV만 수정
  - AVI는 메타데이터 수정 스킵(로그), 파일명만 처리

주의(현실 이슈):
- 컨테이너/트랙/미디어 단위 메타데이터가 다를 수 있음
- v1은 “대표 creation_time 1개만 맞추는 최소 범위”로 구현하고 상세 동기화는 v1.1로 분리

---

## 5. 파일명 규칙(정확한 명세)

### 5.1 PASS 판정(대소문자 무관) + 대문자 정규화
- PASS 판정 개념:
  - 접두사: IMG_ 또는 img_
  - 식별자: 숫자 1개 이상
  - suffix: 영문 0개 이상(대/소문자 모두 허용)
- 예:
  - PASS: IMG_1234, img_1234, IMG_1234a, img_1234ab, IMG_1234AB
- PASS 처리 규칙(결정):
  - prefix가 img_이면 무조건 IMG_로 리네임(식별자/영문 suffix는 유지)
  - 영문 suffix의 대/소문자는 v1에서는 원본 유지

### 5.2 해시 이름 생성
- hash5 = md5(file_content).hexdigest()[:5].upper()
- 결과: `IMG_<hash5>.<ext>`
- ext 정책:
  - PNG/HEIC는 결과물이 JPG이므로 .jpg
  - 그 외는 원본 ext 유지(대소문자도 원본 유지 권장)

### 5.3 중복 처리(언더바 없음)
- 후보 이름이 이미 존재하면:
  - `IMG_<BASE>1, IMG_<BASE>2 ... 형태`
- 예:
  - IMG_A1B2C.jpg → IMG_A1B2C1.jpg → IMG_A1B2C2.jpg

---

## 6. 로그(한글 출력) 설계

### 6.1 내부 이벤트 코드(개발용)
- META_PASS, META_SET, META_SKIP_NO_DATE, META_FAIL_UNSUPPORTED, META_FAIL_WRITE
- NAME_PASS, NAME_SET_HASH, NAME_SET_UPPERCASE, NAME_DUPLICATE_SUFFIX
- CONVERT_PNG_TO_JPG, CONVERT_HEIC_TO_JPG, CONVERT_FAIL
- COPY_TO_RESULT, COPY_FAIL

### 6.2 UI 로그는 “한글 메시지”만 출력
- logging_i18n.py에서 code → 한국어 문장 매핑
- 권장 메시지 예:
  - META_PASS: “메타데이터: 날짜 일치(변경 없음)”
  - META_SET: “메타데이터: 폴더 날짜로 설정(09:00:SS)”
  - META_SKIP_NO_DATE: “메타데이터: 기준 날짜 폴더를 찾지 못해 건너뜀”
  - META_FAIL_UNSUPPORTED: “메타데이터: 지원하지 않는 형식이라 건너뜀”
  - META_FAIL_WRITE: “메타데이터: 수정 실패(오류 로그 확인)”
  - NAME_PASS: “파일명: 표준 형식 확인(유지)”
  - NAME_SET_UPPERCASE: “파일명: 소문자 img_ → 대문자 IMG_로 변경”
  - NAME_SET_HASH: “파일명: 해시 기반으로 변경(IMG_XXXXX)”
  - NAME_DUPLICATE_SUFFIX: “파일명: 중복 발생 → 숫자 접미사 추가(…1, …2)”
  - CONVERT_HEIC_TO_JPG: “변환: HEIC → JPG 변환”
  - CONVERT_PNG_TO_JPG: “변환: PNG → JPG 변환”
  - CONVERT_FAIL: “변환: 실패(오류 로그 확인)”
  - COPY_TO_RESULT: “복사: result 폴더로 복사”
  - COPY_FAIL: “복사: 실패(오류 로그 확인)”

---

## 7. 외부 바이너리 번들링(중요)

### 7.1 경로 해석(paths.py)
- 개발 실행(소스)과 PyInstaller 실행(배포 exe)에서 경로가 달라진다.
- 원칙:
  - PyInstaller 실행 시: sys._MEIPASS 기준으로 assets/bin 경로를 찾는다.
  - 소스 실행 시: 프로젝트 루트 기준 상대 경로로 찾는다.
- 바이너리 탐색 실패 시:
  - UI에 “필수 도구를 찾지 못했습니다” 안내 + error.log 기록 + 해당 기능 스킵

### 7.2 실행 정책
- ffmpeg/ffprobe/exiftool 호출은 subprocess 사용
- 타임아웃(권장):
  - ffprobe: 10초
  - ffmpeg: 기본 60초(대용량은 180초까지)
  - exiftool: 30초
- 실패 시:
  - UI에는 한글 요약 + error.log에 상세 기록

---

## 8. GUI 스레드 안정성

- 워커 스레드에서 직접 Tk 위젯을 갱신하지 않는다.
- 권장 구조:
  - 워커는 Queue에 (progress, message) 이벤트를 push
  - GUI는 root.after(...)로 주기적으로 Queue를 비우며 UI 반영

---

## 9. 테스트 전략(최소)

### 9.1 단위 테스트
- date_resolver: 상위 탐색 및 정규식 처리
- naming: PASS/대문자화/해시/중복 suffix
- duplicate suffix: ...1, ...2 규칙(언더바 없음)

### 9.2 스모크 테스트(통합)
- 임시 폴더 트리 생성(날짜폴더/하위폴더)
- JPG + PNG + HEIC(가능 시) + MP4/MOV(가능 시) + CR3(있으면)
- result 구조 유지
- 재실행 시 멱등성(변경 최소화) 확인

---
