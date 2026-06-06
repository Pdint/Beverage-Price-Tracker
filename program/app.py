"""
[프레젠테이션 계층 (Presentation Layer / UI)]
- 사용자에게 화면(Flet)을 표출하고 입력을 받아 Service 계층에 전달하는 역할을 합니다.
- 데이터베이스 접근 로직(SQL)이 UI 코드에서 완전히 배제되어 유지보수성이 극대화되었습니다.
"""

# -*- coding: utf-8 -*-
import flet as ft
import os
# DB 규격에 맞는 실제 구현체 부품들을 가져옵니다.
from repository import (DuckDbProductRepository, DuckDbPlatformRepository, 
                        DuckDbPromotionRepository, DuckDbPriceRecordRepository, 
                        DuckDbPriceQueryRepository)
from service import ApplicationService

def main(page: ft.Page):
    # Flet 앱 전역 설정
    page.title = "이커머스 음료 체감 최저가 분석기"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 30
    page.window.width = 1200 
    page.window.height = 750
    page.scroll = ft.ScrollMode.AUTO 

    # [의존성 주입 설정] 5개의 개별 저장소 부품을 생성하여 Service에 조립
    service = ApplicationService(
        prod_repo=DuckDbProductRepository(),
        plat_repo=DuckDbPlatformRepository(),
        promo_repo=DuckDbPromotionRepository(),
        price_repo=DuckDbPriceRecordRepository(),
        query_repo=DuckDbPriceQueryRepository()
    )

    # =========================================================================
    # [뷰 1] 메인 대시보드 (최저가 랭킹 출력 화면)
    # =========================================================================
    search_input = ft.TextField(label="음료명 검색 (예: 콜라)", value="", expand=True)
    
    # 조회 결과를 렌더링할 데이터 테이블 UI 정의
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

    def update_dashboard(e=None):
        """검색어 입력 시 Service를 통해 분석 결과를 받아 표를 업데이트하는 이벤트 핸들러"""
        keyword = search_input.value
        # 서비스 계층 호출 (SQL 구문 없이 깔끔한 요청 처리)
        df = service.fetch_dashboard_data(keyword)
        
        data_table.rows.clear()
        
        # 검색 결과가 존재할 경우에만 UI 렌더링 (결과 없으면 빈 표 유지)
        if not df.empty:
            for index, row in df.iterrows():
                has_promo = row['promo_name'] != '행사 없음'
                # 랭킹 1위(최저가) 행에 하이라이트 색상 부여
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

    search_input.on_submit = update_dashboard

    # =========================================================================
    # [뷰 2] 관리자 데이터 적재 패널 (마스터 및 트랜잭션 CRUD 화면)
    # =========================================================================
    def show_toast(msg):
        """작업 성공/실패 여부를 알리는 팝업 메시지 출력"""
        page.snack_bar = ft.SnackBar(ft.Text(msg), show_close_icon=True)
        page.snack_bar.open = True
        page.update()

    # 1. 신규 음료 등록 UI 
    prod_name = ft.TextField(label="신규 상품명 입력", width=250)
    prod_vol = ft.TextField(label="용량 (예: 355ml)", width=120)
    prod_img = ft.TextField(label="이미지 파일명 (예: coke.png)", width=250)
    
    def on_insert_product(e):
        try:
            service.add_product(prod_name.value, prod_vol.value, prod_img.value)
            show_toast(f"음료 [{prod_name.value}] 등록 성공!")
            prod_name.value = ""; prod_vol.value = ""; prod_img.value = ""
            load_dropdowns() # 새 항목 반영을 위한 드롭다운 리로드
        except Exception as ex:
            show_toast(f"등록 실패: {ex}")

    # 2. 신규 플랫폼 등록 UI
    plat_name = ft.TextField(label="플랫폼명 입력 (예: 마켓컬리)", width=250)
    plat_fee = ft.TextField(label="기본 배송비 (예: 3000)", value="0", width=150)

    def on_insert_platform(e):
        try:
            service.add_platform(plat_name.value, plat_fee.value)
            show_toast(f"플랫폼 [{plat_name.value}] 등록 성공!")
            plat_name.value = ""; plat_fee.value = "0"
            load_dropdowns()
        except Exception as ex:
            show_toast(f"등록 실패: {ex}")

    # 3. 신규 프로모션 등록 UI
    promo_name = ft.TextField(label="행사명 입력", width=250)
    promo_plat_dropdown = ft.Dropdown(label="플랫폼 선택 ▼", width=200, menu_height=250)
    promo_start = ft.TextField(label="시작일(YYYY-MM-DD)", value="2026-06-01", width=180)
    promo_end = ft.TextField(label="종료일(YYYY-MM-DD)", value="2026-06-15", width=180)
    promo_disc = ft.TextField(label="할인율(예: 0.15)", width=130)
    promo_rew = ft.TextField(label="적립률(예: 0.05)", width=130)

    def on_insert_promotion(e):
        try:
            service.add_promotion(promo_plat_dropdown.value, promo_name.value, promo_start.value, promo_end.value, promo_disc.value, promo_rew.value)
            show_toast(f"행사 [{promo_name.value}] 등록 성공!")
            promo_name.value = ""; promo_disc.value = ""; promo_rew.value = ""
            load_dropdowns()
        except Exception as ex:
            show_toast(f"등록 실패: {ex}")

    # 4. 가격 이력 트랜잭션 적재 UI
    rec_prod_dropdown = ft.Dropdown(label="음료 선택 ▼", width=250, menu_height=250)
    rec_plat_dropdown = ft.Dropdown(label="플랫폼 선택 ▼", width=200, menu_height=250)
    rec_promo_dropdown = ft.Dropdown(label="적용 행사(선택) ▼", width=200, menu_height=250)
    rec_can = ft.TextField(label="수량(캔)", width=100) 
    rec_price = ft.TextField(label="원가(원)", width=120)
    rec_date = ft.TextField(label="날짜(YYYY-MM-DD)", value="2026-06-05", width=160)

    def on_insert_record(e):
        try:
            service.add_price_record(rec_prod_dropdown.value, rec_plat_dropdown.value, rec_promo_dropdown.value, rec_price.value, rec_can.value, rec_date.value)
            show_toast("가격 이력 적재 성공!")
            rec_price.value = ""; rec_can.value = "" 
        except Exception as ex:
            show_toast(f"적재 실패: {ex}")

    def load_dropdowns():
        """화면 전환 시마다 DB 최신 데이터를 읽어와 각 드롭다운 메뉴를 갱신합니다."""
        prods, plats, promos = service.get_dropdowns()
        
        rec_prod_dropdown.options = [ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in prods]
        
        plat_opts = [ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in plats]
        rec_plat_dropdown.options = plat_opts
        promo_plat_dropdown.options = plat_opts
        
        # 행사 선택 안함(평상시) 옵션을 위한 하드코딩 추가
        rec_promo_dropdown.options = [ft.dropdown.Option(key="NULL", text="행사 없음 (평상시)")] + [ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in promos]
        page.update()

