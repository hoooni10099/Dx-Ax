# Actuator Mini MES 요구사항 명세서

| 항목 | 내용 |
|---|---|
| 문서 버전 | `v1.0` |
| 대상 시스템 | Actuator Mini MES 1차 구현 |
| 최종 갱신일 | 2026-08-05 |
| 구현 기술 | Python, SQLite, Streamlit, pandas, Altair |
| 생산 대상 | 전기차 HVAC 에어믹스 도어 액추에이터 |
| 문서 상태 | 현재 구현 기준 |

## 1. 목적

이 문서는 `app.py`, `pages/`, `src/`, `sql/schema.sql`에 구현된 Actuator Mini MES의 기능, 업무 규칙, 데이터 요구사항과 완료 조건을 정의합니다. README가 프로젝트 소개와 실행 방법을 담당한다면, 이 문서는 시스템이 어떤 조건에서 어떤 동작을 해야 하는지를 명시하는 기준 문서입니다.

## 2. 시스템 범위

가상의 액추에이터 생산라인에서 자재 LOT 입고부터 작업지시, 제품 Serial 발급, 공정실적, 자재 소비, EOL 검사, 생산 완료와 양방향 추적까지 관리합니다.

### 포함 범위

1. 품목·BOM·공정·Routing 기준정보 조회
2. 자재 LOT 입고와 상태 관리
3. 작업지시 생성과 제품 Serial 발급
4. Routing 순서에 따른 공정실적 등록
5. 공정별 자재 LOT 소비 등록
6. EOL 검사 측정값 저장과 PASS·FAIL 판정
7. 제품·작업지시 상태 관리
8. 생산·공정·품질·재고 현황 시각화
9. Serial 정방향 추적과 LOT 역방향 추적
10. SQLite 제약조건과 트랜잭션 기반 데이터 무결성

### 제외 범위

- 로그인, 사용자 권한, 작업자별 감사 이력
- 설비·금형·치공구 상세 관리
- 구매발주, 창고 이동, 출하, ERP 연동
- 재작업, 재검사, 폐기, 보류 프로세스
- PLC·센서·바코드 장비 실시간 통신
- BOM·Routing 버전 관리
- OEE, SPC, AI 품질예측
- 다중 사용자 서버 배포

## 3. 사용자 역할

1차 구현은 인증과 권한을 적용하지 않지만 다음 역할의 업무를 가정합니다.

| 역할 | 주요 업무 |
|---|---|
| 관리자 | 품목, BOM, 공정, Routing 확인 |
| 자재 담당자 | 자재 LOT 입고, 차단·해제, 재고 확인 |
| 생산 관리자 | 작업지시 생성, Serial 발급, 진척 확인 |
| 작업자 | 공정실적과 자재 LOT 투입 등록 |
| 품질 담당자 | EOL 측정값 입력, 판정·품질 추이 확인 |
| 추적 담당자 | Serial·LOT 기준 생산이력 조회 |

## 4. 핵심 데이터와 상태

### 데이터 엔터티

| 테이블 | 역할 |
|---|---|
| `item` | 완제품·자재 품목 |
| `process` | 표준 공정 |
| `routing_step` | 제품별 공정 순서 |
| `bom` | 제품·자재·투입 공정과 소요수량 |
| `material_lot` | 자재 입고 LOT와 상태 |
| `work_order` | 제품별 생산 계획 |
| `product_serial` | 개별 완제품 식별자와 상태 |
| `process_history` | Serial별 공정실적 |
| `material_consumption` | Serial·공정별 실제 LOT 소비 |
| `eol_test_result` | EOL 측정값과 최종 판정 |

### 제품 Serial 상태

| 상태 | 의미 | 전이 조건 |
|---|---|---|
| `CREATED` | Serial 발급 완료 | Serial 생성 |
| `IN_PROGRESS` | 생산 진행 중 | 첫 일반 공정 등록 |
| `PASS` | 합격 생산 종료 | EOL PASS 후 완료 공정 등록 |
| `FAIL` | 불합격 생산 종료 | EOL 최종 FAIL |

### 작업지시 상태

