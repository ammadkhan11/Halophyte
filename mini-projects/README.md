# Mini Projects

Self-contained side projects related to the Halophyte project's broader theme (salinity, salt-tolerant agriculture, remote sensing). Each one lives in its own folder, runs independently, and does **not** modify or depend on the main app in `src/` / `backend/` / `ml/`.

## Index

| Project | Description | Stack |
|---|---|---|
| [`soil-salinity-crop-zoning/`](./soil-salinity-crop-zoning) | Satellite-driven soil salinity prediction + crop recommendation for Punjab/Sindh, Pakistan | Python, Google Earth Engine, scikit-learn, Streamlit |

*(More projects will be added here over time — see "Adding a new mini-project" below.)*

---

## Adding a new mini-project

1. Create a new folder under `mini-projects/` named after the project, e.g. `mini-projects/your-project-name/`.
2. Inside it, include at minimum:
   - `README.md` — a guide doc covering: what the project is, the problem/need it solves, the use case, how it works, and the tech stack (backend + frontend, or note if it's a single-process app like Streamlit).
   - The actual project files (notebook, source code, etc.)
   - A `docs/` subfolder for any supporting PDFs, briefs, or design docs (optional).
3. Add a row for it in the **Index** table above.
4. Do not edit anything outside `mini-projects/` unless you are intentionally integrating it into the main app.

This keeps every mini-project isolated, so the main Halophyte app's build/run instructions never need to change as more get added.
