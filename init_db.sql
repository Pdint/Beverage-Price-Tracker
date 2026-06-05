-- ============================================================================
-- 데이터베이스 구축 및 초기 데이터 적재 SQL 스크립트 
-- ============================================================================

-- 테이블 생성 (DDL)
CREATE TABLE Products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    volume VARCHAR(20),
    image_path VARCHAR(255)
);

CREATE TABLE Platforms (
    platform_id INTEGER PRIMARY KEY,
    platform_name VARCHAR(50) NOT NULL,
    base_shipping_fee INTEGER DEFAULT 0
);

CREATE TABLE Promotions (
    promo_id INTEGER PRIMARY KEY,
    platform_id INTEGER NOT NULL,
    promo_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    discount_rate DECIMAL(3,2) DEFAULT 0.00,
    reward_points_rate DECIMAL(3,2) DEFAULT 0.00,
    FOREIGN KEY (platform_id) REFERENCES Platforms(platform_id)
);

CREATE TABLE Price_Records (
    record_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    promo_id INTEGER,
    base_price INTEGER NOT NULL,
    can_count INTEGER NOT NULL,
    record_date DATE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Products(product_id),
    FOREIGN KEY (platform_id) REFERENCES Platforms(platform_id),
    FOREIGN KEY (promo_id) REFERENCES Promotions(promo_id)
);

-- 초기 데모 데이터 삽입 (DML)

-- 음료 데이터 (브랜드 제외)
INSERT INTO Products VALUES (1, '코카 콜라 제로 캔 350ml', '350ml', 'zero_coke_350.png');
INSERT INTO Products VALUES (2, '펩시 제로 라임 355ml', '355ml', 'zero_pepsi_lime_355.png');
INSERT INTO Products VALUES (3, '칠성사이다 제로 캔 355ml', '355ml', 'zero_cider_355.png');
INSERT INTO Products VALUES (4, '코카 콜라 제로 캔 250ml', '250ml', 'zero_coke_250.png');
INSERT INTO Products VALUES (5, '펩시 제로 라임 500ml', '500ml', 'zero_pepsi_lime_500.png');
INSERT INTO Products VALUES (6, '펩시 제로 라임 250ml', '250ml', 'zero_pepsi_lime_250.png');
INSERT INTO Products VALUES (7, '닥터 페퍼 제로 355ml', '355ml', 'Dr_Pepper_355.png');

-- 플랫폼 데이터
INSERT INTO Platforms VALUES (1, 'G마켓', 3000);
INSERT INTO Platforms VALUES (2, '쿠팡 (와우)', 0);
INSERT INTO Platforms VALUES (3, '11번가', 2500);
INSERT INTO Platforms VALUES (4, '옥션', 3000);
INSERT INTO Platforms VALUES (7, 'SSG.COM', 3000);
INSERT INTO Platforms VALUES (9, '롯데온', 2500);
INSERT INTO Platforms VALUES (10, '쿠팡 (일반)', 3000);
INSERT INTO Platforms VALUES (11, '네이버 쇼핑', 3000);
INSERT INTO Platforms VALUES (12, '카카오 톡딜', 0);
INSERT INTO Platforms VALUES (13, '네이버 쇼핑(멤버십)', 0);

-- 프로모션 데이터
INSERT INTO Promotions VALUES (101, 1, '상반기 빅스마일데이', '2024-05-08', '2024-05-15', 0.15, 0.02);
INSERT INTO Promotions VALUES (102, 3, '그랜드 십일절', '2024-11-01', '2024-11-11', 0.10, 0.05);
INSERT INTO Promotions VALUES (104, 10, '쿠팡 로켓배송 할인', '2024-05-01', '2024-05-31', 0.08, 0.01);
INSERT INTO Promotions VALUES (105, 12, '카카오 톡딜 특가 행사', '2024-05-01', '2024-05-31', 0.20, 0.05);
INSERT INTO Promotions VALUES (106, 13, '네이버 쇼핑 멤버십 할인', '2024-05-26', '2024-05-26', 0.18, 0.04);