| 상태 | 의미 | 전이 조건 |
|---|---|---|
| `PLANNED` | 생산 계획 등록 | 작업지시 생성 |
| `IN_PROGRESS` | Serial 발급 또는 생산 진행 | Serial 발급·첫 생산 시작 |
| `COMPLETED` | 계획된 Serial 전체 종결 | 발급수량이 계획수량과 같고 모두 PASS·FAIL |
| `CANCELLED` | 작업지시 취소 | 취소 처리 |

## 5. 공통 업무 규칙

- 품목코드, 공정코드, 작업지시번호, LOT 번호, Serial 번호는 고유해야 합니다.
- 수량은 양수여야 하며 자재 소비량은 LOT 가용수량을 초과할 수 없습니다.
- 날짜는 유효한 ISO 형식으로 저장하고 작업지시 납기일은 과거일 수 없습니다.
- 생산 대상은 활성 `PRODUCT`, 입고·투입 대상은 활성 `MATERIAL`이어야 합니다.
- 제품은 활성·필수 Routing의 `sequence_no` 순서대로 진행합니다.
- 동일 Serial과 Routing 단계의 공정실적은 한 번만 등록할 수 있습니다.
- 이력이 연결된 데이터는 물리 삭제보다 상태 변경으로 관리합니다.
- 여러 테이블을 함께 변경하는 업무는 하나의 트랜잭션으로 처리합니다.
- SQLite 외래키를 연결마다 활성화하고 `UNIQUE`, `CHECK`, `NOT NULL` 제약을 적용합니다.

## 6. 기능 요구사항

### FR-01 기준정보 조회

시스템은 품목, BOM, 표준 공정과 제품별 Routing을 조회해야 합니다.

- 완제품과 자재를 구분하여 표시합니다.
- 제품별 BOM 자재, 소요수량과 투입 공정을 표시합니다.
- Routing은 공정 순서대로 표시합니다.
- 비활성 여부를 식별할 수 있어야 합니다.

관련 화면: `pages/01_품목_생산기준_조회.py`  
관련 서비스: `src/master_data_service.py`

### FR-02 자재 LOT 입고·상태 관리

시스템은 자재 LOT를 등록하고 입고·사용·가용수량을 조회해야 합니다.

- LOT 번호는 중복될 수 없습니다.
- `MATERIAL` 품목만 입고할 수 있습니다.
- 입고수량은 1 이상이어야 합니다.
- 상태는 `AVAILABLE`, `EXHAUSTED`, `BLOCKED` 중 하나입니다.
- 차단 시 사유와 시각을 기록하고 차단 LOT는 생산에 투입할 수 없습니다.
- 가용수량은 `received_qty - SUM(consumed_qty)`로 계산합니다.

관련 화면: `pages/02_자재_LOT_관리.py`  
관련 서비스: `src/material_lot_service.py`

### FR-03 작업지시 생성

시스템은 활성 완제품, 계획수량과 납기일을 기준으로 작업지시를 생성해야 합니다.

- 작업지시번호는 공백 제거 후 대문자로 저장합니다.
- 계획수량은 1 이상의 정수입니다.
- 납기일은 `YYYY-MM-DD` 형식이며 오늘보다 이전일 수 없습니다.
- 신규 상태는 `PLANNED`입니다.
- 동일 작업지시번호를 중복 등록할 수 없습니다.

관련 화면: `pages/03_작업지시_관리.py`  
관련 서비스: `src/work_order_service.py`

### FR-04 제품 Serial 발급

시스템은 작업지시 잔여 계획수량 범위에서 Serial을 일괄 발급해야 합니다.

- 작업지시 상태가 `PLANNED` 또는 `IN_PROGRESS`일 때만 발급합니다.
- 누적 발급수량은 계획수량을 초과할 수 없습니다.
- Serial 형식은 `{품목코드}-{YYYYMMDD}-{4자리 순번}`입니다.
- 같은 품목·발급일 기준 기존 최대 순번 다음부터 발급합니다.
- 동시 발급 중복을 방지하기 위해 즉시 쓰기 트랜잭션을 사용합니다.
- 신규 Serial 상태는 `CREATED`입니다.

### FR-05 공정실적 등록

