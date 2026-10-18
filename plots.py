# Figures for torque-to-cam: the cam profile (its own tab) and the animated mechanism with the torque and lift graphs.
# The profile uses the calculated points from calc.run(); the animation has its own fixed step, so playback is smooth at any increment.
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from calc import compression, torque

BG = "#0E1117" # matches the dark page background
CAM_FILL = "#2B3542"
LINE = "#C7D0D9"
CAM_EDGE = "#F2F5F8"
BASE_COL = "#8A94A3"
PART = "#8FB3D9"
SPRING = "#E0A84F"
ACCENT = "#5B8DEF"
KNIFE = "#F27C7C"
ROLLERS = "rgba(110,207,151,0.55)"
LIFT_COL = "#A78BFA"
TORQUE_COL = "#4FB3E8"
GRID = "#252C38"
TEXT = "#E6EDF3"
ANGLE_LINE = "#5A6573"

MAX_FRAMES = 180 # most animation frames over the range
MIN_STEP = 1.0 # deg; frames are never closer than this
CAM_POINTS = 720 # most outline points drawn for the turning cam


# ---------- helpers ----------
def _circle(cx, cy, r, n=60): # points around a circle, for drawing
    t = np.linspace(0, 2 * np.pi, n)
    return (cx + r * np.cos(t)).round(2), (cy + r * np.sin(t)).round(2)


def _closed(xy): # outline with the first point repeated at the end
    return np.append(xy[:, 0], xy[0, 0]).round(2), np.append(xy[:, 1], xy[0, 1]).round(2)


def _span(r, p): # half-width that fits the cam and every roller circle
    return max(r.R.max(), np.hypot(r.centres[:, 0], r.centres[:, 1]).max() + p.Rf) + 4


# ---------- cam profile (own tab, never animated) ----------
def profile_fig(r, p, show_circles=True):
    span = _span(r, p)
    fig = go.Figure()
    cx, cy = _closed(r.cam)
    fig.add_trace(go.Scatter(x=cx, y=cy, mode="lines", fill="toself", fillcolor=CAM_FILL,
                             line=dict(color=CAM_EDGE, width=3.5), name="Roller cam")) # the cam you'd build
    bx, by = _circle(0, 0, p.Rb, 180)
    fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color=BASE_COL, width=1.5, dash="dot"), name="Base circle"))
    if show_circles:
        rx, ry = [], [] # every roller circle in one trace, split by None
        for x0, y0 in r.centres:
            x, y = _circle(x0, y0, p.Rf, 40)
            rx += list(x) + [None]
            ry += list(y) + [None]
        fig.add_trace(go.Scatter(x=rx, y=ry, mode="lines", line=dict(color=ROLLERS, width=1.2), name="Roller at each point"))
    fig.add_trace(go.Scatter(x=r.centres[:, 0], y=r.centres[:, 1], mode="lines",
                             line=dict(color=ACCENT, width=3, dash="dash"), name="Roller centre path"))
    fig.add_trace(go.Scatter(x=r.knife[:, 0], y=r.knife[:, 1], mode="lines",
                             line=dict(color=KNIFE, width=3, dash="dot"), name="Knife-edge profile"))
    fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text", text=["O"], textposition="bottom left",
                             marker=dict(color=LINE, size=8), showlegend=False))
    fig.update_traces(hoverinfo="skip")
    fig.update_layout(
        height=820, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor=BG, paper_bgcolor=BG,
        font=dict(size=14, color=TEXT),
        legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top", bgcolor="rgba(23,28,38,0.85)",
                    bordercolor="#3A4452", borderwidth=1, font=dict(size=14)),
    )
    fig.update_xaxes(visible=False, range=[-span, span], constrain="domain") # keep the range fixed, even if the tab starts hidden
    fig.update_yaxes(visible=False, range=[-span, span], scaleanchor="x", scaleratio=1, constrain="domain") # circles stay round
    return fig


# ---------- simulation: mechanism and graph markers (redrawn every frame) ----------
def _sizes(r, p): # fixed mechanism sizes
    span = r.R.max() + 4 # just the turning cam
    base = np.sqrt((p.Rb + p.Rf) ** 2 - p.d**2) # roller centre height on the base circle
    top = base + r.lift.max() + 2.4 * p.Rf + 0.9 * (p.Rb + r.lift.max()) # fixed plate the spring pushes against
    sw = max(0.9 * p.Rf, 5) # spring half-width
    return span, base, top, sw


