import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- 1. 삼성전자 TV 표준 데이터베이스 ---
# 최근 3년 주요 모델(Neo QLED, OLED, Micro LED) 기반 평균 SET 스펙
SAMSUNG_TV_DB = {
    43: {"weight": 9.4, "width": 961, "height": 559, "depth": 20},
    55: {"weight": 15.0, "width": 1227, "height": 706, "depth": 25},
    65: {"weight": 24.2, "width": 1446, "height": 828, "depth": 25},
    70: {"weight": 28.5, "width": 1550, "height": 870, "depth": 30},
    75: {"weight": 34.6, "width": 1670, "height": 957, "depth": 30},
    85: {"weight": 43.5, "width": 1892, "height": 1082, "depth": 35},
    98: {"weight": 68.0, "width": 2185, "height": 1249, "depth": 40},
    115: {"weight": 133.6, "width": 2565, "height": 1467, "depth": 50}
}

def run_app():
    st.set_page_config(page_title="TV Stand Stability Analyzer", layout="wide")
    
    st.title("🛡️ TV Stand Stability & Tipping Simulator")
    st.markdown("삼성전자 TV 디자인 기초 기구 설계 검토용 AI 툴")
    st.divider()

    # --- Sidebar: 입력 파라미터 ---
    st.sidebar.header("📋 STEP 1: TV SET 정보")
    inch = st.sidebar.selectbox("TV 사이즈 선택 (Inch)", list(SAMSUNG_TV_DB.keys()), index=2)
    
    # DB에서 기본값 로드 및 수동 수정 허용
    default_spec = SAMSUNG_TV_DB[inch]
    weight = st.sidebar.number_input("SET 중량 (kg)", value=default_spec["weight"])
    h_set = st.sidebar.number_input("SET 높이 (mm)", value=default_spec["height"])
    d_set = st.sidebar.number_input("SET 두께 (mm)", value=default_spec["depth"])
    
    st.sidebar.header("📐 STEP 2: Stand 설계")
    design_type = st.sidebar.selectbox("디자인 컨셉", 
                                     ["Central Square (Plate)", "Edge Y-Stand (Branch)", "OLED Hexagon"])
    
    # 스탠드 치수 설정
    s_width = st.sidebar.slider("Stand 폭 (가로 mm)", 100, 2000, 450)
    s_depth = st.sidebar.slider("Stand 깊이 (앞뒤 mm)", 50, 600, 300)
    neck_h = st.sidebar.slider("Neck 높이 (지면~SET하단 mm)", 0, 200, 50)

    st.sidebar.header("🔄 STEP 3: 환경 조건")
    tilt_deg = st.sidebar.slider("기울기 테스트 (Tilt °)", -15.0, 30.0, 0.0)

    # --- 물리 연산 엔진 ---
    # 1. 초기 무게중심(CG) 설정 (Side View 기준: z=앞뒤, y=높이)
    # SET의 로컬 CG는 두께의 절반, 높이의 절반으로 가정
    local_cg_z = 0 
    local_cg_y = h_set / 2 + neck_h

    # 2. 회전 변환 (Rotation Matrix)
    rad = np.radians(tilt_deg)
    # y' = y*cosθ - z*sinθ (실제로는 z축이 기울기의 주축)
    # 여기서는 측면도 시각화를 위해 단순화된 2D 회전 적용
    rotated_cg_z = local_cg_z * np.cos(rad) + local_cg_y * np.sin(rad)
    rotated_cg_y = -local_cg_z * np.sin(rad) + local_cg_y * np.cos(rad)

    # 3. 전도 판별 (Pivot Points)
    pivot_front = s_depth / 2
    pivot_back = -s_depth / 2
    is_tipping = rotated_cg_z > pivot_front or rotated_cg_z < pivot_back

    # --- 결과 시각화 ---
    col_chart, col_res = st.columns([2, 1])

    with col_chart:
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # 지면 (Floor)
        ax.axhline(0, color='gray', linestyle='-', linewidth=2)
        ax.fill_between([-1000, 1000], 0, -50, color='lightgray', alpha=0.3)

        # SET 외곽선 계산 (회전 반영)
        # 하단 중앙을 (0, neck_h)로 잡고 4개의 꼭짓점 정의
        rect = np.array([
            [-d_set/2, neck_h], [d_set/2, neck_h], 
            [d_set/2, neck_h+h_set], [-d_set/2, neck_h+h_set], [-d_set/2, neck_h]
        ])
        rot_m = np.array([[np.cos(rad), np.sin(rad)], [-np.sin(rad), np.cos(rad)]])
        rotated_rect = rect @ rot_m.T
        
        ax.plot(rotated_rect[:, 0], rotated_rect[:, 1], 'b-', lw=3, label="TV SET")
        
        # Stand 시각화 (고정 지면부)
        ax.plot([pivot_back, pivot_front], [0, 0], 'k-', lw=6, label="Stand Base")
        ax.plot([0, 0], [0, neck_h], 'k--', lw=2) # Neck
        
        # 무게중심(CG) 및 중력선
        ax.plot(rotated_cg_z, rotated_cg_y, 'ro', markersize=12, label="Center of Gravity")
        ax.vlines(rotated_cg_z, 0, rotated_cg_y, colors='red', linestyles=':', lw=2)
        
        # 텍스트 정보
        ax.text(rotated_cg_z+10, rotated_cg_y+20, f"CG ({rotated_cg_z:.1f}mm)", color='red', fontweight='bold')

        # 그래프 설정
        ax.set_xlim(-600, 600)
        ax.set_ylim(-100, 1600)
        ax.set_aspect('equal')
        ax.set_title(f"Stability Analysis: {tilt_deg}° Tilt", fontsize=15)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

    with col_res:
        st.subheader("📊 검토 결과")
        if is_tipping:
            st.error("🚨 전도 위험 (TIPPING) 🚨")
            st.write("무게중심의 수직선이 스탠드 지지 범위를 벗어났습니다. 스탠드의 깊이(Depth)를 늘리거나 SET의 경사각을 줄여야 합니다.")
        else:
            st.success("✅ 구조적 안정 (STABLE)")
            st.write("현재 설계 데이터 상에서 세트는 안정적인 상태를 유지합니다.")
        
        st.divider()
        st.write(f"**현재 타겟:** {inch}인치 모델")
        st.write(f"**지지 가동 범위:** {pivot_back}mm ~ {pivot_front}mm")
        st.write(f"**현재 CG 오프셋:** {rotated_cg_z:.2f} mm")
        
        # 디자인 인사이트
        st.info(f"💡 **기구 설계 코멘트:**\n\n{design_type} 방식은 최근 삼성전자의 초슬림 베젤 디자인과 결합되어 CG가 전면으로 쏠리는 경향이 있습니다. 스탠드 후면보다 전면 길이를 5~10% 더 확보하는 것이 유리합니다.")

if __name__ == "__main__":
    run_app()