# =========================================================================
    # [화면(View) 컨테이너 및 전환 제어기]
    # =========================================================================
    dashboard_view = ft.Container(
        expand=True, # 🌟 추가: 화면 전체를 쓰도록 확장
        content=ft.Column([
            ft.Row([
                ft.Text("📊 이커머스 1캔당 단가 분석 대시보드", size=24, weight=ft.FontWeight.BOLD),
                ft.TextButton("⚙️ 데이터 적재(관리자)", on_click=lambda e: switch_view(False))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([search_input, ft.ElevatedButton("최저가 검색", on_click=update_dashboard, icon=ft.Icons.SEARCH)]),
            
            # 수정: 가로/세로 스크롤이 모두 완벽하게 작동하도록 Row 컨테이너 속성 강화
            ft.Row(
                [data_table], 
                scroll=ft.ScrollMode.AUTO, # 내용이 넘칠 때만 스크롤바 자동 생성
                expand=True # 표가 남은 공간을 꽉 채우도록 설정
            ) 
        ], expand=True) # 추가: Column도 화면을 꽉 채우도록 설정
    )

    admin_view = ft.Container(
        visible=False, # 초기 렌더링 시 관리자 패널은 숨김 처리
        content=ft.Column([
            ft.Row([
                ft.Text("⚙️ 관리자 데이터 적재 패널", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                ft.TextButton("◀ 대시보드로 복귀", on_click=lambda e: switch_view(True))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            
            ft.Text("▣ 신규 음료 등록 (Products)", weight=ft.FontWeight.BOLD),
            ft.Row([prod_name, prod_vol, prod_img, ft.ElevatedButton("음료 등록", on_click=on_insert_product, color=ft.Colors.GREEN_800)]),
            ft.Container(height=10),
            
            ft.Text("▣ 신규 쇼핑몰 플랫폼 등록 (Platforms)", weight=ft.FontWeight.BOLD),
            ft.Row([plat_name, plat_fee, ft.ElevatedButton("플랫폼 등록", on_click=on_insert_platform, color=ft.Colors.TEAL_800)]),
            ft.Container(height=10),
            
            ft.Text("▣ 신규 프로모션 등록 (Promotions)", weight=ft.FontWeight.BOLD),
            ft.Row([promo_name, promo_plat_dropdown, promo_start, promo_end]),
            ft.Row([promo_disc, promo_rew, ft.ElevatedButton("프로모션 등록", on_click=on_insert_promotion, color=ft.Colors.ORANGE_800)]),
            ft.Container(height=10),
            
            ft.Text("▣ 일별 가격 적재 (Price_Records)", weight=ft.FontWeight.BOLD),
            ft.Row([rec_prod_dropdown, rec_plat_dropdown, rec_promo_dropdown]),
            ft.Row([rec_can, rec_price, rec_date, ft.ElevatedButton("가격 적재", on_click=on_insert_record, color=ft.Colors.BLUE_800)]),
        ])
    )

    def switch_view(show_dashboard):
        """대시보드 화면과 관리자 패널 화면의 가시성(visible) 토글 제어"""
        dashboard_view.visible = show_dashboard
        admin_view.visible = not show_dashboard
        if show_dashboard: 
            update_dashboard()
        else:
            load_dropdowns() 
        page.update()

    # 최종 앱 화면 구성
    page.add(dashboard_view, admin_view)
    load_dropdowns()
    update_dashboard()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")