def _frame(r, p, theta): # every part that moves at this cam angle, in drawing order (later = on top)
    span, base, top, sw = _sizes(r, p)
    T = float(torque(theta, p)) # straight from the formulas, not the calculated points
    s_now = float(compression(theta, p))
    lift = s_now - r.s.min()
    c, s = np.cos(np.radians(theta)), np.sin(np.radians(theta))
    x0, y0 = _closed(r.cam[::max(1, len(r.cam) // CAM_POINTS)]) # thinned outline keeps playback light
    cam_x = (x0 * c - y0 * s).round(2) # cam turned by theta
    cam_y = (x0 * s + y0 * c).round(2)
    yc = base + lift # roller centre height
    rod_top = yc + 2.2 * p.Rf # where the rod meets the spring
    zx = [p.d] + [p.d + (sw if k % 2 else -sw) for k in range(1, 20)] + [p.d] # spring zigzag
    zy = np.linspace(rod_top, top, len(zx)).round(2)
    bx, by = _circle(0, 0, p.Rb, 180)
    rx, ry = _circle(p.d, yc, p.Rf)
    lx = p.d + p.Rf + 4 # lift dimension x position
    text = (f"<b>θ = {theta:.1f}°</b><br>Torque = {T:.2f} N·m<br>"
            f"Compression = {s_now:.2f} mm<br>Lift = {lift:.2f} mm")
    return [
        go.Scatter(x=cam_x, y=cam_y), # cam
        go.Scatter(x=bx, y=by), # base circle
        go.Scatter(x=[p.d, p.d], y=[-span, top]), # follower line
        go.Scatter(x=[0], y=[0]), # cam centre O
        go.Scatter(x=[0, -0.7 * p.Rb * s], y=[0, 0.7 * p.Rb * c]), # cam's 0 deg mark
        go.Scatter(x=zx, y=zy), # spring
        go.Scatter(x=[p.d, p.d], y=[yc, rod_top]), # rod
        go.Scatter(x=[p.d - sw, p.d + sw], y=[rod_top, rod_top]), # spring seat
        go.Scatter(x=rx, y=ry), # roller
        go.Scatter(x=[p.d], y=[yc]), # roller centre
        go.Scatter(x=[lx, lx], y=[base, yc]), # lift dimension
        go.Scatter(x=[p.d - 2 * sw], y=[top - 2], text=[text]), # readout: right edge just left of the spring
        go.Scatter(x=[theta], y=[T]), # dot on torque graph
        go.Scatter(x=[theta, theta], y=[min(r.T.min(), 0), r.T.max()]), # angle line on torque graph
        go.Scatter(x=[theta], y=[lift]), # dot on lift graph
        go.Scatter(x=[theta, theta], y=[0, r.lift.max()]), # angle line on lift graph
    ]


STYLE = [ # look of each part in _frame, same order; set once, frames only change x, y and text
    dict(mode="lines", fill="toself", fillcolor=CAM_FILL, line=dict(color=LINE, width=2.5)), # cam
    dict(mode="lines", line=dict(color=LINE, width=1, dash="dot")), # base circle
    dict(mode="lines", line=dict(color=LINE, width=1, dash="dashdot")), # follower line
    dict(mode="markers+text", text=["O"], textposition="bottom left", marker=dict(color=LINE, size=7)), # cam centre O
    dict(mode="lines", line=dict(color=ACCENT, width=3)), # 0 deg mark
    dict(mode="lines", line=dict(color=SPRING, width=2.5)), # spring
    dict(mode="lines", line=dict(color=PART, width=6)), # rod
    dict(mode="lines", line=dict(color=PART, width=4)), # seat
    dict(mode="lines", fill="toself", fillcolor=BG, line=dict(color=PART, width=2.5)), # roller
    dict(mode="markers", marker=dict(color=PART, size=6)), # roller centre
    dict(mode="lines+markers", line=dict(color=ACCENT, width=1.5),
         marker=dict(symbol="line-ew", size=10, line=dict(width=2, color=ACCENT))), # lift dimension
    dict(mode="text", textposition="bottom left", cliponaxis=False, textfont=dict(size=15, color=TEXT)), # readout
    dict(mode="markers", marker=dict(color=TORQUE_COL, size=12, line=dict(color=BG, width=2))), # torque dot
    dict(mode="lines", line=dict(color=ANGLE_LINE, width=1)), # torque angle line
    dict(mode="markers", marker=dict(color=LIFT_COL, size=12, line=dict(color=BG, width=2))), # lift dot
    dict(mode="lines", line=dict(color=ANGLE_LINE, width=1)), # lift angle line
]
WHERE = [(1, 2)] * 12 + [(1, 1)] * 2 + [(2, 1)] * 2 # subplot of each part: mechanism, torque graph, lift graph


def sim_fig(r, p):
    span, base, top, sw = _sizes(r, p)
    skip = dict(hoverinfo="skip", showlegend=False)
    fig = make_subplots(rows=2, cols=2, column_widths=[0.5, 0.5], horizontal_spacing=0.06, vertical_spacing=0.16,
                        specs=[[{}, {"rowspan": 2}], [{}, None]], # graphs stacked on the left, tall mechanism on the right
                        subplot_titles=("Torque", "Mechanism", "Lift"))

    for tr, st, (row, col) in zip(_frame(r, p, 0), STYLE, WHERE): # moving parts first, so their indices are 0..15
        fig.add_trace(tr.update(**st, **skip), row, col)
    moving = list(range(len(fig.data))) # indices the frames update

    fig.add_trace(go.Scatter(x=[p.d - 1.6 * sw, p.d + 1.6 * sw], y=[top, top], mode="lines",
                             line=dict(color=LINE, width=5), **skip), 1, 2) # fixed plate
    fig.add_trace(go.Scatter(x=r.theta, y=r.T, mode="lines", line=dict(color=TORQUE_COL, width=3.5), fill="tozeroy", fillcolor="rgba(79,179,232,0.12)", showlegend=False,
                             hovertemplate="θ %{x:.1f}°<br>torque %{y:.2f} N·m<extra></extra>"), 1, 1) # torque curve
    fig.add_trace(go.Scatter(x=r.theta, y=r.lift, mode="lines", line=dict(color=LIFT_COL, width=3.5), fill="tozeroy", fillcolor="rgba(167,139,250,0.12)", showlegend=False,
                             hovertemplate="θ %{x:.1f}°<br>lift %{y:.2f} mm<extra></extra>"), 2, 1) # lift curve

    step = max(MIN_STEP, p.end / MAX_FRAMES) # animation step, separate from the increment
    angles = np.append(np.arange(0, p.end - 1e-9, step), p.end).round(2) # always end on the end angle
    fig.frames = [go.Frame(name=f"{a:g}", data=_frame(r, p, a), traces=moving) for a in angles] # sent to the browser once

    play = dict(frame=dict(duration=40, redraw=True), transition=dict(duration=0), fromcurrent=True, mode="immediate")
    pause = dict(frame=dict(duration=0, redraw=False), mode="immediate")
    fig.update_layout(
        height=820, margin=dict(l=60, r=20, t=40, b=120), plot_bgcolor=BG, paper_bgcolor=BG,
        font=dict(size=14, color=TEXT), hoverlabel=dict(font_size=13, bgcolor="#171C26", font_color=TEXT),
        updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.12, xanchor="left", yanchor="top", showactive=False, # no white highlight on the pressed button
                          bgcolor="#171C26", bordercolor="#3A4452", font=dict(size=14, color=TEXT),
                          buttons=[dict(label="Play", method="animate", args=[None, play]),
                                   dict(label="Pause", method="animate", args=[[None], pause])])],
        sliders=[dict(x=0.12, y=-0.12, len=0.88, xanchor="left", yanchor="top", pad=dict(t=0),
                      bgcolor="#2B3542", activebgcolor=ACCENT, bordercolor="#3A4452",
                      ticklen=0, font=dict(color="rgba(0,0,0,0)"), # hide the step labels
                      currentvalue=dict(prefix="Cam angle θ = ", suffix="°", font=dict(size=14, color=TEXT)),
                      steps=[dict(label=f"{a:g}", method="animate",
                                  args=[[f"{a:g}"], dict(frame=dict(duration=0, redraw=True), mode="immediate")])
                             for a in angles])],
    )
    fig.update_xaxes(visible=False, range=[-span - 26, span + abs(p.d) + 6], constrain="domain", row=1, col=2) # extra room on the left for the readout
    fig.update_yaxes(visible=False, range=[-span, top + 4], scaleanchor="x2", scaleratio=1, constrain="domain", row=1, col=2) # circles stay round
    for row, title in [(1, "torque (N·m)"), (2, "lift (mm)")]:
        fig.update_xaxes(range=[0, p.end], gridcolor=GRID, showline=True, linecolor="#3A4452",
                         tickfont=dict(size=13, color=TEXT), row=row, col=1)
        fig.update_yaxes(title=title, gridcolor=GRID, zerolinecolor="#6B7684", zerolinewidth=1.5, showline=True,
                         linecolor="#3A4452", tickfont=dict(size=13, color=TEXT), row=row, col=1)
    fig.update_xaxes(title="cam angle θ (deg)", row=2, col=1)
    fig.update_annotations(font=dict(size=16, color=TEXT)) # subplot titles
    return fig