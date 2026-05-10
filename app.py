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

st.set_page_config(page_title="3D TV Stability Tool", layout="wide")
st.title("🧊 3D TV Rigidity & Tipping Simulator")
st.markdown("기구 개발용: 강체(Rigid Body) 기반 전도 한계 각도 산출 툴")

# --- Sidebar: 설계 파라미터 ---
st.sidebar.header("📐 System Design")
inch = st.sidebar.selectbox("TV 모델 선택", list(SAMSUNG_TV_DB.keys()), index=2)
spec = SAMSUNG_TV_DB[inch]

tw, th, td = spec['w'], spec['h'], spec['d']
t_weight = st.sidebar.number_input("SET 중량 (kg)", value=spec['weight'])
neck_h = st.sidebar.slider("Neck 높이 (mm)", 0, 150, 50)

st.sidebar.header("🦶 Stand Design")
st_type = st.sidebar.radio("디자인 타입", ["Center Plate", "Edge Feet"])
st_w = st.sidebar.slider("Stand 폭 (mm)", 100, int(tw), 400 if st_type=="Center Plate" else int(tw-200))
st_d = st.sidebar.slider("Stand 깊이 (mm)", 100, 600, 300)
st_weight = st.sidebar.number_input("Stand 중량 (kg)", value=2.0)

st.sidebar.header("🌀 Test Condition")
floor_tilt = st.sidebar.slider("바닥 기울기 (Floor Tilt °)", 0.0, 45.0, 0.0)

# --- 2. 물리 계산 (강체 해석) ---
total_mass = t_weight + st_weight
# 시스템 전체 무게중심 (Y: 높이, Z: 깊이)
# SET CG는 높이의 절반 + Neck 높이 / Stand CG는 바닥(0)으로 가정
total_cg_y = (t_weight * (neck_h + th/2) + st_weight * 0) / total_mass
total_cg_z = 0 # 초기 상태 중앙

# 전도 한계 각도 (Critical Angle) 계산
# tan(theta) = (지지점 거리) / (CG 높이)
critical_tilt = np.degrees(np.arctan((st_d / 2) / total_cg_y))

# --- 3. 3D 좌표 변환 함수 ---
def get_rotated_box(w, h, d, offset_y, tilt_deg):
    # 8개 정점 정의
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2])
    y = np.array([0, 0, h, h, 0, 0, h, h]) + offset_y
    z = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2])
    
    # 기울기에 따른 Y-Z 평면 회전 (강체 회전)
    rad = np.radians(tilt_deg)
    rot_y = y * np.cos(rad) - z * np.sin(rad)
    rot_z = y * np.sin(rad) + z * np.cos(rad)
    return x, rot_y, rot_z

# TV 및 Stand 3D 좌표 생성
tx, ty, tz = get_rotated_box(tw, th, td, neck_h, floor_tilt)
sx, sy, sz = get_rotated_box(st_w, 10, st_d, 0, floor_tilt)

# 현재 기울어진 상태의 CG 위치
cur_rad = np.radians(floor_tilt)
cur_cg_y = total_cg_y * np.cos(cur_rad)
cur_cg_z = total_cg_y * np.sin(cur_rad)

# --- 4. Plotly 3D 렌더링 ---
fig = go.Figure()

# TV SET Mesh
fig.add_trace(go.Mesh3d(x=tx, y=ty, z=tz, i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6], color='royalblue', opacity=0.5, name="TV SET"))

# Stand Mesh
fig.add_trace(go.Mesh3d(x=sx, y=sy, z=sz, i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6], color='gray', opacity=0.8, name="Stand"))

# 무게중심 (CG) 표시
fig.add_trace(go.Scatter3d(x=[0], y=[cur_cg_y], z=[cur_cg_z], mode='markers+text', marker=dict(size=10, color='red'), text=["TOTAL CG"], textposition="top center", name="CG"))

# 중력선 (Gravity Line)
fig.add_trace(go.Scatter3d(x=[0, 0], y=[cur_cg_y, 0], z=[cur_cg_z, cur_cg_z], mode='lines', line=dict(color='red', width=4, dash='dash'), name="Gravity Line"))

# 레이아웃 설정
fig.update_layout(
    scene=dict(
        xaxis=dict(title="Width (X)", range=[-1500, 1500]),
        yaxis=dict(title="Height (Y)", range=[-100, 1500]),
        zaxis=dict(title="Depth (Z)", range=[-800, 800]),
        aspectmode='data'
    ),
    margin=dict(l=0, r=0, b=0, t=0)
)

# --- 5. 화면 출력 ---
c1, c2 = st.columns([3, 1])
with c1:
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📊 해석 결과")
    st.metric("시스템 총 중량", f"{total_mass:.1f} kg")
    st.metric("전도 한계 각도", f"{critical_tilt:.2f} °")
    
    st.divider()
    if floor_tilt >= critical_tilt:
        st.error(f"🛑 전도 발생!\n현재 {floor_tilt}° 가 한계치({critical_tilt:.2f}°)를 초과했습니다.")
    else:
        st.success(f"✅ 안정 상태\n전도까지 {critical_tilt - floor_tilt:.2f}° 여유")
    
    st.info(f"무게중심 높이: {total_cg_y:.1f}mm\n지지 깊이: {st_d}mm")