시스템은 각 Serial에 대해 다음 미완료 일반 공정만 등록해야 합니다.

- `PROC-EOL`, `PROC-COMPLETE`는 일반 공정 화면에서 제외합니다.
- 제품 Routing에 없거나 순서가 아닌 공정은 등록할 수 없습니다.
- 첫 공정 등록 시 Serial과 작업지시를 `IN_PROGRESS`로 변경합니다.
- 결과는 `PASS` 또는 `FAIL`입니다.
- 같은 Serial·Routing 단계는 중복 등록할 수 없습니다.
- 공정 등록과 자재 소비는 동일 트랜잭션으로 처리합니다.

관련 화면: `pages/04_공정실적_관리.py`  
관련 서비스: `src/process_service.py`, `src/process_history_service.py`

### FR-06 자재 LOT 소비

시스템은 선택한 공정에 연결된 활성 BOM 자재만 투입해야 합니다.

- BOM의 `input_routing_step_id`가 현재 공정과 일치해야 합니다.
- 선택 LOT의 자재 품목이 BOM 자재와 일치해야 합니다.
- 상태가 `AVAILABLE`이고 가용수량이 필요수량 이상인 LOT만 표시합니다.
- 투입수량은 BOM `required_qty`를 기준으로 기록합니다.
- 동일 Serial·LOT·Routing 단계의 소비 기록은 중복될 수 없습니다.
- 잔량이 소진되면 LOT 상태를 `EXHAUSTED`로 관리할 수 있어야 합니다.

### FR-07 EOL 검사

시스템은 이전 필수 공정이 모두 완료된 Serial에 대해서만 EOL 검사를 허용해야 합니다.

필수 측정값:

- 정방향 동작 여부
- 역방향 동작 여부
- 정방향 동작시간(ms)
- 역방향 동작시간(ms)
- 최대 구동전류(mA)
- 센서형 제품의 목표각도·실제각도

현재 판정 기준:

| 항목 | PASS 기준 |
|---|---|
| 정·역방향 동작 | 모두 정상 |
| 정·역방향 동작시간 | 각각 1,000ms 이하 |
| 최대 구동전류 | 1,500mA 이하 |
| 위치오차 | 3.0° 이하 |

- 하나 이상의 기준을 위반하면 최종 결과는 `FAIL`입니다.
- 실패 사유를 항목별 문자열로 기록합니다.
- EOL 공정실적과 상세 측정값은 하나의 트랜잭션으로 저장합니다.
- FAIL이면 Serial을 즉시 `FAIL`로 종결하고 완료 공정으로 진행하지 않습니다.

관련 화면: `pages/05_EOL_검사_생산완료.py`  
관련 서비스: `src/process_service.py`, `src/eol_service.py`

### FR-08 생산 완료

시스템은 EOL PASS 후 다음 공정이 `PROC-COMPLETE`인 Serial만 생산 완료할 수 있어야 합니다.

- 완료 공정의 PASS 실적을 생성합니다.
- Serial을 `PASS`로 변경하고 완료시각을 기록합니다.
- 발급수량이 계획수량과 같고 모든 Serial이 `PASS` 또는 `FAIL`이면 작업지시를 `COMPLETED`로 변경합니다.
- 아직 발급되지 않았거나 진행 중인 Serial이 있으면 작업지시를 완료하지 않습니다.

### FR-09 생산 현황

시스템은 작업지시별 계획·발급·대기·진행·PASS·FAIL·종결 수량을 집계해야 합니다.

- 진행률은 `종결수량 / 계획수량 × 100`입니다.
- Serial별 완료 공정수, 전체 필수 공정수, 마지막·다음 공정을 표시합니다.
- 메인 대시보드에는 계획 대비 완료, 품질 결과, 공정별 WIP와 최근 7일 생산량을 표시합니다.

관련 화면: `app.py`, `pages/06_생산_현황.py`  
관련 서비스: `src/dashboard_service.py`, `src/production_status_service.py`

### FR-10 EOL 품질 모니터링

시스템은 제품 또는 작업지시 기준으로 EOL 결과를 분석해야 합니다.

