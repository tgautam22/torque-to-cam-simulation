# Streamlit page for torque-to-cam. Run with:  streamlit run app.py
import streamlit as st

from calc import Params, run
from plots import profile_fig, sim_fig

st.set_page_config(page_title="Torque to cam", layout="wide")
st.markdown("<style>.block-container{padding-top:2rem;padding-bottom:1rem}</style>", unsafe_allow_html=True) # less empty space at the top

# ---------- inputs (sidebar) ----------
d = Params() # defaults
sb = st.sidebar
sb.title("Inputs")

sb.subheader("Torque wanted")
sb.caption("T = a₀ + a₁θ + a₂θ² + a₃θ³  (θ in rad, T in N·m)")
a, b = sb.columns(2)
a0 = a.number_input("a₀", value=d.a0, step=0.1, format="%.4f")
a1 = b.number_input("a₁", value=d.a1, step=0.1, format="%.4f")
a, b = sb.columns(2)
a2 = a.number_input("a₂", value=d.a2, step=0.1, format="%.4f")
a3 = b.number_input("a₃", value=d.a3, step=0.1, format="%.4f")
a, b = sb.columns(2)
end = a.number_input("End (°)", value=d.end, step=5.0, min_value=1.0, max_value=350.0)
inc = b.number_input("Increment (°)", value=d.inc, step=0.5, min_value=0.1, max_value=10.0,
                     help="Degrees between calculated points. Each point gets one roller circle on the profile.")

sb.subheader("Spring")
a, b = sb.columns(2)
k = a.number_input("Spring k (N/mm)", value=d.k, step=5.0, min_value=0.1)
s0 = b.number_input("Preload (mm)", value=d.s0, step=0.5, min_value=0.0)

sb.subheader("Cam and follower")
a, b = sb.columns(2)
Rb = a.number_input("Base radius (mm)", value=d.Rb, step=1.0, min_value=0.1)
Rf = b.number_input("Roller radius (mm)", value=d.Rf, step=0.5, min_value=0.1)
off = sb.number_input("Offset d (mm)", value=d.d, step=0.5)

p = Params(a0=a0, a1=a1, a2=a2, a3=a3, end=end, inc=inc, k=k, s0=s0, Rb=Rb, Rf=Rf, d=off)
error = p.check()


@st.cache_data # only recalculates when an input changes
def build(p):
    r = run(p)
    return r, sim_fig(r, p)


@st.cache_data
def build_profile(p, show_circles):
    return profile_fig(run(p), p, show_circles)


# ---------- page ----------
st.title("Torque to cam")
st.caption("Set the torque you want on the left. The Cam profile tab shows how the shape is built; the Simulation tab turns it.")

if error:
    st.error(error)
    st.stop() # nothing below runs until the inputs are fixed

r, fig = build(p)

m1, m2, m3, m4 = st.columns(4) # one-glance summary of the design
m1.metric("Points", f"{len(r.theta)}", help=f"Every {p.inc:g}° from 0° to {p.end:g}°.")
m2.metric("Max lift", f"{r.lift.max():.2f} mm")
m3.metric("Max compression", f"{r.s.max():.2f} mm")
m4.metric("Biggest cam radius", f"{r.R.max():.2f} mm")

tab_profile, tab_sim, tab_method = st.tabs(["Cam profile", "Simulation", "Method"])

with tab_profile:
    show = st.toggle("Show roller circles", value=True, help="One roller circle at each calculated point. The cam is the curve touching the inside of all of them.")
    st.plotly_chart(build_profile(p, show), width="stretch", theme=None) # its own figure, so Play and Pause never touch it

with tab_sim:
    st.plotly_chart(fig, width="stretch", theme=None) # theme=None keeps our own fonts and colours; Play, Pause and the slider are inside the figure

with tab_method:
    st.caption(f"Every curve is calculated every {p.inc:g}°. Angles in degrees, lengths in mm, k in N/mm, torque in N·m.")
    steps = [
        ("Torque wanted", r"T(\theta) = a_0 + a_1\theta + a_2\theta^2 + a_3\theta^3 \quad (\theta \text{ in rad})"),
        ("Spring compression", r"s(\theta) = \sqrt{s_0^2 + \dfrac{2}{k}\left(a_0\theta + \dfrac{a_1\theta^2}{2} + \dfrac{a_2\theta^3}{3} + \dfrac{a_3\theta^4}{4}\right)}"),
        ("Lift", r"\text{lift}(\theta) = s(\theta) - s_{min}"),
        ("Knife-edge point", r"Y = \sqrt{R_b^2 - d^2} + \text{lift}"),
        ("Roller centre", r"Y = \sqrt{(R_b + R_f)^2 - d^2} + \text{lift}"),
        ("Onto the cam", r"x = d\cos\theta + Y\sin\theta,\quad y = -d\sin\theta + Y\cos\theta"),
        ("Cam surface", r"R(\varphi) = \min\left(P\cos(\varphi - A) - \sqrt{R_f^2 - P^2\sin^2(\varphi - A)}\right)"),
    ]
    for n, (label, formula) in enumerate(steps, start=1):
        left, right = st.columns([1, 3], vertical_alignment="center")
        left.markdown(f"**{n}. {label}**")
        right.latex(formula)
   