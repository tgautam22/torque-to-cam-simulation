# Calculations for torque-to-cam: torque -> spring compression -> lift -> knife-edge and roller centres -> cam surface
# Units: mm, deg, k in N/mm, torque in N*m. Points are calculated every `inc` degrees.
from dataclasses import dataclass

import numpy as np


@dataclass
class Params:
    # torque wanted: T = a0 + a1*th + a2*th^2 + a3*th^3 (th in rad, T in N*m)
    a0: float = 0.0
    a1: float = 0.0
    a2: float = 15 / np.radians(160) ** 2 # reaches 15 N*m at 160 deg
    a3: float = 0.0
    end: float = 160.0 # last cam angle (deg)
    inc: float = 1.0 # deg between calculated points
    # spring
    k: float = 100.0 # spring constant (N/mm)
    s0: float = 5.0 # preload (mm)
    # cam and follower
    Rb: float = 25.0 # base radius (mm)
    Rf: float = 6.0 # roller radius (mm)
    d: float = 0.0 # offset of the follower line (mm)

    def check(self): # returns an error message, or None if the inputs are fine
        if not 0 < self.end <= 350:
            return "End must be above 0 and no more than 350 deg."
        if not 0.1 <= self.inc <= 10:
            return "Increment must be between 0.1 and 10 deg."
        if self.k <= 0 or self.Rb <= 0 or self.Rf <= 0:
            return "k and radii must be above zero."
        if self.s0 < 0:
            return "Preload can't be negative."
        if abs(self.d) >= self.Rb:
            return "Offset must be smaller than the base radius."
        if self.a0 != 0 and self.s0 <= 0:
            return "With a0 not zero the torque starts above 0, so the preload has to be above 0."
        inside = self.s0**2 + (2000 / self.k) * _area(angles(self), self) # same value step 5 takes the root of
        if inside.min() < 0:
            return "The value inside the square root goes below zero, so the spring would have to stretch. Increase the preload."
        return None


@dataclass
class Result:
    theta: np.ndarray # cam angles of the calculated points (deg)
    T: np.ndarray # torque wanted (N*m)
    s: np.ndarray # spring compression (mm)
    lift: np.ndarray # follower lift (mm)
    knife: np.ndarray # knife-edge profile points on the cam, shape (n, 2) (mm)
    centres: np.ndarray # roller centres on the cam, shape (n, 2) (mm)
    phi: np.ndarray # directions around the cam for the outline (deg)
    R: np.ndarray # roller cam radius in each direction (mm)
    cam: np.ndarray # roller cam outline, shape (m, 2) (mm)


def angles(p): # 0, inc, 2*inc ... end (the last point lands exactly on end)
    th = np.arange(0, p.end, p.inc, dtype=float)
    th = th[th < p.end - 1e-9] # drop a rounding-error point sitting right on top of end
    return np.append(th, p.end)


def _area(theta, p): # integral of T from 0 to theta: a0*th + a1*th^2/2 + a2*th^3/3 + a3*th^4/4
    t = np.radians(theta)
    return p.a0 * t + p.a1 * t**2 / 2 + p.a2 * t**3 / 3 + p.a3 * t**4 / 4


def torque(theta, p): # T = a0 + a1*th + a2*th^2 + a3*th^3
    t = np.radians(theta)
    return p.a0 + p.a1 * t + p.a2 * t**2 + p.a3 * t**3


def compression(theta, p): # Realmuto Eq. 23: s = sqrt(s0^2 + (2/k) * area), 2000 = 2 * (N*m -> N*mm)
    return np.sqrt(p.s0**2 + (2000 / p.k) * _area(theta, p))


def on_cam(theta, Y, p): # point at height Y on the follower line x = d, turned back by theta onto the cam
    t = np.radians(theta)
    x = p.d * np.cos(t) + Y * np.sin(t)
    y = -p.d * np.sin(t) + Y * np.cos(t)
    return np.column_stack([x, y])


def contacts(centres, p): # where each roller touches the cam: one roller radius in from its centre, square to the centre path
    tang = np.gradient(centres, axis=0) # direction the centre path is heading
    n = np.column_stack([-tang[:, 1], tang[:, 0]]) / np.hypot(tang[:, 0], tang[:, 1])[:, None] # square to the path
    n[(n * centres).sum(axis=1) > 0] *= -1 # make it point in towards O
    return centres + p.Rf * n


def cam_surface(centres, p): # in each direction, the cam reaches out only to the nearest roller circle
    phi = np.arange(0, 360, p.inc, dtype=float) # directions around the cam
    P = np.hypot(centres[:, 0], centres[:, 1]) # distance of each roller centre from O
    A = np.arctan2(centres[:, 0], centres[:, 1]) # angle of each roller centre (clockwise from the top)
    R = np.full_like(phi, p.Rb) # base circle where no roller reaches

    c = contacts(centres, p)
    ca = np.degrees(np.unwrap(np.arctan2(c[:, 0], c[:, 1]))) # contact angles, without the jump at 180
    lo, hi = ca.min(), ca.max() # the span the rollers actually touch
    used = (phi - lo) % 360 <= hi - lo # outside it the cam is just the base circle

    for j, ph in zip(np.flatnonzero(used), np.radians(phi[used])):
        along = P * np.cos(ph - A) # roller centre's distance along this direction
        across = P * np.sin(ph - A) # and sideways from it
        hit = (along > 0) & (np.abs(across) <= p.Rf) # rollers this direction passes through
        if hit.any():
            R[j] = (along[hit] - np.sqrt(p.Rf**2 - across[hit] ** 2)).min() # near edge of the closest roller

    cam = np.column_stack([R * np.sin(np.radians(phi)), R * np.cos(np.radians(phi))])
    return phi, R, cam


def run(p): # whole pipeline in one call
    theta = angles(p)
    T = torque(theta, p)
    s = compression(theta, p)
    lift = s - s.min() # lift = s - smallest s
    knife = on_cam(theta, np.sqrt(p.Rb**2 - p.d**2) + lift, p) # lift on top of the base circle
    centres = on_cam(theta, np.sqrt((p.Rb + p.Rf) ** 2 - p.d**2) + lift, p) # lift on top of the prime circle
    phi, R, cam = cam_surface(centres, p)
    return Result(theta, T, s, lift, knife, centres, phi, R, cam)