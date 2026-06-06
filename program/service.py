"""
[비즈니스 로직 계층 (Service Layer)]
- UI(Controller)와 DB(Repository) 사이의 중간 관리자 역할을 합니다.
- 입력값의 유효성(Validation)을 검증하고, 데이터베이스 저장소에 작업을 위임합니다.
"""

import pandas as pd
from repository import (IProductRepository, IPlatformRepository, 
                        IPromotionRepository, IPriceRecordRepository, IPriceQueryRepository)

class ApplicationService:
    # 생성자를 통한 의존성 주입(DI, Dependency Injection)
    # 구체적인 DB 기술(DuckDB) 대신 인터페이스 규격을 주입받아 결합도를 낮춤
    def __init__(self, 
                 prod_repo: IProductRepository,
                 plat_repo: IPlatformRepository,
                 promo_repo: IPromotionRepository,
                 price_repo: IPriceRecordRepository,
                 query_repo: IPriceQueryRepository):
        self.prod_repo = prod_repo
        self.plat_repo = plat_repo
        self.promo_repo = promo_repo
        self.price_repo = price_repo
        self.query_repo = query_repo

    def fetch_dashboard_data(self, keyword: str) -> pd.DataFrame:
        """대시보드 표출을 위한 최저가 분석 데이터 요청 위임"""
        if not keyword: keyword = ""
        return self.query_repo.find_lowest_prices_by_keyword(keyword)

    def add_product(self, name, vol, img):
        """상품 등록 전 유효성 검사 및 저장 위임"""
        if not name: raise ValueError("상품명은 필수입니다.")
        if not img: img = "default.png"
        self.prod_repo.save(name, vol, img)

    def add_platform(self, name, fee_str):
        """플랫폼 등록 전 유효성 검사 및 저장 위임"""
        if not name: raise ValueError("플랫폼명은 필수입니다.")
        fee = int(fee_str) if fee_str.isdigit() else 0
        self.plat_repo.save(name, fee)

    def add_promotion(self, plat_id, name, start_d, end_d, disc_str, rew_str):
        """프로모션 등록 전 데이터 형변환 및 저장 위임"""
        if not name or not plat_id: raise ValueError("행사명과 플랫폼은 필수입니다.")
        disc = float(disc_str) if disc_str else 0.0
        rew = float(rew_str) if rew_str else 0.0
        self.promo_repo.save(int(plat_id), name, start_d, end_d, disc, rew)

    def add_price_record(self, prod_id, plat_id, promo_id, price_str, can_str, date_str):
        """가격 이력 트랜잭션 적재 전 필수값 검사 및 NULL 매핑 처리"""
        if not prod_id or not plat_id or not price_str or not can_str:
            raise ValueError("필수 칸을 모두 입력하세요.")
        # '행사 없음' 선택 시 프로모션 ID를 내부적으로 NULL로 변환
        p_id = None if promo_id in (None, "NULL") else int(promo_id)
        self.price_repo.save(int(prod_id), int(plat_id), p_id, int(price_str), int(can_str), date_str)

    def get_dropdowns(self):
        """관리자 패널의 드롭다운 UI 구성을 위해 3개의 마스터 데이터를 일괄 조회"""
        return self.prod_repo.find_all(), self.plat_repo.find_all(), self.promo_repo.find_all()