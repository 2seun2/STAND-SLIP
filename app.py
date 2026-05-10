import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. 기본 설정 및 데이터 ---
st.set_page_config(page_title="TV Tilt Analysis", layout="wide")

TV_MODELS = {
    "98인치 Neo QLED": {"mass": 68.0, "w": 2185, "h": 1249, "d": 30},
    "85인치 Neo QLED": {"mass": 43.5, "w": 1892, "h": 1082, "d": 25},
    "75인치 Neo QLED": {"mass": 34.1, "w": 1670, "h": 957, "d": 20}
}

# --- 2. 사이드바: 설계 제원 (좌측 레이아웃) ---
with st.sidebar:
    st.header("📋 설계 제원 (Specs)")
    model_sel = st.selectbox("TV 모델 선택", list(TV_MODELS.keys()))
    spec = TV_MODELS[model_sel]
    
    tw = st.number_input("Panel Width (mm)", value=spec['w'])
    th = st.number_input("Panel Height (mm)", value=spec['h'])
    td = st.number_input("Panel Depth (mm)", value=spec['d'])
    mass = st.number_input("Total Mass (kg)", value=spec['mass'])
    
    st.markdown("---")
    st.subheader("🦶 Stand Geometry")
    st_depth = st.slider("Stand Total Depth (mm)", 100, 800, 450)
    pivot_dist = st.slider("Pivot Distance (d_p) (mm)", 50, 400, 200)
    cg_h = st.slider("CG Height (h_cg) (mm)", 100, int(th/2), 350)
    
    st.markdown("---")
    tilt_angle = st.slider("Tilt Angle (θ) (°)", 0.0, 45.0, 20.0)

# --- 3. 공학 계산 (Logic) ---
# 임계 각도: theta = arctan(d_pivot / h_cg)
critical_angle = np.degrees(np.arctan(pivot_dist / cg_h))
is_stable = tilt_angle < critical_angle

# --- 4. 시각화 로직 (강체 회전) ---
def get_rotated_coords(w, h, d, ox, oy, oz, angle):
    # 기본 정점 (Z-up 기준)
    x = np.array([-w/2, w/2, w/2, -w/2, -w/2, w/2, w/2, -w/2]) + ox
    y = np.array([-d/2, -d/2, -d/2, -d/2, d/2, d/2, d/2, d/2]) + oy
    z = np.array([0, 0, h, h, 0, 0, h, h]) + oz
    
    # X축 기준 회전 행렬 적용
    rad = np.radians(angle)
    # y' = y*cos - z*sin, z' = y*sin + z*cos
    ry = y * np.cos(rad) - z * np.sin(rad)
    rz = y * np.sin(rad) + z * np.cos(rad)
    return x, ry, rz

# 메쉬 인덱스
I, J, K = [0,1,2,0,2,3,4,5,6,4,6,7,0,1,5,0,5,4,1,2,6,1,6,5,2,3,7,2,7,6,3,0,4,3,4,7], \
         [1,2,3,3,0,2,5,6,7,7,4,6,1,5,4,4,0,5,2,6,5,5,1,6,3,7,6,6,2,7,0,4,7,7,3,4], \
         [2,3,0,1,1,3,6,7,4,5,5,7,5,4,0,1,1,0,6,5,1,2,2,1,7,6,2,3,3,2,4,7,3,0,0,3]

# --- 5. 메인 레이아웃 (스케치 반영) ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("📦 3D Perspective")
    # TV Panel & Stand를 하나의 강체로 렌더링
    px, py, pz = get_rotated_coords(tw, th, td, 0, 0, 0, tilt_angle)
    # 바닥면
    fx, fy, fz = get_rotated_coords(tw+500, 10, st_depth+200, 0, 0, -20, tilt_angle)
    
    fig3d = go.Figure()
    fig3d.add_trace(go.Mesh3d(x=px, y=py, z=pz, i=I, j=J, k=K, color='royalblue', opacity=0.8, name='TV'))
    fig3d.add_trace(go.Mesh3d(x=fx, y=fy, z=fz, i=I, j=J, k=K, color='lightgray', opacity=0.5, name='Floor'))
    
    # CG 포인트
    rad = np.radians(tilt_angle)
    cg_y, cg_z = 0 * np.cos(rad) - cg_h * np.sin(rad), 0 * np.sin(rad) + cg_h * np.cos(rad)
    fig3d.add_trace(go.Scatter3d(x=[0], y=[cg_y], z=[cg_z], mode='markers', marker=dict(size=8, color='red')))
    
    fig3d.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=450, scene=dict(aspectmode='data'))
    st.plotly_chart(fig3d, use_container_width=True)

with row1_col2:
    st.subheader("📐 2D Side Profile")
    # 2D 단면 벡터 계산
    rad = np.radians(tilt_angle)
    # TV 라인
    line_z = [0, th * np.cos(rad)]
    line_y = [0, -th * np.sin(rad)]
    
    fig2d = go.Figure()
    # 바닥 기울기 선
    fig2d.add_shape(type="line", x0=-400, y0=0, x1=400, y1=0, line=dict(color="Black", width=3))
    # TV 단면
    fig2d.add_trace(go.Scatter(x=line_y, y=line_z, mode='lines', line=dict(width=10, color='royalblue')))
    # CG 및 중력선
    curr_cg_y = -cg_h * np.sin(rad)
    curr_cg_z = cg_h * np.cos(rad)
    fig2d.add_trace(go.Scatter(x=[curr_cg_y], y=[curr_cg_z], mode='markers+text', 
                               text=["CG"], textposition="top center", marker=dict(size=12, color='red')))
    fig2d.add_trace(go.Scatter(x=[curr_cg_y, curr_cg_y], y=[curr_cg_z, 0], mode='lines', line=dict(dash='dash', color='red')))
    
    fig2d.update_layout(height=450, showlegend=False, xaxis=dict(range=[-500, 500]), yaxis=dict(range=[-50, 1300]))
    st.plotly_chart(fig2d, use_container_width=True)

# 하단 결과 및 로직 영역
st.markdown("---")
res_col1, res_col2 = st.columns([1, 3])

with res_col1:
    st.markdown("### 🏁 Result")
    if is_stable:
        st.success(f"**Stable (안정)**\n\nMargin: {critical_angle - tilt_angle:.2f}°")
    else:
        st.error(f"**Tipped (전도)**\n\nOver: {tilt_angle - critical_angle:.2f}°")

with res_col2:
    st.markdown("### 🧠 Engineering Logic")
    st.latex(r"\theta_{critical} = \arctan\left(\frac{d_{pivot}}{h_{cg}}\right)")
    st.write(f"현재 모델의 Pivot 거리({pivot_dist}mm)와 CG 높이({cg_h}mm) 기준:")
    st.latex(f"\\arctan\\left(\\frac{{{pivot_dist}}}{{{cg_h}}}\\right) = {critical_angle:.2f}^\circ")
