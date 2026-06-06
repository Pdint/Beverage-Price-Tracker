"""
[데이터 접근 계층 (Repository Layer)]
- 데이터베이스(DuckDB)와의 통신을 전담하는 모듈입니다.
- 상위 계층(Service)이 DB 인프라에 종속되지 않도록 ABC 모듈을 활용하여 인터페이스를 추상화하였습니다.
- 기초 데이터 CRUD 인터페이스 4개와 JOIN 전담 인터페이스 1개로 구성되어 있습니다.
"""

import duckdb
import pandas as pd
import os
from abc import ABC, abstractmethod

DB_FILE = 'beverage_prices.duckdb'
SQL_SCRIPT_FILE = 'init_db.sql'

def init_database():
    """
    초기 데이터베이스 파일(duckdb)이 없을 경우, 
    SQL 스크립트 파일을 읽어와 초기 스키마와 테이블을 생성합니다.
    """
    if os.path.exists(DB_FILE): return
    try:
        if os.path.exists(SQL_SCRIPT_FILE):
            with open(SQL_SCRIPT_FILE, 'r', encoding='utf-8') as file:
                sql_script = file.read()
            con = duckdb.connect(DB_FILE)
            con.execute(sql_script)
            con.commit()
            con.close()
    except Exception as e:
        print(f"DB 초기화 중 에러: {e}")

# =========================================================================
# [1] 단위 테이블 CRUD 인터페이스 (추상화 규격)
# - 교수님 가이드라인 반영: 테이블별 인터페이스 분리 및 save/find 명명 규칙 적용
# =========================================================================
class IProductRepository(ABC):
    @abstractmethod
    def save(self, name: str, vol: str, img: str): 
        """신규 상품 마스터 등록 (CREATE)"""
        pass
    @abstractmethod
    def find_all(self) -> list: 
        """전체 상품 목록 조회 - 드롭다운 메뉴용 (READ)"""
        pass

class IPlatformRepository(ABC):
    @abstractmethod
    def save(self, name: str, fee: int): 
        """신규 판매처 플랫폼 마스터 등록 (CREATE)"""
        pass
    @abstractmethod
    def find_all(self) -> list: 
        """전체 플랫폼 목록 조회 (READ)"""
        pass

class IPromotionRepository(ABC):
    @abstractmethod
    def save(self, plat_id: int, name: str, start_d: str, end_d: str, disc: float, rew: float): 
        """기간 한정 프로모션 행사 등록 (CREATE)"""
        pass
    @abstractmethod
    def find_all(self) -> list: 
        """전체 프로모션 목록 조회 (READ)"""
        pass

class IPriceRecordRepository(ABC):
    @abstractmethod
    def save(self, prod_id: int, plat_id: int, promo_id: int, price: int, can: int, date: str): 
        """특정 일자의 매핑 가격 이력 트랜잭션 적재 (CREATE)"""
        pass

# =========================================================================
# [2] Join 전담 인터페이스 (다중 테이블 결합)
# =========================================================================
class IPriceQueryRepository(ABC):
    @abstractmethod
    def find_lowest_prices_by_keyword(self, keyword: str) -> pd.DataFrame: 
        """사용자 검색어 기반 다중 조인 및 최저가 분석 결과 반환"""
        pass


# =========================================================================
# [3] 실제 데이터베이스 구현체 클래스들 (Implementation)
# - 위에서 정의한 규격(Interface)을 바탕으로 실제 DuckDB SQL을 실행합니다.
# =========================================================================
class DuckDbProductRepository(IProductRepository):
    def save(self, name: str, vol: str, img: str):
        con = duckdb.connect(DB_FILE)
        # PK(Primary Key) 자동 증가 로직
        next_id = con.execute("SELECT COALESCE(MAX(product_id), 0) + 1 FROM Products").fetchone()[0]
        con.execute("INSERT INTO Products VALUES (?, ?, ?, ?)", [next_id, name, vol, img])
        con.commit(); con.close()
        
    def find_all(self) -> list:
        if not os.path.exists(DB_FILE): return []
        con = duckdb.connect(DB_FILE, read_only=True)
        res = con.execute("SELECT product_id, product_name FROM Products").fetchall()
        con.close(); return res

