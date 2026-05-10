import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. TV 설계 데이터베이스 ---
TV_SPECS = {
    "65인치 (이미지 모델)": {"mass": 26.2, "w": 1446, "h": 828, "d": 25},
    "75인치": {"mass": 34.6, "w": 1670, "h": 957, "d": 30},
    "85인치": {"mass": 43.5, "w": 1892, "h": 1082, "d": 35}
}

st.set_page_config(page_title="TV Rigid Body Lab", layout="wide")
st.title("🔬 TV Stand 전도 해석 지그 (Tilt Jig Simulator)")

# --- Sidebar: 설계 파라미터 ---
st.sidebar.header("📐 설계 제원 (Input)")
inch = st.sidebar.selectbox("TV 모델 선택", list(TV_SPECS.keys()))
spec = TV_SPECS[inch]

tw, th, td = spec['w'], spec['h'], spec['d']
cg_h = st.sidebar.slider("무게중심 높이 (h_cg mm)", 100, int(th/2), 275)

st.sidebar.subheader("🦶 스탠드 설계")
st_depth = st.sidebar.slider("스탠드 총 깊이 (mm)", 100, 600, 300)
front_ratio = st.sidebar.slider("전면 지지 비율", 0.1, 0.9, 0.6)
d_front = st_depth * front_ratio
d_back = st_depth * (1 - front_ratio)

floor_tilt = st.sidebar.slider("바닥 기울기 테스트 (°)", 0.0, 45.0, 23.5)

# --- 2. 통합 강체 회전 로직 (Rigid Body Transformation) ---
def get_box_mesh(w, h, d, ox, oy, oz, tilt_deg):
    """육면체 정점 생성 및 통합 회전 적용"""
    # 8개 정점 정의
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2]) + ox
    y = np.array([0, 0, h, h, 0, 0, h, h]) + oy
    z = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2]) + oz
    
    # 바닥 기울기에 따른 회전 (Y-Z 평면 회전)
    rad = np.radians(tilt_deg)
    rot_y = y * np.cos(rad) - z * np.sin(rad)
    rot_z = y * np.sin(rad) + z * np.cos(rad)
    return x, rot_y, rot_z

# 육면체 구성을 위한 삼각 메쉬 인덱스 (고정)
I = [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7]
J = [1, 2, 3, 3, 0, 2, 5, 6, 7, 7, 4, 6, 1, 5, 4, 4, 0, 5, 2, 6, 5, 5, 1, 6, 3, 7, 6, 6, 2, 7, 0, 4, 7, 7, 3, 4]
K = [2, 3, 0, 1, 1, 3, 6, 7, 4, 5, 5, 7, 5, 4, 0, 1, 1, 0, 6, 5, 1, 2, 2, 1, 7, 6, 2, 3, 3, 2, 4, 7, 3, 0, 0, 3]

# [강체 1] TV 패널
px, py, pz = get_box_mesh(tw, th, td, 0, 0, 0, floor_tilt)

# [강체 2] 스탠드 다리 (두 개)
f_w, f_h = 30, 40
f_oz = (d_front - d_back) / 2
f1x, f1y, f1z = get_box_mesh(f_w, f_h, st_depth, -tw/3, -f_h, f_oz, floor_tilt)
f2x, f2y, f2z = get_box_mesh(f_w, f_h, st_depth, tw/3, -f_h, f_oz, floor_tilt)

# [강체 3] 바닥 측정 지그
jx, jy, jz = get_box_mesh(tw+400, 20, st_depth+400, 0, -f_h-20, f_oz, floor_tilt)

# --- 3. 시각화 ---
fig = go.Figure()

# 메쉬 추가 (색상 채우기로 중앙이 비어 보이지 않게 설정)
fig.add_trace(go.Mesh3d(x=px, y=py, z=pz, i=I, j=J, k=K, color='royalblue', opacity=1.0, name='TV Panel'))
fig.add_trace(go.Mesh3d(x=f1x, y=f1y, z=f1z, i=I, j=J, k=K, color='black', name='Stand L'))
fig.add_trace(go.Mesh3d(x=f2x, y=f2y, z=f2z, i=I, j=J, k=K, color='black', name='Stand R'))
fig.add_trace(go.Mesh3d(x=jx, y=jy, z=jz, i=I, j=J, k=K, color='silver', opacity=0.3, name='Tilt Jig'))

# 무게중심(CG) 포인트 및 중력선
rad = np.radians(floor_tilt)
cur_cg_y, cur_cg_z = cg_h * np.cos(rad), cg_h * np.sin(rad)
fig.add_trace(go.Scatter3d(x=[0], y=[cur_cg_y], z=[cur_cg_z], mode='markers', marker=dict(size=10, color='red'), name='System CG'))
fig.add_trace(go.Scatter3d(x=[0, 0], y=[cur_cg_y, 0], z=[cur_cg_z, cur_cg_z], mode='lines', line=dict(color='red', width=5, dash='dash'), name='Gravity Line'))

fig.update_layout(height=800, scene=dict(aspectmode='data', xaxis_title="X (Width)", yaxis_title="Y (Height)", zaxis_title="Z (Depth)"), margin=dict(l=0, r=0, b=0, t=0))

# --- 4. 결과 출력 ---
col1, col2 = st.columns([4, 1])
with col1:
    st.plotly_chart(fig, use_container_width=True)
with col2:
    critical_tilt = np.degrees(np.arctan(d_front / cg_h))
    st.metric("한계 각도", f"{critical_tilt:.2f}°")
    if floor_tilt >= critical_tilt:
        st.error("🛑 전도 발생")
    else:
        st.success("✅ 안정")
    st.write(f"현재 각도: {floor_tilt}°")
