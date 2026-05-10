import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. 삼성전자 TV 표준 데이터베이스 (이전 동일) ---
SAMSUNG_TV_DB = {
    "43인치": {"weight": 9.4, "w": 961, "h": 559, "d": 20},
    "65인치": {"weight": 24.2, "w": 1446, "h": 828, "d": 25},
    "85인치": {"weight": 43.5, "w": 1892, "h": 1082, "d": 35},
    "115인치": {"weight": 133.6, "w": 2565, "h": 1467, "d": 50}
}

st.set_page_config(page_title="Unified 3D TV Tool", layout="wide")
st.title("🧊 Unified 3D TV Rigid Body Simulation")
st.markdown("기구 개발용: 스탠드-패널 통합 강체 모델 및 전도 한계 해석")

# --- Sidebar: 설계 파라미터 ---
st.sidebar.header("📐 System Design (Rigid Body)")
inch = st.sidebar.selectbox("TV 모델 선택", list(SAMSUNG_TV_DB.keys()), index=1)
spec = SAMSUNG_TV_DB[inch]

# 상세 제원
tw, th, td = spec['w'], spec['h'], spec['d']
t_weight = st.sidebar.number_input("SET 중량 (kg)", value=spec['weight'])

st.sidebar.header("🦶 Edge Feet Design (Integrated)")
st_w_offset = st.sidebar.slider("다리 위치 (폭 Offset mm)", 50, int(tw/2), 150)
st_d_total = st.sidebar.slider("다리 총 깊이 (Depth mm)", 100, 600, 300)
# V자형 다리의 앞뒤 비대칭성 고려 (삼성 디자인 특성)
st_d_front = st.sidebar.slider("다리 전면 길이 (CG 기준 mm)", 50, st_d_total, int(st_d_total*0.6))
st_d_back = st_d_total - st_d_front

st.sidebar.header("🌀 Environment")
floor_tilt = st.sidebar.slider("바닥 기울기 (Floor Tilt °)", 0.0, 45.0, 0.0)

# --- 2. 물리 계산 (강체 해석) ---
# 전체 무게중심 (간략화: SET 중앙)
total_mass = t_weight
total_cg_y = th / 2
total_cg_z = 0 # 다리 깊이에 대해 중앙으로 가정

# 전도 한계 각도 (Critical Angle) 계산
critical_tilt = np.degrees(np.arctan((st_d_front) / total_cg_y))

# --- 3. 3D 좌표 변환 함수 ---
def get_rotated_points(x, y, z, tilt_deg):
    rad = np.radians(tilt_deg)
    rot_y = y * np.cos(rad) - z * np.sin(rad)
    rot_z = y * np.sin(rad) + z * np.cos(rad)
    return x, rot_y, rot_z

# 통합 3D 메쉬 생성 데이터 준비
# (x, y, z 좌표를 하나의 배열로 통합하여 단일 Mesh3d로 렌더링)
vertices_x, vertices_y, vertices_z = [], [], []

# A. TV Panel 메쉬 (Box)
panel_x = np.array([-tw/2, tw/2, tw/2, -tw/2, -tw/2, tw/2, tw/2, -tw/2])
panel_y = np.array([0, 0, th, th, 0, 0, th, th])
panel_z = np.array([-td/2, -td/2, -td/2, -td/2, td/2, td/2, td/2, td/2])
# 패널 좌표 회전
r_px, r_py, r_pz = get_rotated_points(panel_x, panel_y, panel_z, floor_tilt)

# B. Edge Feet 메쉬 (비대칭 V형 2개)
def add_foot_mesh(offset_x, front, back):
    # 각 다리는 단순화된 삼각기둥 형태로 좌표 정의
    fx = np.array([offset_x, offset_x+10, offset_x, offset_x+10, offset_x])
    fy = np.array([0, 0, -20, -20, -50]) # 지면 아래로 확장
    fz = np.array([-td/2-back, -td/2-back, -td/2-back, -td/2-back, td/2+front])
    # 다리 좌표 회전
    r_fx, r_fy, r_fz = get_rotated_points(fx, fy, fz, floor_tilt)
    return r_fx, r_fy, r_fz

f1x, f1y, f1z = add_foot_mesh(-tw/2+st_w_offset, st_d_front, st_d_back) # Left Foot
f2x, f2y, f2z = add_foot_mesh(tw/2-st_w_offset-10, st_d_front, st_d_back) # Right Foot

# 전체 좌표 통합
all_x = np.concatenate([r_px, f1x, f2x])
all_y = np.concatenate([r_py, f1y, f2y])
all_z = np.concatenate([r_pz, f1z, f2z])

# 현재 CG 위치
cur_rad = np.radians(floor_tilt)
cur_cg_y = total_cg_y * np.cos(cur_rad)
cur_cg_z = total_cg_y * np.sin(cur_rad)

# --- 4. Plotly 3D 통합 렌더링 ---
fig = go.Figure()

# Unified TV + Stand Mesh
# (i, j, k는 메쉬 삼각형의 정점 인덱스로, 패널과 다리를 한꺼번에 정의)
i = [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7] # Panel faces
# 다리 메쉬 인덱스 추가 (패널 인덱스 8 이후)
i += [8, 9, 10, 8, 10, 11, 8, 9, 12, 13, 14, 15] # Left Foot faces
i += [16, 17, 18, 16, 18, 19, 16, 17, 20, 21, 22, 23] # Right Foot faces
# (전체 인덱스 j, k도 이에 맞춰 확장 정의)
# ... (상세 인덱스 정의 생략, 실제 코드에는 전체를 넣어야 함) ...
j = [1, 2, 3, 4, 5, 6, 7, 0, 1, 5, 2, 6] # 예시용 일부
k = [2, 3, 0, 5, 6, 7, 4, 1, 6, 1, 3, 7] # 예시용 일부

# (전체 메쉬 삼각형 j, k 인덱스를 실제 코드에 정의해야 함)
# ... (상세 인덱스 정의 생략) ...

fig.add_trace(go.Mesh3d(
    x=all_x, y=all_y, z=all_z,
    # (위에서 정의한 전체 i, j, k 인덱스를 여기에 전달)
    color='royalblue', opacity=0.6,
    name="Unified TV Body"
))

# 무게중심 (CG) 및 중력선 표시 (이전 동일)
# ... (이전 코드와 동일한 CG 시각화 로직) ...

fig.update_layout(scene=dict(aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0))

# --- 5. 결과 출력 (이전 동일) ---
# ... (이전 코드와 동일한 결과 출력 로직) ...
