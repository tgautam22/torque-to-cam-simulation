# Tests for calc.py. Each one checks the answer a different way than calc.py gets it. 
# Run with:  python -m pytest
import numpy as np
import pytest

from calc import Params, run


def test_constant_torque_by_hand(): # constant 5 N*m over 90 deg, worked out on paper with energy
    r = run(Params(a0=5.0, a1=0.0, a2=0.0, a3=0.0, end=90.0, k=100.0, s0=5.0))
    # work in = T * angle = 5 N*m * (pi/2 rad) = 7.854 J = 7854 N*mm
    # spring energy gained = 0.5 * k * (s^2 - s0^2) = 50 * (s^2 - 25)  ->  s^2 = 25 + 7854/50 = 182.08  ->  s = 13.494 mm
    assert r.s[-1] == pytest.approx(13.494, abs=0.001)


def test_energy_balance(): # work from the torque curve (added up numerically) = energy stored in the spring
    p = Params(inc=0.1)
    r = run(p)
    work = np.trapezoid(r.T, np.radians(r.theta)) * 1000 # N*m*rad -> N*mm
    stored = 0.5 * p.k * (r.s[-1] ** 2 - p.s0**2) # N*mm
    assert stored == pytest.approx(work, rel=1e-4)


def test_torque_comes_back(): # run the compression forwards through T = k*s*ds/dth and get the torque we asked for
    p = Params(a0=1.0, a1=2.0, a2=1.5, a3=-0.3, inc=0.1)
    r = run(p)
    ds = np.gradient(r.s, np.radians(r.theta)) # slope found numerically, not from the formula
    T_back = p.k * r.s * ds / 1000
    inner = slice(1, -1) # end points use a one-sided slope, so skip them
    assert T_back[inner] == pytest.approx(r.T[inner], rel=1e-3, abs=1e-3)


@pytest.mark.parametrize("d", [0.0, 6.0, -8.0])
def test_roller_sits_on_cam(d): # the cam never cuts into any roller, and touches each one (no gap)
    p = Params(inc=0.1, Rf=8.0, d=d)
    r = run(p)
    for cx, cy in r.centres[5:-5]: # skip the very ends, where the cam drops back to the base circle
        gap = np.hypot(r.cam[:, 0] - cx, r.cam[:, 1] - cy).min() # closest cam point to this roller centre
        assert gap >= p.Rf - 1e-6 # never inside the roller
        assert gap <= p.Rf + 0.02 # and touching it (0.02 mm allows for points every 0.1 deg)


@pytest.mark.parametrize("d", [0.0, 6.0, -8.0])
def test_points_land_on_follower_line(d): # turn each point forward by its cam angle: it must sit on the line x = d at the right height
    p = Params(d=d)
    r = run(p)
    c, s = np.cos(np.radians(r.theta)), np.sin(np.radians(r.theta))
    for pts, base in [(r.knife, np.sqrt(p.Rb**2 - d**2)), (r.centres, np.sqrt((p.Rb + p.Rf) ** 2 - d**2))]: # knife-edge on the base circle, roller centre on the prime circle
        x = pts[:, 0] * c - pts[:, 1] * s # where the point is when the cam has turned by theta
        y = pts[:, 0] * s + pts[:, 1] * c
        assert x == pytest.approx(np.full_like(x, d), abs=1e-9) # on the follower line
        assert y == pytest.approx(base + r.lift, abs=1e-9) # lifted by exactly the lift


def test_cam_never_inside_base_circle(): # torque that goes negative first: the spring relaxes below preload, but lift still starts from 0
    r = run(Params(a1=-3.0, a2=3.0, s0=10.0))
    assert r.s.min() < 10.0 # the spring really did relax below preload
    assert r.lift.min() == pytest.approx(0, abs=1e-12) # lowest point sits on the base circle
    assert r.R.min() >= 25.0 - 1e-9 # no part of the cam is smaller than the base radius


def test_increment_only_changes_resolution(): # the same angle gives the same lift whatever the increment
    coarse, fine = run(Params(inc=2.0)), run(Params(inc=0.5))
    at_60_coarse = coarse.lift[np.isclose(coarse.theta, 60)][0]
    at_60_fine = fine.lift[np.isclose(fine.theta, 60)][0]
    assert at_60_coarse == pytest.approx(at_60_fine, abs=1e-12)


def test_spring_would_stretch():
    error = Params(a2=-5.0, s0=1.0).check() # torque goes negative enough to pull the spring past free length
    assert error is not None and "stretch" in error


def test_torque_at_start_needs_preload():
    error = Params(a0=2.0, s0=0.0).check() # torque above 0 at the start, but the spring isn't loaded yet
    assert error is not None and "preload" in error


def test_default_inputs_are_fine():
    assert Params().check() is None