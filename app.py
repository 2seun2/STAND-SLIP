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

st.set_page_config(page_title="Unified 3D TV Tool", layout="wide")
st.title("🧊 통합형 3D TV 강체 전도 시뮬레이터")
st.markdown("패널과 Edge Feet 스탠드를 하나의 강체로 결합하여 한계 각도를 산출합니다.")

# --- Sidebar: 설정 ---
st.sidebar.header("📐 TV Spec & Stand")
inch = st.sidebar.selectbox("모델 선택", list(SAMSUNG_TV_DB.keys()), index=2)
spec = SAMSUNG_TV_DB[inch]

# 기본 제원
tw, th, td = spec['w'], spec['h'], spec['d']
t_weight = st.sidebar.number_input("중량 (kg)", value=spec['weight'])

# 스탠드 상세 (V자형 Edge Feet)
st_depth = st.sidebar.slider("스탠드 앞뒤 총 길이 (mm)", 100, 600, 300)
st_inset = st.sidebar.slider("스탠드 좌우 인셋 (mm)", 0, 300, 100)
# 무게중심(CG) 기준 앞/뒤 지지 비율 (보통 전면이 더 김)
front_ratio = st.sidebar.slider("전면 지지 비율", 0.1, 0.9, 0.6)
d_front = st_depth * front_ratio
d_back = st_depth * (1 - front_ratio)

st.sidebar.header("🌀 Test Condition")
floor_tilt = st.sidebar.slider("바닥 기울기 (°)", 0.0, 45.0, 0.0)

# --- 2. 물리 계산 (강체 해석) ---
# 전체 무게중심 (Panel 중앙 가정)
cg_y = th / 2
# 전도 한계 각도 (Critical Angle)
critical_tilt = np.degrees(np.arctan(d_front / cg_y))

# --- 3. 3D 메쉬 생성 로직 ---
def create_box(w, h, d, offset_x, offset_y, offset_z):
    # 육면체 정점 정의
    x = np.array([0, w, w, 0, 0, w, w, 0]) + offset_x - w/2
    y = np.array([0, 0, h, h, 0, 0, h, h]) + offset_y
    z = np.array([0, 0, 0, 0, d, d, d, d]) + offset_z - d/2
    return x, y, z

# A. TV Panel
px, py, pz = create_box(tw, th, td, 0, 0, 0)

# B. Left & Right Feet (V자형을 모사한 얇은 박스 결합)
f_w, f_h = 20, 30 # 다리 두께와 높이
f1x, f1y, f1z = create_box(f_w, f_h, st_depth, -tw/2 + st_inset, -f_h, (d_front - d_back)/2)
f2x, f2y, f2z = create_box(f_w, f_h, st_depth, tw/2 - st_inset, -f_h, (d_front - d_back)/2)

# 전체 좌표 통합 및 회전
all_x = np.concatenate([px, f1x, f2x])
all_y = np.concatenate([py, f1y, f2y])
all_z = np.concatenate([pz, f1z, f2z])

rad = np.radians(floor_tilt)
rot_y = all_y * np.cos(rad) - all_z * np.sin(rad)
rot_z = all_y * np.sin(rad) + all_z * np.cos(rad)

# 현재 CG 위치 계산
cur_cg_y = cg_y * np.cos(rad)
cur_cg_z = cg_y * np.sin(rad)

# --- 4. Plotly 3D 시각화 ---
fig = go.Figure()

# 통합 강체 메쉬 (TV + Feet)
def add_mesh(x, y, z, color, name):
    i = [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7]
    j = [1, 2, 3, 3, 0, 2, 5, 6, 7, 7, 4, 6, 1, 5, 4, 4, 0, 5, 2, 6, 5, 5, 1, 6, 3, 7, 6, 6, 2, 7, 0, 4, 7, 7, 3, 4]
    k = [2, 3, 0, 1, 1, 3, 6, 7, 4, 5, 5, 7, 5, 4, 0, 1, 1, 0, 6, 5, 1, 2, 2, 1, 7, 6, 2, 3, 3, 2, 4, 7, 3, 0, 0, 3]
    fig.add_trace(go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=0.7, name=name))

# Panel, Feet 각각 추가 (인덱스 관리를 위해 분리 호출 가능)
add_mesh(all_x[:8], rot_y[:8], rot_z[:8], 'royalblue', 'Panel')
add_mesh(all_x[8:16], rot_y[8:16], rot_z[8:16], 'black', 'Left Foot')
add_mesh(all_x[16:], rot_y[16:], rot_z[16:], 'black', 'Right Foot')

# CG 및 지면 표시
fig.add_trace(go.Scatter3d(x=[0], y=[cur_cg_y], z=[cur_cg_z], mode='markers', marker=dict(size=8, color='red'), name="Total CG"))
fig.add_trace(go.Scatter3d(x=[0,0], y=[cur_cg_y, 0], z=[cur_cg_z, cur_cg_z], mode='lines', line=dict(color='red', width=4), name="Gravity Line"))

fig.update_layout(scene=dict(aspectmode='data', xaxis=dict(range=[-1500,1500]), yaxis=dict(range=[-200,1500]), zaxis=dict(range=[-500,500])))

# --- 5. 결과 레이아웃 ---
c1, c2 = st.columns([3, 1])
with c1:
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("📊 검토 결과")
    st.metric("전도 한계 각도", f"{critical_tilt:.2f} °")
    if floor_tilt >= critical_tilt:
        st.error("🚨 전도 위험!")
    else:
        st.success("✅ 안정적")
    st.info(f"스탠드 전면 길이: {d_front:.1f}mm\n무게중심 높이: {cg_y:.1f}mm")