class DuckDbPlatformRepository(IPlatformRepository):
    def save(self, name: str, fee: int):
        con = duckdb.connect(DB_FILE)
        next_id = con.execute("SELECT COALESCE(MAX(platform_id), 0) + 1 FROM Platforms").fetchone()[0]
        con.execute("INSERT INTO Platforms VALUES (?, ?, ?)", [next_id, name, fee])
        con.commit(); con.close()
        
    def find_all(self) -> list:
        if not os.path.exists(DB_FILE): return []
        con = duckdb.connect(DB_FILE, read_only=True)
        res = con.execute("SELECT platform_id, platform_name FROM Platforms").fetchall()
        con.close(); return res

class DuckDbPromotionRepository(IPromotionRepository):
    def save(self, plat_id: int, name: str, start_d: str, end_d: str, disc: float, rew: float):
        con = duckdb.connect(DB_FILE)
        next_id = con.execute("SELECT COALESCE(MAX(promo_id), 0) + 1 FROM Promotions").fetchone()[0]
        con.execute("INSERT INTO Promotions VALUES (?, ?, ?, ?, ?, ?, ?)", [next_id, plat_id, name, start_d, end_d, disc, rew])
        con.commit(); con.close()
        
    def find_all(self) -> list:
        if not os.path.exists(DB_FILE): return []
        con = duckdb.connect(DB_FILE, read_only=True)
        res = con.execute("SELECT promo_id, promo_name FROM Promotions").fetchall()
        con.close(); return res

class DuckDbPriceRecordRepository(IPriceRecordRepository):
    def save(self, prod_id: int, plat_id: int, promo_id: int, price: int, can: int, date: str):
        con = duckdb.connect(DB_FILE)
        next_id = con.execute("SELECT COALESCE(MAX(record_id), 0) + 1 FROM Price_Records").fetchone()[0]
        con.execute("INSERT INTO Price_Records VALUES (?, ?, ?, ?, ?, ?, ?)", [next_id, prod_id, plat_id, promo_id, price, can, date])
        con.commit(); con.close()

class DuckDbPriceQueryRepository(IPriceQueryRepository):
    def __init__(self): 
        # 분석 레포지토리 생성 시 초기 DB 세팅 확인
        init_database()
    
    def find_lowest_prices_by_keyword(self, keyword: str) -> pd.DataFrame:
        if not os.path.exists(DB_FILE): return pd.DataFrame()
        con = duckdb.connect(DB_FILE, read_only=True)
        
        # [핵심 로직] 4개 테이블 다중 JOIN 및 체감가 수학적 연산 (CTE 활용)
        query = """
            WITH Calculated AS (
                SELECT 
                    p.image_path, p.product_name, pl.platform_name,
                    COALESCE(pro.promo_name, '행사 없음') AS promo_name,
                    pr.base_price, pr.can_count, pr.record_date,
                    CAST(pr.base_price * (1 - COALESCE(pro.discount_rate, 0)) AS INTEGER) AS discount_price,
                    CAST(pr.base_price * COALESCE(pro.reward_points_rate, 0) AS INTEGER) AS reward,
                    CAST(pr.base_price * (1 - COALESCE(pro.discount_rate, 0)) 
                         - (pr.base_price * COALESCE(pro.reward_points_rate, 0)) 
                         + pl.base_shipping_fee AS INTEGER) AS final_price
                FROM Price_Records pr
                LEFT JOIN Products p ON pr.product_id = p.product_id
                LEFT JOIN Platforms pl ON pr.platform_id = pl.platform_id
                LEFT JOIN Promotions pro ON pr.promo_id = pro.promo_id
                WHERE p.product_name LIKE ?
            )
            -- 도출된 총 체감가를 캔 수로 나누어 1캔당 단가(unit_price) 도출 및 오름차순 정렬
            SELECT *, CAST(final_price / can_count AS INTEGER) AS unit_price
            FROM Calculated ORDER BY unit_price ASC;
        """
        try: 
            # 쿼리 결과를 Pandas DataFrame으로 변환하여 반환
            df = con.execute(query, [f"%{keyword}%"]).df()
        except Exception: 
            df = pd.DataFrame() # 예외 발생 시 빈 데이터프레임 반환
        finally: 
            con.close()
        return df