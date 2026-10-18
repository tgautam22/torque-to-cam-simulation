# Torque to Cam Simulation

This simulation allows you to design a cam profile for a roller, follower, and spring from a torque curve you choose. Shows how the cam profile is built and simulates the finished cam in an actual cam-spring system to check it.

## Inputs

- a0, a1, a2, a3: coefficients of the torque wanted, T = a0 + a1θ + a2θ² + a3θ³ (θ in rad, T in N·m)
- End: last cam angle the profile is designed for (deg)
- Increment: degrees between calculated points; smaller gives a smoother profile
- Spring k: spring constant (N/mm)
- Preload: how much the spring is compressed at the start (mm)
- Base radius: radius of the cam without any lift (mm)
- Roller radius: radius of the roller follower (mm)
- Offset: sideways distance of the follower line from the cam centre (mm)

The Method tab in the app explains the calculations in detail.

## Setup

```
git clone https://github.com/tgautam22/torque-to-cam-simulation.git
cd torque-to-cam-simulation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```
streamlit run app.py
```

## Test

```
python -m pytest
```

## Files

- calc.py: all the calculations
- plots.py: the cam profile drawing, and the animated mechanism with the torque and lift graphs
- app.py: the Streamlit page
- tests/test_calc.py: tests for calc.py

## References

- Realmuto, J., Klute, G., and Devasia, S. (2015). Nonlinear Passive Cam-Based Springs for Powered Ankle Prostheses. Journal of Medical Devices, 9(1), 011007.
