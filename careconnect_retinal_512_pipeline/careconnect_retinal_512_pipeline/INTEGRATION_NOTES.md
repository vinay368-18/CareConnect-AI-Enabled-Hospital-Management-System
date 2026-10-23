# Integration notes

Existing documented components include `cvd-ai-service/vessel_segmentation.py`, `api_server.py`, Java `CVDClient.java`, `CVDServlet.java`, and `cvd-report.jsp`.

Before replacing anything:
1. Back up original files and `models/residual_unet_best.pt`.
2. Inspect exact model input channels, normalization, output activation, checkpoint keys, and training patch size.
3. Add the 512x512 green CLAHE preprocessing to the segmentation branch only.
4. Keep classifier preprocessing at 224x224 unless separately retrained and evaluated.
5. Update API serialization and JSP only after Python output is visually verified.
6. Run existing tests and test one real fundus image end-to-end.

The actual source project and trained checkpoint were not supplied with this package, so drop-in compatibility cannot be guaranteed from documentation alone.
