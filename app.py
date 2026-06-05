# -*- coding: utf-8 -*-
"""
이커머스 음료 최저가 분석기 (Flet + DuckDB)
- 완벽 스크롤 및 드롭다운 메뉴 높이 제한 적용 버전
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
    
    # ⭐ [핵심 추가] 페이지 전체에 위아래(수직) 스크롤 활성화! (데이터가 많아져도 무한 스크롤 가능)
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
                        ft.DataCell(ft.Text(str(row['record_date']))),
                    ], color=bg_color
                )
            )
        page.update()

    # =========================================================================
    # [뷰 2] 데이터 적재 (관리자)
    # =========================================================================
    def show_toast(msg):
        page.snack_bar = ft.SnackBar(ft.Text(msg), show_close_icon=True)
        page.snack_bar.open = True
        page.update()

    prod_name = ft.TextField(label="신규 상품명 입력", expand=True)
    
    def insert_product(e):
        if not prod_name.value: return show_toast("상품명은 필수입니다.")
        con = duckdb.connect(DB_FILE)
        try:
            next_id = con.execute("SELECT COALESCE(MAX(product_id), 0) + 1 FROM Products").fetchone()[0]
            con.execute("INSERT INTO Products (product_id, product_name, image_path) VALUES (?, ?, 'default.png')", [next_id, prod_name.value])
            con.commit()
            show_toast(f"음료 [{prod_name.value}] 등록 성공!")
            prod_name.value = ""
            load_dropdowns() 
        except Exception as ex:
            show_toast(f"등록 실패: {ex}")
        finally:
            con.close()

    # ⭐ [핵심 추가] max_menu_height=250 을 추가하여 드롭다운 내부에 스크롤바가 생기도록 강제 제한!
    rec_prod_dropdown = ft.Dropdown(label="음료 선택 ▼", width=250, menu_height=250)
    rec_plat_dropdown = ft.Dropdown(label="플랫폼 선택 ▼", width=200, menu_height=250)
    
    rec_can = ft.TextField(label="수량(캔)", width=100) 
    rec_price = ft.TextField(label="원가(원)", width=120)
    rec_date = ft.TextField(label="날짜(YYYY-MM-DD)", value="2026-05-10", width=160)

    def load_dropdowns():
        if not os.path.exists(DB_FILE): return
        con = duckdb.connect(DB_FILE, read_only=True)
        
        prods = con.execute("SELECT product_id, product_name FROM Products").fetchall()
        rec_prod_dropdown.options = [ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in prods]
        
        plats = con.execute("SELECT platform_id, platform_name FROM Platforms").fetchall()
        rec_plat_dropdown.options = [ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in plats]
        
        con.close()
        page.update()

    def insert_record(e):
        if not rec_prod_dropdown.value or not rec_plat_dropdown.value or not rec_price.value or not rec_can.value: 
            return show_toast("모든 칸을 입력하세요.")
        con = duckdb.connect(DB_FILE)
        try:
            next_rec_id = con.execute("SELECT COALESCE(MAX(record_id), 0) + 1 FROM Price_Records").fetchone()[0]
            con.execute("INSERT INTO Price_Records (record_id, product_id, platform_id, promo_id, base_price, can_count, record_date) VALUES (?, ?, ?, NULL, ?, ?, ?)", 
                        [next_rec_id, int(rec_prod_dropdown.value), int(rec_plat_dropdown.value), int(rec_price.value), int(rec_can.value), rec_date.value])
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
            # ⭐ 열(가로 항목)이 모니터를 넘어가면 무조건 가로 스크롤 생성
            ft.Row([data_table], scroll=ft.ScrollMode.ALWAYS) 
        ])
    )

    admin_view = ft.Container(
        visible=False,
        content=ft.Column([
            ft.Row([
                ft.Text("⚙️ 관리자 데이터 적재 패널", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                ft.TextButton("◀ 대시보드로 복귀", on_click=lambda e: switch_view(True))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Text("▣ 신규 음료 등록 (Products)", weight=ft.FontWeight.BOLD),
            ft.Row([prod_name, ft.ElevatedButton("음료 등록", on_click=insert_product, color=ft.Colors.GREEN_800)]),
            ft.Container(height=20),
            ft.Text("▣ 일별 가격 적재 (Price_Records)", weight=ft.FontWeight.BOLD),
            ft.Row([rec_prod_dropdown, rec_plat_dropdown, rec_can, rec_price, rec_date, ft.ElevatedButton("가격 적재", on_click=insert_record, color=ft.Colors.BLUE_800)]),
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