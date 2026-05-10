import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. 삼성전자 TV 표준 데이터베이스 ---
SAMSUNG_TV_DB = {
    "43인치": {"weight": 9.4, "w": 961, "h": 559, "d": 20},
    "65인치": {"weight": 24.2, "w": 1446, "h": 828, "d": 25},
    "85인치": {"weight": 43.5, "w": 1892, "h": 1082, "d": 35},
    "115인치": {"weight": 133.6, "w": 2565, "h": 1467, "d": 50}
}

st.set_page_config(page_title="3D TV Rigidity Tool", layout="wide")
st.title("🧊 3D TV Stand Stability Mechanical Tool")

# --- Sidebar: 설계 파라미터 ---
st.sidebar.header("📐 System Design")
inch = st.sidebar.selectbox("TV 모델 선택", list(SAMSUNG_TV_DB.keys()))
spec = SAMSUNG_TV_DB[inch]

# 상세 제원 수정
tw, th, td = spec['w'], spec['h'], spec['d']
t_weight = st.sidebar.number_input("SET 중량 (kg)", value=spec['weight'])
neck_h = st.sidebar.slider("Neck 높이 (mm)", 0, 150, 50)

st.sidebar.header("🦶 Stand Design")
st_type = st.sidebar.radio("디자인 타입", ["Center Plate", "Edge Feet"])
st_w = st.sidebar.slider("Stand 폭 (mm)", 100, tw, 400 if st_type=="Center Plate" else tw-200)
st_d = st.sidebar.slider("Stand 깊이 (mm)", 100, 600, 300)
st_weight = st.sidebar.number_input("Stand 중량 (kg)", value=2.0)

st.sidebar.header("🌀 Environment")
floor_tilt = st.sidebar.slider("바닥 기울기 (Floor Tilt °)", 0.0, 30.0, 0.0)

# --- 2. 물리 계산 (강체 해석) ---
# 전체 시스템의 무게중심 (바닥 중앙을 0,0,0으로 가정)
# Y: 높이, Z: 앞뒤(깊이), X: 좌우(폭)
total_mass = t_weight + st_weight
# SET CG (높이 절반 + Neck)
cg_set_y = neck_h + (th / 2)
# 시스템 전체 무게중심 (간략화: Stand CG는 바닥면에 가깝다고 가정)
total_cg_y = (t_weight * cg_set_y + st_weight * 0) / total_mass
total_cg_z = 0 # 초기 상태 중앙

# 전도 한계 각도 계산 (Critical Angle)
# tan(θ) = (지지거리_절반) / (CG_높이)
critical_tilt = np.degrees(np.arctan((st_depth / 2) / total_cg_y)) if 'st_depth' in locals() else np.degrees(np.arctan((st_d/2)/total_cg_y))

# --- 3. 3D 시각화 함수 ---
def get_box_coords(w, h, d, offset_y, tilt_deg):
    # 8개의 꼭짓점 정의
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2])
    y = np.array([0, 0, h, h, 0, 0, h, h]) + offset_y
    z = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2])
    
    # 기울기에 따른 회전 (Z-Y 평면 회전)
    rad = np.radians(tilt_deg)
    new_y = y * np.cos(rad) - z * np.sin(rad)
    new_z = y * np.sin(rad) + z * np.cos(rad)
    
    return x, new_y, new_z

# 데이터 생성
tx, ty, tz = get_box_coords(tw, th, td, neck_h, floor_tilt) # TV Panel
sx, sy, sz = get_box_coords(st_w, 10, st_d, 0, floor_tilt) # Stand Base

# --- 4. Plotly 3D 렌더링 ---
fig = go.Figure()

# TV Panel (Mesh)
fig.add_trace(go.Mesh3d(x=tx, y=ty, z=tz, i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6], color='royalblue', opacity=0.6, name="TV SET"))

# Stand (Mesh)
fig.add_trace(go.Mesh3d(x=sx, y=sy, z=sz, i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6], color='silver', opacity=0.8, name="Stand"))

# 무게중심 (CG Point)
cg_rad = np.radians(floor_tilt)
cur_cg_z = total_cg_y * np.sin(cg_rad)
cur_cg_y = total_cg_y * np.cos(cg_rad)
fig.add_trace(go.Scatter3d(x=[0], y=[cur_cg_y], z=[cur_cg_z], mode='markers', marker=dict(size=8, color='red'), name="Total CG"))

# 지면 (Floor)
fig.add_trace(go.Surface(x=np.linspace(-tw, tw, 10), y=np.zeros((10,10)), z=np.linspace(-600, 600, 10), colorscale='Greys', showscale=False, opacity=0.5))

fig.update_layout(scene=dict(xaxis=dict(range=[-1500, 1500]), yaxis=dict(range=[-100, 1500]), zaxis=dict(range=[-800, 800]), aspectmode='manual', aspectratio=dict(x=1, y=1, z=0.8)), margin=dict(l=0, r=0, b=0, t=0))

# --- 5. 결과 출력 ---
col1, col2 = st.columns([3, 1])
with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Analysis Result")
    st.metric("시스템 총 중량", f"{total_mass:.1f} kg")
    st.metric("전도 한계 각도", f"{critical_tilt:.2f} °")
    
    st.write("---")
    if floor_tilt >= critical_tilt:
        st.error(f"🛑 전도 발생! (Tipped)\n현재 {floor_tilt}° 가 한계치({critical_tilt:.2f}°)를 초과했습니다.")
    else:
        st.success(f"✅ 안정 (Stable)\n한계 각도까지 {critical_tilt - floor_tilt:.2f}° 남음")
        
    st.info("💡 **Engineer Note:** 강체 해석 결과, 스탠드의 깊이(Depth)가 {st_d}mm 일 때 전도에 가장 민감합니다. 삼성전자의 최신 대형 모델은 안전율을 고려하여 한계 각도를 보통 15~20° 이상으로 설계합니다.")
