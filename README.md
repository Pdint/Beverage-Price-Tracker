# 📊 이커머스 음료 체감 최저가 통합 분석기 (Beverage Price Tracker)

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Flet](https://img.shields.io/badge/Flet-GUI-purple?logo=flet)
![DuckDB](https://img.shields.io/badge/DuckDB-Embedded_OLAP-yellow)
![Status](https://img.shields.io/badge/Status-Completed-success)

**데이터베이스 기말 텀 프로젝트 **

이커머스 쇼핑몰의 복잡한 프로모션, 기본 배송비, 포인트 적립률을 전산 수학적으로 통합 연산하여 **'최종 1캔당 체감 최저가'**를 직관적으로 분석해 주는 데스크톱 GUI 애플리케이션입니다.

## 🌟 핵심 기능 (Key Features)

1. **다중 테이블 LEFT JOIN 집계 연산**
   - 단편적인 가격 조회를 넘어 `Price_Records`를 드라이빙 테이블로 삼아 `Products`, `Platforms`, `Promotions` 총 4개의 테이블을 동시에 결합하는 고성능 JOIN 질의를 수행합니다.
2. **BCNF 정규화 기반 무결성 설계**
   - 갱신 이상(Update Anomaly)을 방지하기 위해 할인 행사 엔티티와 쇼핑몰 엔티티를 명확히 분리하여 완벽한 보이스-코드 정규형(BCNF) 스키마를 구축했습니다.
3. **Flet 데스크톱 GUI & 데이터 시각화**
   - CLI 환경의 한계를 벗어나, Flet 프레임워크를 활용해 사용자가 직관적으로 검색하고 결과를 랭킹(오름차순) 형태로 확인할 수 있는 모던 대시보드를 제공합니다. (로컬 이미지 에셋 연동 완료)
4. **관리자 데이터 적재(CRUD) 시스템 통합**
   - 애플리케이션 내에서 신규 음료 마스터 데이터 및 일별 가격 이력을 안전하게 삽입(INSERT)할 수 있으며, 외래키 참조 무결성을 검증합니다.

## 🛠 기술 스택 (Tech Stack)
- **Language:** Python 3.14
- **Database:** DuckDB (Embedded Columnar Vectorized Database)
- **GUI Framework:** Flet (v0.22+)
- **Data Manipulation:** Pandas
- **Modeling Tool:** VSCode ERD Editor (Crow's Foot Notation)

## 📁 프로젝트 파일 구조 (Project Structure)
```text
📦 Beverage_Price_Tracker
 ┣ 📂 assets/                 # 음료 캔 이미지 저장 폴더 (coke.png 등)
 ┣ 📜 app.py                  # 메인 GUI 애플리케이션 및 JOIN 비즈니스 로직
 ┣ 📜 init_db.sql             # BCNF 스키마 빌드 및 3개월 치 과거 더미 데이터 세팅 스크립트
 ┗ 📜 README.md               # 프로젝트 명세서

 ---
```   

### 🚀 2. GitHub 릴리즈(Release) 진행 가이드

프로젝트 평가 요구사항인 **"(5) GitHub Public Repository 증빙"**을 완벽하게 마무리하기 위한 단계입니다.