- 검사수량, PASS·FAIL 수량과 합격률을 제공합니다.
- 최대전류 추이와 허용 기준선을 표시합니다.
- 정·역방향 동작시간 분포를 표시합니다.
- 빈 데이터, 숫자 변환 실패와 조회 오류를 사용자에게 안내합니다.

### FR-11 Serial 정방향 추적

Serial 하나를 기준으로 다음 정보를 조회해야 합니다.

- 제품과 작업지시 정보
- 현재 Serial 상태
- Routing별 공정 결과와 처리시각
- 공정별 투입 자재 LOT와 수량
- EOL 측정값, 판정과 실패 사유

관련 화면: `pages/07_Serial_정방향_추적.py`  
관련 서비스: `src/traceability_service.py`

### FR-12 자재 LOT 역방향 추적

자재 LOT 하나를 기준으로 해당 LOT가 투입된 모든 제품을 조회해야 합니다.

- LOT 품목, 입고·사용·가용수량과 상태를 표시합니다.
- 소비된 Serial, 작업지시, 투입 공정과 수량을 표시합니다.
- 영향 제품의 현재 상태와 EOL 결과를 연결하여 표시합니다.

관련 화면: `pages/08_자재_LOT_역방향_추적.py`  
관련 서비스: `src/traceability_service.py`

## 7. 비기능 요구사항

### NFR-01 사용성

- 화면, 입력 안내와 오류 메시지는 한국어로 제공합니다.
- 사용 가능한 품목·작업지시·Serial·LOT는 선택 UI를 우선 사용합니다.
- 빈 조회 결과와 처리 실패 원인을 사용자에게 명확히 안내합니다.

### NFR-02 데이터 무결성

- 모든 DB 연결에서 `PRAGMA foreign_keys = ON`을 적용합니다.
- 식별자 중복은 DB `UNIQUE` 제약과 서비스 검증으로 방지합니다.
- 상태와 수량은 `CHECK` 제약과 서비스 검증으로 제한합니다.
- 복수 테이블 변경은 트랜잭션으로 원자성을 보장합니다.
- SQL에는 파라미터 바인딩을 사용합니다.

### NFR-03 유지보수성

- Streamlit 화면, 업무 서비스, DB 연결을 분리합니다.
- 공통 UI는 `src/ui.py`, 공통 DB 연결은 `src/db.py`를 사용합니다.
- 조회 결과는 pandas DataFrame, 업무 처리 결과는 명확한 반환값 또는 `ServiceResult`로 제공합니다.
- 현재 실행 코드와 실험·레거시 코드를 구분할 수 있어야 합니다.

### NFR-04 실행 환경

- Windows 11, WSL, macOS·Linux의 Python 가상환경에서 실행할 수 있어야 합니다.
- 별도 DB 서버 없이 `sql/mes_dev.db`로 실행할 수 있어야 합니다.
- `sql/schema.sql`과 `sql/seed.sql`로 DB 구조와 초기 데이터를 재구성할 수 있어야 합니다.

### NFR-05 성능·동시성

- 학습용 데이터 규모에서 등록과 조회가 체감 지연 없이 완료되어야 합니다.
- Serial 발급은 `BEGIN IMMEDIATE`를 사용해 동시 중복을 방지합니다.
- 추적에 사용되는 고유 식별자와 외래키 관계를 활용해 조회합니다.

### NFR-06 테스트 가능성

- 테스트는 원본 DB가 아닌 임시 복사본을 사용해야 합니다.
- 정상 생산과 EOL FAIL 흐름을 자동 검증해야 합니다.
- DB 외래키와 무결성 검사를 검증해야 합니다.

## 8. 화면·서비스·데이터 매핑