-- =========================================================================
-- [가격 이력 데이터] 2026년 3월 ~ 5월 시계열 데이터 적재
-- =========================================================================

-- 1. 평상시 가격 (2026년 3월 15일 - 행사 없음)
-- 코카콜라 제로 355ml (평상시 24캔 기준 22,000원 ~ 24,000원대)
INSERT INTO Price_Records VALUES (1, 1, 1, NULL, 24000, 24, '2026-03-15'); -- G마켓
INSERT INTO Price_Records VALUES (2, 1, 2, NULL, 22500, 24, '2026-03-15'); -- 쿠팡(와우)
INSERT INTO Price_Records VALUES (3, 1, 3, NULL, 23000, 24, '2026-03-15'); -- 11번가
-- 펩시 제로 라임 355ml (코카콜라보다 보통 약간 저렴함)
INSERT INTO Price_Records VALUES (4, 2, 2, NULL, 19800, 24, '2026-03-15'); -- 쿠팡(와우)
INSERT INTO Price_Records VALUES (5, 2, 11, NULL, 21000, 24, '2026-03-15'); -- 네이버 쇼핑

-- 2. 소규모 게릴라 행사 (2026년 4월 20일 - 쿠팡 로켓배송 할인)
-- 코카콜라 제로 250ml & 펩시 제로 355ml (쿠팡 104번 프로모션 적용)
INSERT INTO Price_Records VALUES (6, 4, 10, 104, 18000, 30, '2026-04-20'); -- 코카콜라 250ml 30캔
INSERT INTO Price_Records VALUES (7, 2, 2, 104, 17500, 24, '2026-04-20'); -- 펩시 라임 355ml 24캔
INSERT INTO Price_Records VALUES (8, 1, 1, NULL, 23800, 24, '2026-04-20'); -- G마켓(행사 없음)
INSERT INTO Price_Records VALUES (9, 3, 3, NULL, 20000, 24, '2026-04-20'); -- 칠성사이다 11번가

-- 3. ★ 대형 프로모션 기간 (2026년 5월 10일 - G마켓 빅스마일데이 역대급 핫딜)
-- G마켓(1)에 101번(빅스마일데이) 프로모션이 걸리면서 타 플랫폼 대비 압도적으로 저렴한 가격 형성
INSERT INTO Price_Records VALUES (10, 1, 1, 101, 24000, 24, '2026-05-10'); -- 코카콜라 355ml (할인적용시 1캔당 800원대)
INSERT INTO Price_Records VALUES (11, 2, 1, 101, 21000, 24, '2026-05-10'); -- 펩시 라임 355ml (할인적용시 1캔당 700원대)
INSERT INTO Price_Records VALUES (12, 7, 1, 101, 19000, 24, '2026-05-10'); -- 닥터 페퍼 355ml (할인적용시 1캔당 600원대)
-- 경쟁사들의 방어 가격 (행사가 없거나 약해서 밀림)
INSERT INTO Price_Records VALUES (13, 1, 2, NULL, 21900, 24, '2026-05-10'); -- 쿠팡(와우)
INSERT INTO Price_Records VALUES (14, 1, 3, NULL, 23500, 24, '2026-05-10'); -- 11번가

-- 4. 특정 플랫폼 전용 행사 (2026년 5월 26일 - 네이버 쇼핑 멤버십 데이)
-- 네이버 쇼핑(13)에 106번 프로모션 적용
INSERT INTO Price_Records VALUES (15, 1, 13, 106, 25000, 24, '2026-05-26'); -- 코카콜라 355ml (기본가는 비싸지만 적립률 높았음)
INSERT INTO Price_Records VALUES (16, 2, 13, 106, 22000, 24, '2026-05-26'); -- 펩시 라임 355ml
INSERT INTO Price_Records VALUES (17, 3, 12, 105, 18500, 30, '2026-05-26'); -- 칠성사이다 카카오 톡딜(105번 행사) 적용
INSERT INTO Price_Records VALUES (18, 1, 2, NULL, 22500, 24, '2026-05-26'); -- 쿠팡(와우) 평상시 복귀