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

-- 가격 이력 데이터
INSERT INTO Price_Records VALUES (1, 1, 1, 101, 24000, 24, '2026-05-10');
INSERT INTO Price_Records VALUES (2, 1, 2, NULL, 22000, 30, '2026-05-10');
INSERT INTO Price_Records VALUES (3, 1, 3, NULL, 23500, 30, '2026-05-10');
INSERT INTO Price_Records VALUES (4, 2, 1, 101, 21000, 30, '2026-05-10');
INSERT INTO Price_Records VALUES (5, 2, 2, NULL, 19500, 24, '2026-05-10');