# SCERT Class 1 (2026–27) Class-Wide Audit & Edition Report

**Date of Execution:** 2026-11-04T00:16:55.595628+00:00 UTC  
**Repository:** Eaglesiva/tn-class-01  
**Branch:** scert/class-01/audit-2026-27-term1-vol1  
**Live SCERT API URL:** `https://emis3.tnschools.gov.in/api/get_scert_books`  
**Snapshot SHA-256:** `404f283443b1f7a6a0fae814092aae556d0419ad2b4b2c0b0a0f7ebd756cc3e4`  

---

## 1. Class-Level Reconciliation Summary

| Metric | Count | Details |
|---|---|---|
| **Total Class 1 Official API Records** | **31** | Exact count from live EMIS API |
| **In-Scope Records (State Board Tamil & English)** | **9** | 3 Term-I, 3 Term-II, 3 Term-III |
| **Out-of-Scope Records** | **22** | 1 CBSE Tamil + 21 Minority language readers/mediums |
| **Official URLs Successfully Downloaded & Audited** | **6** | All 6 available Term-I & Term-II State Board books |
| **Official URLs Unavailable (HTTP 403)** | **3** | Exactly 3 Term-III books (Distribution pending) |
| **Books Matching Existing Local Baseline** | **0** | All existing repository books are legacy 2018/2022 editions |
| **Books with Confirmed New Edition (2026)** | **6** | All 6 downloaded books confirmed as 2026 curriculum editions |
| **Books Successfully Split into 1-Page PDFs** | **1** | Class 1 Term 1 Vol 1 (176/176 pages validated) |
| **Books Committed to Audit Branch** | **1** | `official_editions/2026-27/term1/vol1_tamil_english/` |
| **Books Requiring Manual Review** | **1** | Term 1 Vol 1 TOC subject boundary (TOC_STATUS: MANUAL_REVIEW_REQUIRED) |
| **Books Awaiting Official Release (Term-III)** | **3** | Not yet available on SCERT CDN |
| **Production Files Modified on main** | **0** | `main` branch completely untouched |

---

## 2. In-Scope Book Details

| Term | Subject | Medium | Official Pages | Local Pages | Official Imprint | Status |
|---|---|---|---|---|---|---|
| **Term-I** | VOL-I (TAMIL& ENGLISH) | Tamil & English | 176 | 146 (81p Tam + 65p Eng) | First Edition 2026 | **SPLIT_VALIDATED** |
| **Term-I** | VOL-II (MATHS & EVS) | Tamil Medium | 144 | 130 (66p Mat + 64p Sci) | First Edition 2026 | **NEW_EDITION_CONFIRMED** |
| **Term-I** | VOL-II (MATHS & EVS) | English Medium | 144 | 130 (66p Mat + 64p Sci) | First Edition 2026 | **NEW_EDITION_CONFIRMED** |
| **Term-II** | VOL-I (TAMIL& ENGLISH) | Tamil & English | 144 | 112 (64p Tam + 48p Eng) | 2026 Curriculum Combined | **NEW_EDITION_CONFIRMED** |
| **Term-II** | VOL-II (MATHS & EVS) | Tamil Medium | 120 | 90 (52p Mat + 38p Sci) | 2026 Curriculum Combined | **NEW_EDITION_CONFIRMED** |
| **Term-II** | VOL-II (MATHS & EVS) | English Medium | 120 | 88 (52p Mat + 36p Sci) | 2026 Curriculum Combined | **NEW_EDITION_CONFIRMED** |
| **Term-III** | VOL-I (TAMIL& ENGLISH) | Tamil & English | - | 134 (75p Tam + 59p Eng) | HTTP 403 Forbidden | **URL_NOT_AVAILABLE** |
| **Term-III** | VOL-II (MATHS & EVS) | Tamil Medium | - | 116 (68p Mat + 48p Sci) | HTTP 403 Forbidden | **URL_NOT_AVAILABLE** |
| **Term-III** | VOL-II (MATHS & EVS) | English Medium | - | 116 (67p Mat + 49p Sci) | HTTP 403 Forbidden | **URL_NOT_AVAILABLE** |

---

## 3. Git Safety & Branch State
- Master PDFs downloaded to runner `/tmp/` only, inspected, split (for Term-I Vol-I), and deleted immediately.
- 0 master PDFs committed.
- Zero changes to existing production folders (`tamil/`, `english/`, `maths_tm/`, `maths_em/`, `science_tm/`, `science_em/`, `index.html`, `viewer.html`).
- All new files staged strictly under:
  - `class_01_2026_27_audit_manifest.csv`
  - `class_01_official_api_snapshot.json`
  - `class_01_audit_summary.md`
  - `audit_artifacts/`
  - `official_editions/2026-27/term1/vol1_tamil_english/`
