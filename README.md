# phase-portrait-lab

A tiny public lab for planar dynamical systems.

The point is simple: generate phase portraits that are worth looking at, not just mention the system names and move on.

This repo opens with three small case studies:

- **Van der Pol** for self-excited oscillation
- **Lotka-Volterra** for predator-prey cycling
- **Brusselator** for a compact reaction-kinetics oscillator

Each portrait combines four things in one figure:

- local flow arrows
- nullclines
- seeded trajectories
- fixed points

That makes the picture more useful than a bare vector field and lighter than a full notebook-only treatment.

## Why this repo is worth opening

- pure Python, no plotting stack required
- generated SVGs, so the output stays sharp in the browser
- a small library shape instead of one throwaway script
- companion notebook for the science side
- tests that at least check the fixed points and the RK4 stepper

## Gallery

### Van der Pol oscillator

![Van der Pol phase portrait](assets/vanderpol-phase-portrait.svg)

### Lotka-Volterra predator-prey

![Lotka-Volterra phase portrait](assets/lotka-volterra-phase-portrait.svg)

### Brusselator

![Brusselator phase portrait](assets/brusselator-phase-portrait.svg)

## Quick start

```bash
python3 scripts/generate_gallery.py
python3 -m unittest discover -s tests
```

## Notebook

See `notebooks/phase_portrait_tour.ipynb` for the companion walkthrough with equations, reading cues, and next questions.

## Repo layout

- `phaseportraitlab/systems.py` defines the system catalog
- `phaseportraitlab/integrate.py` holds the RK4 integrator
- `phaseportraitlab/analysis.py` builds vector fields and trajectories
- `phaseportraitlab/svg.py` renders the portraits
- `phaseportraitlab/gallery.py` writes the asset set
- `scripts/generate_gallery.py` rebuilds the gallery
- `tests/test_systems.py` runs the small verification pass
- `notebooks/phase_portrait_tour.ipynb` is the companion science notebook

## Next useful moves

- add a saddle-point example so stable and unstable manifolds show up explicitly
- add one bifurcation-focused notebook instead of stopping at static portraits
- add a small CLI that prints fixed points and local linearization hints
