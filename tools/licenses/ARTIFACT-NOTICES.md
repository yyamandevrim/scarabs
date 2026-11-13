# Artifact redistribution notices

This notice is CC0-1.0. It does not change any underlying licence. Checked 2026-11-13.
Publish this notice and artifacts-manifest.json beside the objects; keep public read access to their licence and source links. No bucket ACL is changed by the uploader.

## Prepared rasters and offline map images — CC BY 4.0

Contains National Land Survey of Finland Elevation model 10 m (2019 Paituli archive); Finnish Environment Institute (Syke), CORINE Land Cover 2024 national 20 m; Natural Resources Institute Finland (Luke), MS-NFI 2023 mean stand height and canopy cover. Accessed 2026-11-13. Clipped/reprojected, aggregated and converted to local PNG map images by this project. No endorsement implied. Raster source URLs and processing are retained in metadata.json and placement/README.md.

- NLS terms: https://www.maanmittauslaitos.fi/en/opendata-licence-cc40
- Syke terms: https://www.syke.fi/en/environmental-data/use-license-and-responsibilities
- Luke product and terms: https://kartta.luke.fi/index-en.html
- Licence: https://creativecommons.org/licenses/by/4.0/

The previously documented Luke README-2023.txt URL returned 404 during this review; the live Luke product index confirms CC BY 4.0. These licences allow redistribution with attribution and change notices.

## Model — AGPL-3.0-only

Pyronear YOLO11s, Tenacious Tiger v8.3.0, unmodified ONNX export. Revision de398b5192b2c1d5f8963aef56bf8df1f13c159e. The pinned upstream licence and model card expressly cover PyTorch, ONNX and NCNN weights under AGPL-3.0. Its Ultralytics ancestry is retained. Full licence accompanies the bundle as PYRONEAR-AGPL-3.0.txt.

- Pinned repository/model card: https://huggingface.co/pyronear/yolov11s/tree/de398b5192b2c1d5f8963aef56bf8df1f13c159e
- Original editable weights: https://huggingface.co/pyronear/yolov11s/resolve/de398b5192b2c1d5f8963aef56bf8df1f13c159e/best.pt
- Training/export manifest: https://huggingface.co/pyronear/yolov11s/raw/de398b5192b2c1d5f8963aef56bf8df1f13c159e/manifest.yaml
- Training/export source: https://github.com/pyronear/pyro-train
- Framework source: https://github.com/ultralytics/ultralytics

AGPL permits redistribution subject to its terms, including corresponding-source availability. Source references above are upstream access points, not a locally verified complete corresponding-source archive. The public placement site does not execute or serve this model. The owner must preserve the model licence and corresponding-source access when distributing/operating the station; the manifest does not relicense project code. Do not treat the ONNX binary alone as the complete source distribution.

## Unmodified recorded test clips

- smoke.ogv: “Wildfire Near Monserrate”, Peter Angritt (Mrtony77), CC BY-SA 4.0. https://commons.wikimedia.org/wiki/File:Wildfire_Near_Monserrate.ogv ; https://creativecommons.org/licenses/by-sa/4.0/
- cloud.webm: “Angeles National Forest from Mount Wilson”, Tom Hawkins, CC BY-SA 3.0. https://commons.wikimedia.org/wiki/File:Angeles_National_Forest_from_Mount_Wilson.webm ; https://creativecommons.org/licenses/by-sa/3.0/
- glare.webm: “072014 CostaRica Cow close up shot great lens flare”, Michael Weinman, CC BY-SA 2.0. https://commons.wikimedia.org/wiki/File:072014_CostaRica_Cow_close_up_shot_great_lens_flare.webm ; https://creativecommons.org/licenses/by-sa/2.0/

Source pages explicitly permit sharing under attribution/share-alike conditions. Originals unchanged; station capture ignores audio. Derived annotations/clips require the relevant change notices and share-alike terms. Glare footage shows a barn, not a forest-domain view.

## Excluded

fog.webm: Athulvis, uploader asserts CC BY-SA 4.0, but the Commons page retains “License review needed (video)”. Excluded conservatively pending provenance verification; not a claim that redistribution is forbidden. Source: https://commons.wikimedia.org/wiki/File:Fog_covering_mountain_time_lapse.webm . Restore does not fetch it. The station's original fetcher remains available for local demos, with its documented caveat.

Raw raster download caches, runtime event evidence, SQLite databases, local configuration and credentials are excluded. None of the reviewed licences expressly forbids redistribution; unresolved fog provenance is the only clip exclusion.
