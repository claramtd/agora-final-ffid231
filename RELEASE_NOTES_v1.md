# Release Notes v1.0.0

## AGORA Final FFID 231 Demonstration Repository

This initial release documents an AGORA-aligned 2D shot-domain seismic processing workflow for `FFID 231` from the dataset **2D Vibroseis Seismic Data Line 001 - Poland**.

## Included in this release

- standalone subproject layout for GitHub publication
- data preparation workflow from SEG-Y to NumPy arrays
- extraction workflow for `FFID 231`
- stage-by-stage AGORA-aligned processing pipeline
- processing configuration in JSON format
- flowchart and repository documentation
- prepared subset data for `FFID 231`
- demonstration QC outputs and summary metrics

## Processing scope

The repository covers:

1. SEG-Y input preparation,
2. extraction of the target field file identifier,
3. geometry and offset QC,
4. preclean and first-break protection,
5. band-limit and resampling,
6. AGORA characterization,
7. FK-based coherent-noise modeling and attenuation,
8. final QC documentation.

## Notes

- This implementation is AGORA-aligned and intended for documentation, reproducibility, and academic demonstration.
- It is not the proprietary CGG AGORA engine.
- The demonstrated example is limited to `FFID 231` and should be treated as a documented case study.
