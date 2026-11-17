---
name: india-map
description: Prepare and verify geographic maps for studio covers, reels and video graphics using the Government of India's boundary depiction. Use for India maps, Indian states and territories, and world or regional maps that include India; exclude software diagrams and mind maps.
---

# India maps for studio graphics

Resolve the studio root two directories above this skill. This is the shared map workflow for cover images and every video editor. Read [references/sources.md](references/sources.md) to choose the actual official source and its usage terms.

## Source the geography

- Use the Government of India's depiction, with Survey of India as the boundary reference. Prefer the appropriate official outline/vector product for an outline and the official political/state map for administrative divisions. Check the current source when obtaining or updating data; retain the dated project snapshot on resume.
- Do not use a generic Natural Earth, OpenStreetMap or stock silhouette without checking its boundary depiction. AI-generated geography and hand-invented outlines are not substitutes for source geometry. A third-party dataset claiming an India point of view still needs comparison with the official reference and recorded provenance.
- Preserve the complete northern boundary, Jammu and Kashmir, Ladakh, Arunachal Pradesh, the northeast connection, and the island groups as depicted in the chosen official product. For state/UT graphics, verify the current official administrative divisions and labels. For regional/world maps, use compatible adjoining polygons so mixed boundary editions do not create overlaps or gaps.
- Establish the source's usage rights for the actual deliverable. A free download is not necessarily commercially reusable. Keep restricted official downloads and derivatives in the local project, out of the distributable skill. If a dataset permits internal review but not commercial use, label the result accordingly and use a source with appropriate permission for a commercial deliverable. Do not silently fall back to a different boundary to avoid a rights issue.

## Prepare the artwork

- Use code to render verified geometry, not image generation. Preserve the projection or apply a documented proper map projection; keep proportions with uniform scaling. No freehand border fixes, arbitrary perspective warps, mirroring, or removal of detached polygons to make the shape fit.
- For the official polygon-shapefile ZIP, the local helper can make a transparent PNG while retaining all source rings and islands:

  ```bash
  skills/effects/.venv/bin/python skills/india-map/scripts/render_outline.py --archive PROJECT/maps/Outline_of_India.zip --output PROJECT/maps/india-outline.png --source-url https://surveyofindia.gov.in/documents/Outline_of_India.zip
  ```

  Use the actual project paths. Windows uses `skills/effects/.venv/Scripts/python.exe`. The helper needs Pillow from the existing effects environment and Python's standard library. Download/verify the source separately; the helper cannot authenticate an archive's provenance or grant reuse rights.
- Style fill, stroke, labels and animation to the current cover/video design without changing the boundary. For covers, pass the prepared image as `hero.image` to the cover renderer and omit superseded `hero.polygons`. Add the required source acknowledgement. For video graphics, import the same vetted asset/geometry into the selected editor and animate position, scale or reveals without redrawing its border.
- A regional close-up is valid when clearly framed as that region. A cover labelled India should not accidentally crop away territories or islands; fit the complete chosen outline or use a clearly labelled inset derived from the same source.

## Review and retain

- Inspect the actual output beside the official reference, especially the northern border, northeast, coast and island groups. Check colour/label legibility and edge clipping at final resolution. A source URL, dataset name or successful render alone does not establish correctness.
- Record source page and download URLs, retrieval date, source edition when provided, archive SHA-256, projection, transformation, usage terms, attribution, derived files and review status in the project's map manifest. Keep the original source unchanged. Cache by source hash; changes require fresh visual verification.
- Show the actual map/cover inline with absolute local image paths. In video workflows, include it in the existing plan and actual-frame review. This skill never approves the video or bypasses the editor's frame/audio gates.
- Do not claim Government of India/Survey of India certification, endorsement or official authorship of a styled derivative. Distinguish an official source from the studio's rendering.
