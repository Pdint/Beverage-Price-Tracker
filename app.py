# -*- coding: utf-8 -*-
"""
이커머스 음료 최저가 분석기 (Flet + DuckDB)
"""

import flet as ft
import duckdb
import os

DB_FILE = 'beverage_prices.duckdb'
SQL_SCRIPT_FILE = 'init_db.sql'

def init_database():
    if os.path.exists(DB_FILE): return
    try:
        with open(SQL_SCRIPT_FILE, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        con = duckdb.connect(DB_FILE)
        con.execute(sql_script)
        con.commit()
        con.close()
        print(f"[{SQL_SCRIPT_FILE}] 스크립트로 DB 초기화 완료.")
    except Exception as e:
        print(f"DB 초기화 중 에러: {e}")

def main(page: ft.Page) -> None:
    init_database()
    page.title = "이커머스 음료 체감 최저가 분석기"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 30
    page.window.width = 1200 
    page.window.height = 750
    page.scroll = ft.ScrollMode.AUTO 

    # =========================================================================
    # [뷰 1] 메인 대시보드
    # =========================================================================
    search_input = ft.TextField(label="음료명 검색 (예: 콜라)", value="", expand=True)
    search_input.on_submit = lambda e: update_dashboard()

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("이미지", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("상품명", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("판매처", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("적용 행사", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("할인/적립 내역", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("수량(캔)", weight=ft.FontWeight.BOLD)), 
            ft.DataColumn(ft.Text("총 체감가", weight=ft.FontWeight.BOLD)), 
            ft.DataColumn(ft.Text("1캔당 단가", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)), 
            ft.DataColumn(ft.Text("기록 일자", weight=ft.FontWeight.BOLD)),
        ],
        rows=[]
    )

    def update_dashboard():
        keyword = search_input.value
        if not os.path.exists(DB_FILE): return

        con = duckdb.connect(DB_FILE, read_only=True)
        
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
            SELECT 
                *,
                CAST(final_price / can_count AS INTEGER) AS unit_price
            FROM Calculated
            ORDER BY unit_price ASC;
        """
        
        try:
            df = con.execute(query, [f"%{keyword}%"]).df()
        except Exception as e:
            print(f"DB Error: {e}")
            con.close()
            return
        con.close()

        data_table.rows.clear()
        for index, row in df.iterrows():
            has_promo = row['promo_name'] != '행사 없음'
            bg_color = ft.Colors.RED_50 if index == 0 else None 
            
            data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Image(src=f"/{row['image_path']}", width=50, height=50)),
                        ft.DataCell(ft.Text(row['product_name'])),
                        ft.DataCell(ft.Text(row['platform_name'])),
                        ft.DataCell(ft.Text(row['promo_name'], color=ft.Colors.BLUE_700 if has_promo else None)), 
                        ft.DataCell(ft.Text(f"{row['discount_price']:,}원 (적립: {row['reward']:,})")),
                        ft.DataCell(ft.Text(f"{row['can_count']}캔")),
                        ft.DataCell(ft.Text(f"{row['final_price']:,}원")),
                        ft.DataCell(ft.Text(f"{row['unit_price']:,}원", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700, size=16)),
                        ft.DataCell(ft.Text(str(row['record_date'])[:10])),
                    ], color=bg_color
                )
            )
        page.update()

    # =========================================================================
    # [뷰 2] 데이터 적재 (관리자) - 업그레이드됨!
    # =========================================================================
    def show_toast(msg):
        page.snack_bar = ft.SnackBar(ft.Text(msg), show_close_icon=True)
        page.snack_bar.open = True
        page.update()

    # 1. 음료 등록 필드 (이미지, 용량 추가)
    prod_name = ft.TextField(label="신규 상품명 입력", width=250)
    prod_vol = ft.TextField(label="용량 (예: 355ml)", width=120)
    prod_img = ft.TextField(label="이미지 파일명 (예: coke.png)", width=250)
    
    def insert_product(e):
        if not prod_name.value: return show_toast("상품명은 필수입니다.")
        img_path = prod_img.value if prod_img.value else "default.png"
        con = duckdb.connect(DB_FILE)
        try:
            next_id = con.execute("SELECT COALESCE(MAX(product_id), 0) + 1 FROM Products").fetchone()[0]
            con.execute("INSERT INTO Products (product_id, product_name, volume, image_path) VALUES (?, ?, ?, ?)", 
                        [next_id, prod_name.value, prod_vol.value, img_path])
            con.commit()
            show_toast(f"음료 [{prod_name.value}] 등록 성공!")
            prod_name.value = ""; prod_vol.value = ""; prod_img.value = ""
            load_dropdowns() 
        except Exception as ex:
            show_toast(f"등록 실패: {ex}")
        finally:
            con.close()

    # 2. 프로모션 등록 필드 (신규 추가)
    promo_name = ft.TextField(label="행사명 입력", width=250)
    promo_plat_dropdown = ft.Dropdown(label="플랫폼 선택 ▼", width=200, menu_height=250)
    promo_start = ft.TextField(label="시작일(YYYY-MM-DD)", value="2026-06-01", width=180)
    promo_end = ft.TextField(label="종료일(YYYY-MM-DD)", value="2026-06-15", width=180)
    promo_disc = ft.TextField(label="할인율(예: 0.15)", width=130)
    promo_rew = ft.TextField(label="적립률(예: 0.05)", width=130)

    def insert_promotion(e):
        if not promo_name.value or not promo_plat_dropdown.value: return show_toast("행사명과 플랫폼은 필수입니다.")
        con = duckdb.connect(DB_FILE)
        try:
            next_id = con.execute("SELECT COALESCE(MAX(promo_id), 0) + 1 FROM Promotions").fetchone()[0]
            disc = float(promo_disc.value) if promo_disc.value else 0.0
            rew = float(promo_rew.value) if promo_rew.value else 0.0
            con.execute("INSERT INTO Promotions (promo_id, platform_id, promo_name, start_date, end_date, discount_rate, reward_points_rate) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        [next_id, int(promo_plat_dropdown.value), promo_name.value, promo_start.value, promo_end.value, disc, rew])
            con.commit()
            show_toast(f"행사 [{promo_name.value}] 등록 성공!")
            promo_name.value = ""; promo_disc.value = ""; promo_rew.value = ""
            load_dropdowns() # 등록된 행사가 '가격 적재'의 드롭다운에 바로 뜨도록 새로고침
        except Exception as ex:
            show_toast(f"등록 실패: {ex}")
        finally:
            con.close()

    # 3. 가격 이력 적재 필드 (행사 드롭다운 추가)
    rec_prod_dropdown = ft.Dropdown(label="음료 선택 ▼", width=250, menu_height=250)
    rec_plat_dropdown = ft.Dropdown(label="플랫폼 선택 ▼", width=200, menu_height=250)
    rec_promo_dropdown = ft.Dropdown(label="적용 행사(선택) ▼", width=200, menu_height=250)
    rec_can = ft.TextField(label="수량(캔)", width=100) 
    rec_price = ft.TextField(label="원가(원)", width=120)
    rec_date = ft.TextField(label="날짜(YYYY-MM-DD)", value="2026-06-05", width=160)

    def load_dropdowns():
        if not os.path.exists(DB_FILE): return
        con = duckdb.connect(DB_FILE, read_only=True)
        
        prods = con.execute("SELECT product_id, product_name FROM Products").fetchall()
        rec_prod_dropdown.options = [ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in prods]
        
        plats = con.execute("SELECT platform_id, platform_name FROM Platforms").fetchall()
        plat_options = [ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in plats]
        rec_plat_dropdown.options = plat_options
        promo_plat_dropdown.options = plat_options # 프로모션 등록용 플랫폼 목록도 채워줌
        
        promos = con.execute("SELECT promo_id, promo_name FROM Promotions").fetchall()
        # 행사는 없을 수도 있으므로 '행사 없음(NULL)' 옵션을 맨 위에 추가
        rec_promo_dropdown.options = [ft.dropdown.Option(key="NULL", text="행사 없음 (평상시)")] + [ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in promos]
        
        con.close()
        page.update()

    def insert_record(e):
        if not rec_prod_dropdown.value or not rec_plat_dropdown.value or not rec_price.value or not rec_can.value: 
            return show_toast("필수 칸을 모두 입력하세요.")
        con = duckdb.connect(DB_FILE)
        try:
            next_rec_id = con.execute("SELECT COALESCE(MAX(record_id), 0) + 1 FROM Price_Records").fetchone()[0]
            # '행사 없음'을 선택했으면 NULL로, 아니면 해당 ID로 변환
            p_id = None if rec_promo_dropdown.value in (None, "NULL") else int(rec_promo_dropdown.value)
            
            con.execute("INSERT INTO Price_Records (record_id, product_id, platform_id, promo_id, base_price, can_count, record_date) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                        [next_rec_id, int(rec_prod_dropdown.value), int(rec_plat_dropdown.value), p_id, int(rec_price.value), int(rec_can.value), rec_date.value])
            con.commit()
            show_toast("가격 이력 적재 성공!")
            rec_price.value = ""; rec_can.value = "" 
        except Exception as ex:
            show_toast(f"적재 실패: {ex}")
        finally:
            con.close()

    # =========================================================================
    # [뷰 전환 제어기]
    # =========================================================================
    dashboard_view = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("📊 이커머스 1캔당 단가 분석 대시보드", size=24, weight=ft.FontWeight.BOLD),
                ft.TextButton("⚙️ 데이터 적재(관리자)", on_click=lambda e: switch_view(False))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([search_input, ft.ElevatedButton("최저가 검색", on_click=lambda e: update_dashboard(), icon=ft.Icons.SEARCH)]),
            ft.Row([data_table], scroll=ft.ScrollMode.ALWAYS) 
        ])
    )

    # 관리자 화면 레이아웃 (섹션별로 깔끔하게 정리)
    admin_view = ft.Container(
        visible=False,
        content=ft.Column([
            ft.Row([
                ft.Text("⚙️ 관리자 데이터 적재 패널", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                ft.TextButton("◀ 대시보드로 복귀", on_click=lambda e: switch_view(True))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            
            ft.Text("▣ 신규 음료 등록 (Products)", weight=ft.FontWeight.BOLD),
            ft.Row([prod_name, prod_vol, prod_img, ft.ElevatedButton("음료 등록", on_click=insert_product, color=ft.Colors.GREEN_800)]),
            ft.Container(height=10),
            
            ft.Text("▣ 신규 프로모션 등록 (Promotions)", weight=ft.FontWeight.BOLD),
            ft.Row([promo_name, promo_plat_dropdown, promo_start, promo_end]),
            ft.Row([promo_disc, promo_rew, ft.ElevatedButton("프로모션 등록", on_click=insert_promotion, color=ft.Colors.ORANGE_800)]),
            ft.Container(height=10),
            
            ft.Text("▣ 일별 가격 적재 (Price_Records)", weight=ft.FontWeight.BOLD),
            ft.Row([rec_prod_dropdown, rec_plat_dropdown, rec_promo_dropdown]),
            ft.Row([rec_can, rec_price, rec_date, ft.ElevatedButton("가격 적재", on_click=insert_record, color=ft.Colors.BLUE_800)]),
        ])
    )

    def switch_view(show_dashboard):
        dashboard_view.visible = show_dashboard
        admin_view.visible = not show_dashboard
        if show_dashboard: 
            update_dashboard()
        else:
            load_dropdowns() 
        page.update()

    page.add(dashboard_view, admin_view)
    load_dropdowns()
    update_dashboard()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")