| 사용자 흐름 | 화면 | 주요 서비스 | 주요 테이블 |
|---|---|---|---|
| 기준정보 확인 | 01 화면 | `master_data_service` | `item`, `bom`, `process`, `routing_step` |
| 자재 입고 | 02 화면 | `material_lot_service` | `item`, `material_lot`, `material_consumption` |
| 작업지시·Serial | 03 화면 | `work_order_service` | `work_order`, `product_serial`, `item` |
| 공정실적·자재투입 | 04 화면 | `process_service` | `routing_step`, `process_history`, `material_consumption` |
| EOL·완료 | 05 화면 | `process_service`, `eol_service` | `process_history`, `eol_test_result`, `product_serial` |
| 생산 현황 | 메인·06 화면 | `dashboard_service`, `production_status_service` | `work_order`, `product_serial`, `process_history` |
| Serial 추적 | 07 화면 | `traceability_service` | 생산이력 관련 전체 테이블 |
| LOT 추적 | 08 화면 | `traceability_service` | `material_lot`, `material_consumption`, 생산이력 테이블 |

## 9. 인수 검증 시나리오

### 시나리오 A: 정상 생산

1. 활성 완제품, BOM, Routing과 가용 자재 LOT를 준비합니다.
2. 계획수량 2개의 작업지시를 생성합니다.
3. Serial 2개를 발급합니다.
4. Routing 순서대로 자재 LOT와 일반 공정 PASS 실적을 등록합니다.
5. EOL 기준 이내 측정값을 등록합니다.
6. 완료 공정을 처리합니다.
7. Serial은 `PASS`, 작업지시는 전체 종결 후 `COMPLETED`인지 확인합니다.

### 시나리오 B: EOL 불합격

1. 일반 공정을 모두 완료합니다.
2. 동작불량, 시간·전류·위치오차 중 하나 이상의 기준 초과값을 입력합니다.
3. EOL과 Serial 상태가 `FAIL`이고 실패 사유가 기록되는지 확인합니다.
4. 완료 공정 대상에서 제외되는지 확인합니다.

### 시나리오 C: 업무 규칙 차단

- 중복 작업지시·LOT·Serial 등록
- 계획수량 초과 Serial 발급
- 과거 납기일 작업지시 생성
- Routing 순서 위반
- BOM에 없는 자재 또는 차단 LOT 투입
- 가용수량 초과 소비
- 선행 공정 미완료 EOL 검사
- EOL 미합격 제품 생산 완료

위 동작은 저장되지 않아야 하며 사용자에게 원인을 안내해야 합니다.

### 시나리오 D: 양방향 추적

- Serial 검색 시 작업지시, 모든 공정, 투입 LOT와 EOL 결과가 연결되어야 합니다.
- LOT 검색 시 해당 LOT가 사용된 모든 Serial과 품질 결과가 누락 없이 표시되어야 합니다.

## 10. 완료 정의

다음 조건을 만족하면 1차 구현 요구사항을 충족한 것으로 판단합니다.

- FR-01부터 FR-12까지의 핵심 기능이 화면과 서비스에서 동작합니다.
- 정상 생산, EOL FAIL, 업무 규칙 차단과 양방향 추적 시나리오를 재현할 수 있습니다.
- `schema.sql`과 `seed.sql`로 실행 가능한 DB를 구성할 수 있습니다.
- README만으로 환경 구성과 실행 방법을 이해할 수 있습니다.
- 테스트가 임시 DB를 사용하고 정상·불량 생산 흐름을 검증합니다.
- README, 요구사항, 코드의 상태·판정·식별번호 규칙이 일치합니다.

## 11. 후속 개선 요구사항

- EOL 기준값을 코드 상수에서 DB 설정으로 이동
- BOM·Routing 버전과 적용일 관리
- 재작업·재검사·보류·폐기 상태 추가
- 사용자 인증, 역할별 권한과 변경 감사 로그
- 설비·작업자·불량코드 기준정보 추가
- PostgreSQL 등 서버형 DB와 다중 사용자 동시성 지원
- GitHub Actions 기반 문법검사·자동 테스트
- 현재 서비스와 실험·레거시 파일 구조 정리

## 12. 문서 변경 원칙

- 업무 규칙이 바뀌면 요구사항, 스키마, 서비스, 테스트와 README를 함께 검토합니다.
- 코드와 문서가 다를 경우 운영 의도를 먼저 확정한 뒤 둘 중 하나를 수정합니다.
- 새로운 기능은 기능 요구사항, 입력·출력, 예외 조건, 데이터 영향과 인수 시나리오를 함께 추가합니다.
