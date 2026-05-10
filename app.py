import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. TV 데이터베이스 ---
SAMSUNG_TV_DB = {
    "43인치": {"weight": 9.4, "w": 961, "h": 559, "d": 20},
    "65인치": {"weight": 24.2, "w": 1446, "h": 828, "d": 25},
    "85인치": {"weight": 43.5, "w": 1892, "h": 1082, "d": 35},
    "115인치": {"weight": 133.6, "w": 2565, "h": 1467, "d": 50}
}

st.set_page_config(page_title="TV Jig Analyzer", layout="wide")
st.title("🔬 TV Stand 전도 해석 지그 (Tilt Jig Simulator)")

# --- Sidebar 설정 ---
st.sidebar.header("📐 설계 제원")
inch = st.sidebar.selectbox("TV 모델 선택", list(SAMSUNG_TV_DB.keys()), index=1)
spec = SAMSUNG_TV_DB[inch]

tw, th, td = spec['w'], spec['h'], spec['d']
st_depth = st.sidebar.slider("스탠드 총 깊이 (mm)", 100, 600, 300)
front_ratio = st.sidebar.slider("전면 지지 비중", 0.1, 0.9, 0.6)
floor_tilt = st.sidebar.slider("측정 지그 기울기 (°)", 0.0, 45.0, 0.0)

# --- 2. 물리 및 좌표 계산 ---
d_front = st_depth * front_ratio
d_back = st_depth * (1 - front_ratio)
total_cg_h = th / 2
critical_tilt = np.degrees(np.arctan(d_front / total_cg_h))

def get_box_coords(w, h, d, ox, oy, oz, tilt_deg):
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2]) + ox
    y = np.array([0, 0, h, h, 0, 0, h, h]) + oy
    z = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2]) + oz
    rad = np.radians(tilt_deg)
    rot_y = y * np.cos(rad) - z * np.sin(rad)
    rot_z = y * np.sin(rad) + z * np.cos(rad)
    return x, rot_y, rot_z

# 육면체 면 구성을 위한 고정 인덱스
I = [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7]
J = [1, 2, 3, 3, 0, 2, 5, 6, 7, 7, 4, 6, 1, 5, 4, 4, 0, 5, 2, 6, 5, 5, 1, 6, 3, 7, 6, 6, 2, 7, 0, 4, 7, 7, 3, 4]
K = [2, 3, 0, 1, 1, 3, 6, 7, 4, 5, 5, 7, 5, 4, 0, 1, 1, 0, 6, 5, 1, 2, 2, 1, 7, 6, 2, 3, 3, 2, 4, 7, 3, 0, 0, 3]

# 객체 좌표 생성
px, py, pz = get_box_coords(tw, th, td, 0, 0, 0, floor_tilt)
f1x, f1y, f1z = get_box_coords(30, 40, st_depth, -tw/3, -40, (d_front-d_back)/2, floor_tilt)
f2x, f2y, f2z = get_box_coords(30, 40, st_depth, tw/3, -40, (d_front-d_back)/2, floor_tilt)
jx, jy, jz = get_box_coords(tw+400, 20, st_depth+400, 0, -60, (d_front-d_back)/2, floor_tilt)

# --- 3. Plotly 시각화 ---
fig = go.Figure()

# 각 객체를 Mesh3d로 추가 (TypeError 방지를 위해 i, j, k 명시)
fig.add_trace(go.Mesh3d(x=px, y=py, z=pz, i=I, j=J, k=K, color='royalblue', opacity=0.8, name='TV'))
fig.add_trace(go.Mesh3d(x=f1x, y=f1y, z=f1z, i=I, j=J, k=K, color='black', name='Stand_L'))
fig.add_trace(go.Mesh3d(x=f2x, y=f2y, z=f2z, i=I, j=J, k=K, color='black', name='Stand_R'))
fig.add_trace(go.Mesh3d(x=jx, y=jy, z=jz, i=I, j=J, k=K, color='silver', opacity=0.3, name='Jig'))

# 무게중심(CG) 표시
rad = np.radians(floor_tilt)
fig.add_trace(go.Scatter3d(x=[0], y=[total_cg_h*np.cos(rad)], z=[total_cg_h*np.sin(rad)], mode='markers', marker=dict(size=8, color='red'), name='CG'))

fig.update_layout(height=800, scene=dict(aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0))

# --- 4. 화면 출력 ---
c1, c2 = st.columns([4, 1])
with c1:
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.metric("한계 각도", f"{critical_tilt:.2f}°")
    if floor_tilt >= critical_tilt:
        st.error("🛑 전도 위험!")
    else:
        st.success("✅ 안정")
