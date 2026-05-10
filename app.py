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

st.set_page_config(page_title="TV Jig Analyzer", layout="wide")
st.title("🔬 TV Stand 전도 해석 지그 (Tilt Jig Simulator)")
st.markdown("시청 환경 기준 좌표계(Z-up) 및 각도 측정기 일체화")

# --- Sidebar: 파라미터 설정 ---
st.sidebar.header("📐 설계 제원")
inch = st.sidebar.selectbox("TV 모델 선택", list(SAMSUNG_TV_DB.keys()), index=2)
spec = SAMSUNG_TV_DB[inch]

# 시청 환경 좌표계 정의: 폭(Y), 높이(Z), 깊이(X) -> 사용자는 -X 방향을 바라봄
# 여기서는 시각화 편의를 위해 표준 좌표계(폭 X, 높이 Y, 깊이 Z)를 사용하되 로직만 적용
tw, th, td = spec['w'], spec['h'], spec['d']
t_weight = st.sidebar.number_input("SET 중량 (kg)", value=spec['weight'])

st.sidebar.header("🦶 스탠드 설계 (Edge Feet)")
st_depth = st.sidebar.slider("스탠드 총 깊이 (mm)", 100, 600, 300)
st_inset = st.sidebar.slider("좌우 위치 오프셋 (mm)", 0, 300, 100)
front_ratio = st.sidebar.slider("전면 지지 비중 (0.5=대칭)", 0.1, 0.9, 0.6)

d_front = st_depth * front_ratio
d_back = st_depth * (1 - front_ratio)

st.sidebar.header("🌀 시험 조건 (Jig 동작)")
# 측정기 바닥 기울기 설정
floor_tilt = st.sidebar.slider("측정 지그 기울기 (°)", 0.0, 45.0, 0.0)

# --- 2. 물리 계산 ---
# 수직 높이 방향 무게중심 (바닥에서 th/2)
total_cg_h = th / 2
# 임계 각도 계산: tan(theta) = 전면지지거리 / CG높이
critical_tilt = np.degrees(np.arctan(d_front / total_cg_h))

# --- 3. 3D 좌표 및 회전 로직 ---
def get_rotated_box(w, h, d, ox, oy, oz, tilt_deg):
    # 초기 상태 정점 (똑바로 선 상태): X(폭), Y(높이), Z(깊이)
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2]) + ox
    y = np.array([0, 0, h, h, 0, 0, h, h]) + oy
    z = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2]) + oz
    
    # 지그 기울기에 따른 회전 (Y-Z 평면 회전 -> 패널이 앞뒤로 누움)
    rad = np.radians(tilt_deg)
    rot_y = y * np.cos(rad) - z * np.sin(rad)
    rot_z = y * np.sin(rad) + z * np.cos(rad)
    return x, rot_y, rot_z

# A. TV 패널 생성 (시청 환경 방향)
px, py, pz = get_rotated_box(tw, th, td, 0, 0, 0, floor_tilt)

# B. 스탠드 다리 생성 (V자형 Edge Feet 모사)
f_w, f_h = 30, 40
foot_oz = (d_front - d_back) / 2 # CG 기준 오프셋
f1x, f1y, f1z = get_rotated_box(f_w, f_h, st_depth, -tw/2+st_inset, -f_h, foot_oz, floor_tilt)
f2x, f2y, f2z = get_rotated_box(f_w, f_h, st_depth, tw/2-st_inset, -f_h, foot_oz, floor_tilt)

# C. 기울기 측정 지그 (바닥판) 생성
# TV 스탠드 하단(-f_h)에 위치하며, 슬라이더 각도에 따라 함께 회전
jig_w, jig_d, jig_h = tw + 200, st_depth + 200, 20
jx, jy, jz = get_rotated_box(jig_w, jig_h, jig_d, 0, -f_h - jig_h, foot_oz, floor_tilt)

# --- 4. Plotly 시각화 (확대 레이아웃) ---
fig = go.Figure()

mesh_params = dict(
    i=[0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7],
    j=[1, 2, 3, 3, 0, 2, 5, 6, 7, 7, 4, 6, 1, 5, 4, 4, 0, 5, 2, 6, 5, 5, 1, 6, 3, 7, 6, 6, 2, 7, 0, 4, 7, 7, 3, 4],
    k=[2, 3, 0, 1, 1, 3, 6, 7, 4, 5, 5, 7, 5, 4, 0, 1, 1, 0, 6, 5, 1, 2, 2, 1, 7, 6, 2, 3, 3, 2, 4, 7, 3, 0, 0, 3],
    opacity=0.8
)

# 객체 추가
fig.add_trace(go.Mesh3d(x=px, y=py, z=pz, color='royalblue', name='Panel', **mesh_params))
fig.add_trace(go.Mesh3d(x=f1x, y=f1y, z=f1z, color='black', name='Left Foot', **mesh_params))
fig.add_trace(go.Mesh3d(x=f2x, y=f2y, z=f2z, color='black', name='Right Foot', **mesh_params))
# 지그 바닥판 (투명도 조절)
fig.add_trace(go.Mesh3d(x=jx, y=jy, z=jz, color='silver', opacity=0.3, name='Tilt Jig', **mesh_params))

# 무게중심 및 중력선
rad = np.radians(floor_tilt)
cur_cg_y, cur_cg_z = total_cg_h * np.cos(rad), total_cg_h * np.sin(rad)
fig.add_trace(go.Scatter3d(x=[0], y=[cur_cg_y], z=[cur_cg_z], marker=dict(size=10, color='red'), name='CG'))
fig.add_trace(go.Scatter3d(x=[0,0], y=[cur_cg_y, 0], z=[cur_cg_z, cur_cg_z], mode='lines', line=dict(color='red', width=4, dash='dash'), name='Gravity Line'))

# 레이아웃 설정
fig.update_layout(
    height=850, 
    scene=dict(
        aspectmode='data',
        xaxis=dict(title="폭 (X)", range=[-1500, 1500]),
        yaxis=dict(title="높이 (Y)", range=[-200, 1500]),
        zaxis=dict(title="깊이 (Z)", range=[-800, 800])
    ),
    margin=dict(l=0, r=0, b=0, t=0)
)

# --- 5. 화면 출력 ---
col1, col2 = st.columns([4, 1])
with col1:
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("📋 해석 결과")
    st.metric("한계 각도 (Critical)", f"{critical_tilt:.2f} °")
    st.write("---")
    if floor_tilt >= critical_tilt:
        st.error(f"🛑 전도 발생!\n현재 각도 {floor_tilt}°가 한계를 초과했습니다.")
    else:
        st.success(f"✅ 안정 상태\n여유 각도: {critical_tilt - floor_tilt:.2f}°")
    st.info(f"설정 각도: {floor_tilt}°\n전면 지지: {d_front:.1f}mm\nCG 높이: {total_cg_h:.1f}mm")
