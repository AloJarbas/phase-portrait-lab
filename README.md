# phase-portrait-lab

A tiny public lab for planar dynamical systems.

The point is simple: generate phase portraits that are worth looking at, not just mention the system names and move on.

This repo now opens with four small case studies:

- **Linear saddle** for the cleanest stable-manifold versus unstable-manifold picture
- **Van der Pol** for self-excited oscillation
- **Lotka-Volterra** for predator-prey cycling
- **Brusselator** for a compact reaction-kinetics oscillator

Each portrait combines four things in one figure:

- local flow arrows
- nullclines
- seeded trajectories
- fixed points

The latest pass adds a local-stability layer too:

- fixed-point classification from the Jacobian
- eigenvalue readouts in the SVG side panel
- a CLI report for system-by-system local behavior

That makes the picture more useful than a bare vector field and lighter than a full notebook-only treatment.

## Why this repo is worth opening

- pure Python, no plotting stack required
- generated SVGs, so the output stays sharp in the browser
- a small library shape instead of one throwaway script
- companion notebook for the science side
- tests that check the fixed points, the RK4 stepper, and the new local-stability layer

## Gallery

### Linear saddle

![Linear saddle phase portrait](assets/linear-saddle-phase-portrait.svg)

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
python3 -m phaseportraitlab.cli linear-saddle lotka-volterra
```

## Notebook

See `notebooks/phase_portrait_tour.ipynb` for the companion walkthrough with equations, reading cues, and next questions.

## Repo layout

- `phaseportraitlab/systems.py` defines the system catalog
- `phaseportraitlab/integrate.py` holds the RK4 integrator
- `phaseportraitlab/analysis.py` builds vector fields, trajectories, and Jacobian-based fixed-point analysis
- `phaseportraitlab/cli.py` prints fixed-point classifications and eigenvalue hints
- `phaseportraitlab/svg.py` renders the portraits
- `phaseportraitlab/gallery.py` writes the asset set
- `scripts/generate_gallery.py` rebuilds the gallery
- `tests/test_systems.py` runs the verification pass
- `notebooks/phase_portrait_tour.ipynb` is the companion science notebook

## Next useful moves

- add one notebook on local linearization and Jacobian intuition so the new classification layer has a slower companion
- add one parameter sweep that shows a calm node turning into an oscillator in a controlled way
- add one report mode that compares fixed-point types across several systems at once
