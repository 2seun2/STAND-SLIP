import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. TV 표준 제원 데이터 (인터넷 서칭 기반 평균치) ---
# 43~115인치: [폭(mm), 높이(mm), 평균 중량(kg)]
TV_DATA = {
    "43": [967, 564, 9.0],
    "50": [1118, 644, 11.5],
    "55": [1232, 708, 15.0],
    "65": [1450, 830, 21.0],
    "70": [1570, 890, 25.0],
    "75": [1670, 960, 31.0],
    "85": [1890, 1080, 45.0],
    "98": [2190, 1250, 65.0],
    "115": [2560, 1450, 95.0]
}

st.set_page_config(page_title="TV Stand Analysis Pro", layout="wide")
st.title("🔬 TV 전도 해석 지그 시뮬레이터 (Pro)")

# --- 2. 사이드바: 설계 제원 입력 ---
with st.sidebar:
    st.header("📐 설계 제원 (Input)")
    
    # 사이즈 선택 및 자동 데이터 매핑
    size_opt = st.selectbox("Display Size (Inch)", list(TV_DATA.keys()), index=3) # 기본 65인치
    default_w, default_h, default_weight = TV_DATA[size_opt]
    
    st.markdown("---")
    tw = st.number_input("Panel Width (mm)", value=default_w)
    th = st.number_input("Panel Height (mm)", value=default_h)
    td = st.number_input("Panel Depth (mm)", value=25)
    
    # 중량 정보 (자동 연동 + 사용자 수정)
    st.subheader("⚖️ 중량 설정")
    weight = st.number_input("Total Weight (kg)", value=default_weight, step=0.5, help="인터넷 평균치 자동입력, 직접 수정 가능")
    
    st.markdown("---")
    st.subheader("🦶 스탠드 유형 및 설계")
    stand_type = st.radio("Stand Type", ["Two-Leg (Side)", "Center Stand"])
    
    st_depth = st.slider("Stand Total Depth (mm)", 100, 800, 350)
    pivot_dist = st.slider("Pivot Distance (d_p) (mm)", 50, 400, 150)
    cg_h = st.slider("CG Height (h_cg) (mm)", 100, 700, int(th/3))
    
    st.markdown("---")
    tilt_angle = st.slider("바닥 기울기 테스트 (°)", 0.0, 45.0, 23.5)

# --- 3. 3D 메쉬 생성 로직 ---
def get_box_mesh(w, h, d, ox, oy, oz, angle):
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2]) + ox
    y = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2]) + oy
    z = np.array([0, 0, h, h, 0, 0, h, h]) + oz
    rad = np.radians(angle)
    rot_y = y * np.cos(rad) - z * np.sin(rad)
    rot_z = y * np.sin(rad) + z * np.cos(rad)
    return x, rot_y, rot_z

I = [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7]
J = [1, 2, 3, 3, 0, 2, 5, 6, 7, 7, 4, 6, 1, 5, 4, 4, 0, 5, 2, 6, 5, 5, 1, 6, 3, 7, 6, 6, 2, 7, 0, 4, 7, 7, 3, 4]
K = [2, 3, 0, 1, 1, 3, 6, 7, 4, 5, 5, 7, 5, 4, 0, 1, 1, 0, 6, 5, 1, 2, 2, 1, 7, 6, 2, 3, 3, 2, 4, 7, 3, 0, 0, 3]

# --- 4. 시각화 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"📦 3D View ({stand_type})")
    fig3d = go.Figure()

    # TV 패널
    px, py, pz = get_box_mesh(tw, th, td, 0, 0, 0, tilt_angle)
    fig3d.add_trace(go.Mesh3d(x=px, y=py, z=pz, i=I, j=J, k=K, color='royalblue', opacity=0.8, name='Panel'))

    # 스탠드 렌더링
    stand_color = 'black'
    f_h = 40 # 스탠드 높이 기본값
    if stand_type == "Two-Leg (Side)":
        # 사이드 2개 다리
        f1x, f1y, f1z = get_box_mesh(25, f_h, st_depth, -tw/3, -f_h, (st_depth/2 - pivot_dist), tilt_angle)
        f2x, f2y, f2z = get_box_mesh(25, f_h, st_depth, tw/3, -f_h, (st_depth/2 - pivot_dist), tilt_angle)
        fig3d.add_trace(go.Mesh3d(x=f1x, y=f1y, z=f1z, i=I, j=J, k=K, color=stand_color, name='Leg L'))
        fig3d.add_trace(go.Mesh3d(x=f2x, y=f2y, z=f2z, i=I, j=J, k=K, color=stand_color, name='Leg R'))
    else:
        # 중앙 센터 스탠드
        cx, cy, cz = get_box_mesh(tw/4, f_h, st_depth, 0, -f_h, (st_depth/2 - pivot_dist), tilt_angle)
        fig3d.add_trace(go.Mesh3d(x=cx, y=cy, z=cz, i=I, j=J, k=K, color=stand_color, name='Center Stand'))

    # 바닥 지그
    gx, gy, gz = get_box_mesh(tw+500, 10, st_depth+500, 0, -f_h-10, (st_depth/2 - pivot_dist), tilt_angle)
    fig3d.add_trace(go.Mesh3d(x=gx, y=gy, z=gz, i=I, j=J, k=K, color='lightgray', opacity=0.3, name='Floor'))

    fig3d.update_layout(height=550, scene=dict(aspectmode='data'))
    st.plotly_chart(fig3d, use_container_width=True)

with col2:
    st.subheader("📐 Analysis Profile")
    critical_angle = np.degrees(np.arctan(pivot_dist / cg_h))
    
    # 2D Side View
    rad = np.radians(tilt_angle)
    p_z = [0, th * np.cos(rad)]; p_y = [0, -th * np.sin(rad)]
    cg_y = -cg_h * np.sin(rad); cg_z = cg_h * np.cos(rad)
    
    fig2d = go.Figure()
    fig2d.add_shape(type="line", x0=-600, y0=-f_h, x1=600, y1=-f_h, line=dict(color="Black", width=3))
    fig2d.add_trace(go.Scatter(x=p_y, y=p_z, mode='lines', line=dict(width=10, color='royalblue'), name='TV'))
    fig2d.add_trace(go.Scatter(x=[cg_y], y=[cg_z], mode='markers', marker=dict(size=15, color='red'), name='CG'))
    fig2d.add_trace(go.Scatter(x=[cg_y, cg_y], y=[cg_z, -f_h], mode='lines', line=dict(dash='dash', color='red')))
    
    fig2d.update_layout(height=550, xaxis=dict(range=[-600, 600]), yaxis=dict(range=[-100, th+200]))
    st.plotly_chart(fig2d, use_container_width=True)

# --- 5. 최종 결과 리포트 ---
st.markdown("---")
m1, m2, m3 = st.columns(3)
m1.metric("Selected Size", f"{size_opt} Inch")
m2.metric("Total Weight", f"{weight} kg")
m3.metric("Critical Angle", f"{critical_angle:.2f}°")

if tilt_angle < critical_angle:
    st.success(f"✅ 현재 각도 {tilt_angle}°에서 안정합니다. (여유각: {critical_angle - tilt_angle:.2f}°)")
else:
    st.error(f"🛑 현재 각도 {tilt_angle}°에서 전도 위험이 있습니다! (임계값 초과)")
