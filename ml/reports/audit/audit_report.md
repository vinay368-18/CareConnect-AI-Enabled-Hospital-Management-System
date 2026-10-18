# CareConnect Dataset Audit Report

**Generated:** 2026-10-18 12:21:35
**Audit Script:** `ml/src/dataset_audit.py`

## Executive Summary

| Dataset | Images | Patients | CVD Label | Usable for CVD? |
|:--|:--:|:--:|:--:|:--:|
| mBRSET | 4002 | 1289 |   vascular_disease |   Yes |
| BRSET | 187 | ? (no labels) |   None |   No |
| ODIR-5K | 6392 | 3358 |   None |   No (ocular only) |

## 1. mBRSET (Primary Dataset)

- **Metadata CSV rows:** 5164
- **Images on disk:** 4002
- **Matched (CSV <-> disk):** 4002
- **Missing from disk:** 1162
- **Corrupted images:** 0
- **Total patients in CSV:** 1291
- **Patients with >=1 image:** 1289

### Vascular Disease (Patient-Level)
| Value | Count |
|:--:|:--:|
| 0.0 | 1055 |
| 1.0 | 217 |
| nan | 19 |

### Systemic Hypertension (Patient-Level)
| Value | Count |
|:--:|:--:|
| 0.0 | 366 |
| 1.0 | 914 |
| nan | 11 |

### Diabetic Retinopathy ICDR Grade (Image-Level)
| Grade | Count |
|:--:|:--:|
| 0.0 | 3750 |
| 1.0 | 272 |
| 2.0 | 568 |
| 3.0 | 82 |
| 4.0 | 212 |
| nan | 280 |

**Inconsistent vascular_disease across images of same patient:** 0

## 2. BRSET (Incomplete Download)

- **Images found:** 187
- **CSV files found:** 0
- **Complete download:** False
- **Usable for CVD:** False
- **Reason:** Only 187 images from a partial download shard. No label CSV(s) found within the extracted data.

## 3. ODIR-5K

- **Images on disk:** 6392
- **Metadata rows:** 6392
- **Total patients:** 3358

### CVD Label Compatibility
- **Has CVD label:** False
- **Has vascular_disease:** False
- **Assessment:** ODIR-5K contains ocular disease labels (N, D, G, C, A, H, M, O). The 'H' column indicates hypertensive retinopathy (an ocular finding), NOT systemic cardiovascular disease history. The 'D' column indicates diabetic retinopathy, NOT a diabetes diagnosis. There is NO cardiovascular disease (CVD) or vascular_disease label in ODIR-5K. Direct label mapping to mBRSET's vascular_disease target is NOT scientifically valid.

## 4. Cross-Dataset Overlap

| Comparison | Filename Overlap |
|:--|:--:|
| mbrset_vs_odir | 0 |
| mbrset_vs_brset | 0 |
| odir_vs_brset | 0 |

mBRSET and ODIR-5K use independent patient ID namespaces (different institutions, countries, and study designs). Numeric overlap of IDs is coincidental and does NOT indicate that the same physical patients appear in both datasets. Cross-dataset patient leakage is not a concern.

## 5. Recommendations

1. **Primary training dataset:** mBRSET with `vascular_disease` as the CVD target
2. **BRSET:** Cannot be used -- incomplete download with no labels
3. **ODIR-5K:** Cannot provide CVD labels -- only suitable for:
   - Retinal image pretraining (self-supervised or ImageNet-style)
   - Separate ocular disease classification task
   - Multi-task learning with separate ODIR-specific heads
4. **Missing mBRSET images:** 1,162 metadata rows lack corresponding images -- exclude from training but document the exclusion
5. **Investigate baseline metrics:** CVD AUC 0.56 and HT AUC 0.46 suggest potential label errors, preprocessing bugs, or fundamental signal weakness