import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. TV 설계 데이터베이스 ---
# 삼성 TV 최신 라인업 기반 가이드 제원
TV_SPECS = {
    "65인치 QLED": {"mass_kg": 24.2, "w_mm": 1446, "h_mm": 828, "d_mm": 25},
    "75인치 Neo QLED": {"mass_kg": 34.6, "w_mm": 1670, "h_mm": 957, "d_mm": 30},
    "85인치 QLED": {"mass_kg": 43.5, "w_mm": 1892, "h_mm": 1082, "d_mm": 35}
}

st.set_page_config(page_title="TV Stand stability analyzer", layout="wide")
st.title("🔬 TV Stand 전도 해석 지그 (Tilt Jig Simulator)")

# --- Sidebar: 설계 파라미터 ---
st.sidebar.header("📐 설계 제원 (Input)")
inch = st.sidebar.selectbox("TV 모델 선택", list(TV_SPECS.keys()))
spec = TV_SPECS[inch]

tw, th, td = spec['w_mm'], spec['h_mm'], spec['d_mm']
t_weight = st.sidebar.number_input("중량 (kg)", value=spec['mass_kg'])
# 무게중심 높이 설정 (패널 하단에서 h/2)
cg_h = st.sidebar.slider("무게중심 높이 (h_cg mm)", 100, int(th/2), 275)

st.sidebar.subheader("🦶 스탠드 설계 (Edge Feet)")
st_w_inset = st.sidebar.slider("스탠드 인셋 (w_inset mm)", 0, 300, 100)
st_depth = st.sidebar.slider("스탠드 총 깊이 (mm)", 100, 600, 300)
# 비대칭 스탠드 고려 (삼성 디자인 특성)
front_ratio = st.sidebar.slider("전면 지지 비율", 0.1, 0.9, 0.6)
d_front = st_depth * front_ratio
d_back = st_depth * (1 - front_ratio)

st.sidebar.header("🌀 시험 조건")
floor_tilt = st.sidebar.slider("바닥 기울기 테스트 (°)", 0.0, 45.0, 0.0)

# --- 2. 물리 및 좌표 계산 (통합 강체 로직) ---
# 전체 무게중심 (Panel CG: Z-up 좌표계 사용)
total_cg_z = cg_h
# 회전 중심(Pivot Point): 앞다리의 끝점
pivot_z = d_front

# 임계 각도 계산: tan(theta) = 지지거리 / CG높이
# theta = arctan(d_front / h_cg)
critical_tilt = np.degrees(np.arctan(d_front / cg_h))

# 3D 좌표 변환 함수 (X축 기준 회전)
def get_rotated_box(w, h, d, ox, oy, oz, tilt_deg):
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2]) + ox
    y = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2]) + oy
    z = np.array([0, 0, h, h, 0, 0, h, h]) + oz
    # 회전 행렬 적용 (Y-Z 평면 회전)
    rad = np.radians(tilt_deg)
    rot_y = y * np.cos(rad) - z * np.sin(rad)
    rot_z = y * np.sin(rad) + z * np.cos(rad)
    return x, rot_y, rot_z

# 통합 강체( Rigid Body ) 좌표 생성
px, py, pz = get_box_coords(tw, th, td, 0, 0, 0, floor_tilt) # TV Panel
# 스탠드 다리 생성 (V자형 Edge Feet 모사)
f_w, f_h = 30, 40
foot_oz = (d_front - d_back) / 2 # CG 기준 오프셋
f1x, f1y, f1z = get_box_coords(f_w, f_h, st_depth, -tw/2+st_inset, -f_h, foot_oz, floor_tilt)
f2x, f2y, f2z = get_box_coords(f_w, f_h, st_depth, tw/2-st_inset, -f_h, foot_oz, floor_tilt)

# --- 3. 시각화 (확대 레이아웃) ---
fig = go.Figure()

mesh_config = dict(
    i=[0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7],
    j=[1, 2, 3, 3, 0, 2, 5, 6, 7, 7, 4, 6, 1, 5, 4, 4, 0, 5, 2, 6, 5, 5, 1, 6, 3, 7, 6, 6, 2, 7, 0, 4, 7, 7, 3, 4],
    k=[2, 3, 0, 1, 1, 3, 6, 7, 4, 5, 5, 7, 5, 4, 0, 1, 1, 0, 6, 5, 1, 2, 2, 1, 7, 6, 2, 3, 3, 2, 4, 7, 3, 0, 0, 3],
    opacity=0.8
)

# 객체 추가
fig.add_trace(go.Mesh3d(x=px, y=py, z=pz, color='royalblue', name='Panel', **mesh_config))
fig.add_trace(go.Mesh3d(x=f1x, y=f1y, z=f1z, color='black', name='Left Foot', **mesh_config))
fig.add_trace(go.Mesh3d(x=f2x, y=f2y, z=f2z, color='black', name='Right Foot', **mesh_config))

# 무게중심 및 지면
rad = np.radians(floor_tilt)
cur_cg_y, cur_cg_z = total_cg_h * np.cos(rad), total_cg_h * np.sin(rad)
fig.add_trace(go.Scatter3d(x=[0], y=[cur_cg_y], z=[cur_cg_z], marker=dict(size=10, color='red'), name='CG'))

fig.update_layout(height=850, scene=dict(aspectmode='data', xaxis=dict(range=[-1500, 1500]), yaxis=dict(range=[-200, 1500]), zaxis=dict(range=[-800, 800])), margin=dict(l=0, r=0, b=0, t=0))

# --- 4. 화면 레이아웃 (3D + 계산로직) ---
col1, col2 = st.columns([3, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 해석 결과")
    st.metric("한계 각도", f"{critical_tilt:.2f} °")
    
    st.write("---")
    st.write("### 🧮 계산 로직 (Mechanical Formula)")
    # 이미지에 있는 수식을 그대로 완벽하게 LaTeX로 구현
    st.latex(r"""
    \theta_{\text{critical}} = \arctan\left(\frac{\text{Pivot Distance}}{\text{CG Height}}\right)
    """)
    
    st.latex(f"""
    \\theta_{{\\text{{critical}}}} = \\arctan\\left(\\frac{{{pivot_z}}}{{{cg_h}}}\\right)
    """)
    
    st.latex(f"""
    \\theta_{{\\text{{critical}}}} = \\arctan({pivot_z/cg_h:.4f}...)
    """)
    
    st.latex(r"""
    \theta_{\text{critical}} \approx 23.50167623676\ldots^\circ
    """)
    
    st.write(f"### 측정 결과 (Analysis Result): **{critical_tilt:.2f}°**")
    st.write(f"현재 기울기: {floor_tilt}°")
    
    st.divider()
    if floor_tilt >= critical_tilt:
        st.error("🛑 전도 발생")
    else:
        st.success("✅ 안정")
