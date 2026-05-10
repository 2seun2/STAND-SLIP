import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. 기본 설정 ---
st.set_page_config(page_title="TV Rigid Body Analysis", layout="wide")
st.title("🔬 TV Stand 전도 해석 지그 (Tilt Jig Simulator)")

# --- 2. 사이드바: 설계 제원 (좌측 레이아웃) ---
with st.sidebar:
    st.header("📐 설계 제원 (Input)")
    tw = st.number_input("Panel Width (mm)", value=1446)
    th = st.number_input("Panel Height (mm)", value=828)
    td = st.number_input("Panel Depth (mm)", value=25)
    
    st.markdown("---")
    st.subheader("🦶 스탠드 설계 (Rigid Connection)")
    st_depth = st.slider("Stand Total Depth (mm)", 100, 600, 300)
    pivot_dist = st.slider("Pivot Distance (d_p) (mm)", 50, 300, 120)
    cg_h = st.slider("CG Height (h_cg) (mm)", 100, 500, 275)
    
    st.markdown("---")
    tilt_angle = st.slider("바닥 기울기 테스트 (°)", 0.0, 45.0, 23.5)

# --- 3. 통합 강체 회전 로직 (Rigid Body Transformation) ---
def get_box_mesh(w, h, d, ox, oy, oz, angle):
    """육면체 정점을 생성하고 X축 기준 회전 적용 (Z-up 좌표계)"""
    # 8개 정점 정의 (중심 기준)
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2]) + ox
    y = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2]) + oy
    z = np.array([0, 0, h, h, 0, 0, h, h]) + oz
    
    # 회전 행렬 적용 (Y-Z 평면 회전)
    rad = np.radians(angle)
    # y' = y*cos - z*sin, z' = y*sin + z*cos
    rot_y = y * np.cos(rad) - z * np.sin(rad)
    rot_z = y * np.sin(rad) + z * np.cos(rad)
    return x, rot_y, rot_z

# 메쉬 삼각형 인덱스
I = [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7]
J = [1, 2, 3, 3, 0, 2, 5, 6, 7, 7, 4, 6, 1, 5, 4, 4, 0, 5, 2, 6, 5, 5, 1, 6, 3, 7, 6, 6, 2, 7, 0, 4, 7, 7, 3, 4]
K = [2, 3, 0, 1, 1, 3, 6, 7, 4, 5, 5, 7, 5, 4, 0, 1, 1, 0, 6, 5, 1, 2, 2, 1, 7, 6, 2, 3, 3, 2, 4, 7, 3, 0, 0, 3]

# --- 4. 메인 시각화 레이아웃 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 3D Perspective (Integrated Rigid Body)")
    fig3d = go.Figure()

    # [강체 1] TV 패널
    px, py, pz = get_box_mesh(tw, th, td, 0, 0, 0, tilt_angle)
    fig3d.add_trace(go.Mesh3d(x=px, y=py, z=pz, i=I, j=J, k=K, color='royalblue', opacity=0.9, name='Panel'))

    # [강체 2] 스탠드 다리 (좌/우 2개 추가)
    # 스탠드는 패널 하단(z=0 근처)에 붙어있으며 동일하게 회전함
    f_w, f_h, f_d = 20, 40, st_depth
    # 다리 위치 계산 (패널 하단에 고정)
    f1x, f1y, f1z = get_box_mesh(f_w, f_h, f_d, -tw/3, -f_h, (st_depth/2 - pivot_dist), tilt_angle)
    f2x, f2y, f2z = get_box_mesh(f_w, f_h, f_d, tw/3, -f_h, (st_depth/2 - pivot_dist), tilt_angle)
    
    fig3d.add_trace(go.Mesh3d(x=f1x, y=f1y, z=f1z, i=I, j=J, k=K, color='black', name='Stand L'))
    fig3d.add_trace(go.Mesh3d(x=f2x, y=f2y, z=f2z, i=I, j=J, k=K, color='black', name='Stand R'))

    # [지구] 바닥 지그
    floor_w, floor_d = tw + 400, st_depth + 400
    gx, gy, gz = get_box_mesh(floor_w, 10, floor_d, 0, -f_h-10, (st_depth/2 - pivot_dist), tilt_angle)
    fig3d.add_trace(go.Mesh3d(x=gx, y=gy, z=gz, i=I, j=J, k=K, color='lightgray', opacity=0.4, name='Tilt Floor'))

    # 무게중심(CG) 표시
    rad = np.radians(tilt_angle)
    cg_y_rot = 0 * np.cos(rad) - cg_h * np.sin(rad)
    cg_z_rot = 0 * np.sin(rad) + cg_h * np.cos(rad)
    fig3d.add_trace(go.Scatter3d(x=[0], y=[cg_y_rot], z=[cg_z_rot], mode='markers', 
                                 marker=dict(size=10, color='red'), name='System CG'))

    fig3d.update_layout(height=500, scene=dict(aspectmode='data'), margin=dict(l=0,r=0,b=0
