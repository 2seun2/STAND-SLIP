import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. 삼성전자 TV 표준 데이터베이스 ---
SAMSUNG_TV_DB = {
    "43인치": {"weight": 9.4, "w": 961, "h": 559, "d": 20},
    "55인치": {"weight": 15.0, "w": 1227, "h": 706, "d": 25},
    "65인치": {"weight": 24.2, "w": 1446, "h": 828, "d": 25},
    "75인치": {"weight": 34.6, "w": 1670, "h": 957, "d": 30},
    "85인치": {"weight": 43.5, "w": 1892, "h": 1082, "d": 35},
    "98인치": {"weight": 68.0, "w": 2185, "h": 1249, "d": 40},
    "115인치": {"weight": 133.6, "w": 2565, "h": 1467, "d": 50}
}

st.set_page_config(page_title="Rigid Body 3D Analyzer", layout="wide") # 전체 화면 모드
st.title("📺 TV Stand 통합 강체 3D 전도 해석 툴")

# --- Sidebar: 설계 파라미터 ---
st.sidebar.header("📐 설계 제원")
inch = st.sidebar.selectbox("TV 모델 선택", list(SAMSUNG_TV_DB.keys()), index=2)
spec = SAMSUNG_TV_DB[inch]

tw, th, td = spec['w'], spec['h'], spec['d']
t_weight = st.sidebar.number_input("SET 중량 (kg)", value=spec['weight'])

st.sidebar.header("🦶 스탠드 설계 (Edge Feet)")
st_depth = st.sidebar.slider("스탠드 총 깊이 (mm)", 100, 600, 300)
st_inset = st.sidebar.slider("좌우 위치 오프셋 (mm)", 0, 300, 100)
front_ratio = st.sidebar.slider("전면 지지 비중 (0.5=대칭)", 0.1, 0.9, 0.6)

d_front = st_depth * front_ratio
d_back = st_depth * (1 - front_ratio)

st.sidebar.header("🌀 시험 조건")
floor_tilt = st.sidebar.slider("바닥 기울기 테스트 (°)", 0.0, 45.0, 0.0)

# --- 2. 물리 계산 (강체 해석) ---
total_cg_y = th / 2
# 임계 각도 계산: tan(theta) = 지지거리 / CG높이
critical_tilt = np.degrees(np.arctan(d_front / total_cg_y))

# --- 3. 3D 좌표 및 회전 로직 (TV를 똑바로 세움) ---
def get_box_mesh(w, h, d, ox, oy, oz, tilt_deg):
    # 정점 정의 (똑바로 서 있는 상태 기준)
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2]) + ox
    y = np.array([0, 0, h, h, 0, 0, h, h]) + oy
    z = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2]) + oz
    
    # 바닥 기울기에 따른 회전 변환 (Z-Y 평면)
    rad = np.radians(tilt_deg)
    rot_y = y * np.cos(rad) - z * np.sin(rad)
    rot_z = y * np.sin(rad) + z * np.cos(rad)
    return x, rot_y, rot_z

# TV 패널과 다리를 각각 생성 (동일한 기울기 적용)
px, py, pz = get_box_mesh(tw, th, td, 0, 0, 0, floor_tilt)
# 스탠드 다리 (V자형을 모사한 얇은 박스)
f_w, f_h = 30, 40
f1x, f1y, f1z = get_box_mesh(f_w, f_h, st_depth, -tw/2+st_inset, -f_h, (d_front-d_back)/2, floor_tilt)
f2x, f2y, f2z = get_box_mesh(f_w, f_h, st_depth, tw/2-st_inset, -f_h, (d_front-d_back)/2, floor_tilt)

# --- 4. 시각화 (창 크기 최대화) ---
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
cur_cg_y, cur_cg_z = total_cg_y * np.cos(rad), total_cg_y * np.sin(rad)
fig.add_trace(go.Scatter3d(x=[0], y=[cur_cg_y], z=[cur_cg_z], marker=dict(size=10, color='red'), name='CG'))

# 레이아웃: 창 크기를 대폭 키움 (height=800)
fig.update_layout(
    height=850, 
    scene=dict(
        aspectmode='data',
        xaxis=dict(range=[-1500, 1500]),
        yaxis=dict(range=[-200, 1500]),
        zaxis=dict(range=[-800, 800])
    ),
    margin=dict(l=0, r=0, b=0, t=0)
)

# --- 5. 결과 출력 ---
col1, col2 = st.columns([4, 1]) # 시각화 비중을 더 키움
with col1:
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("📋 분석 결과")
    st.metric("한계 각도", f"{critical_tilt:.2f} °")
    if floor_tilt >= critical_tilt:
        st.error("🛑 전도 발생")
    else:
        st.success("✅ 안정")
