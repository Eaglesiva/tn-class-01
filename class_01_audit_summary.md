# SCERT Class 1 (2026–27) Comprehensive Class-Wide Audit & Ingestion Report

**Execution Timestamp:** 2026-11-04T19:11:25.018454+00:00 UTC  
**Target Repository:** Eaglesiva/tn-class-01  
**Target Branch:** scert/class-01/audit-2026-27-term1-vol1  
**Live Official API URL:** `https://emis3.tnschools.gov.in/api/get_scert_books`  
**Raw API Snapshot SHA-256:** `404f283443b1f7a6a0fae814092aae556d0419ad2b4b2c0b0a0f7ebd756cc3e4`  

---

## 1. Class-Wide Metric Reconciliation Table (34 Records Complete)

| No. | Audit Verification Metric | Count | Reconciliation & Evidence Details |
|---|---|:---:|---|
| 1 | **Total Class 1 Official API Records** | **34** | Complete live API inventory across all sections: 31 academic, 1 valuation module, 2 physical education resource books. |
| 2 | **In-Scope Records (State Board Tamil & English)** | **9** | Core State Board academic books: 3 Term-I, 3 Term-II, 3 Term-III. |
| 3 | **Out-of-Scope Records** | **25** | • 1 CBSE Tamil volume (`TAMIL(CBSE)`)<br>• 21 Minority language readers & mediums (Telugu, Kannada, Malayalam, Urdu, Hindi)<br>• 1 Value education supplementary module (`1st_Std_Value_Education_Module.pdf`)<br>• 2 Physical education teacher's resource books (Tamil & English) |
| 4 | **Official URLs Successfully Downloaded & Audited** | **6** | All 6 currently released Term-I and Term-II State Board books sequentially downloaded to runner `/tmp/`, verified, and removed. |
| 5 | **Official URLs Returning HTTP 403 on GET** | **3** | Exactly 3 Term-III State Board books returned HTTP 403 Forbidden on both HEAD and GET. Confirms official Textbook Corporation distribution schedule (Term-III 2026–27 PDFs not yet released). |
| 6 | **Books Matching Existing Local Baseline** | **0** | Zero. All repository baseline folders contain legacy 2018/2022 reprint page files. |
| 7 | **Books with Confirmed New/Different Edition (2026)** | **6** | All 6 downloaded books confirmed as 2026 combined curriculum volumes with higher page counts and differing text. |
| 8 | **Books Successfully Split & Validated into 1-Page PDFs** | **6** | All 6 confirmed new edition books split into individual pages (**848 total pages**) with 100% passing structural validation (magic bytes, 1-page, renderable, size, continuity). |
| 9 | **Books Ingested into Audit Branch Editions** | **6** | Ingested under immutable paths in `official_editions/2026-27/`: <br>• `term1/vol1_tamil_english/` (176p)<br>• `term1/vol2_maths_evs_tm/` (144p)<br>• `term1/vol2_maths_evs_em/` (144p)<br>• `term2/vol1_tamil_english/` (144p)<br>• `term2/vol2_maths_evs_tm/` (120p)<br>• `term2/vol2_maths_evs_em/` (120p) |
| 10 | **Books Requiring Manual Review (TOC boundaries)** | **6** | All 6 combined volumes require unit-level manual review to map internal subject boundaries before production viewer routing. |
| 11 | **Books Awaiting Official Release (Term-III)** | **3** | All 3 Term-III State Board books. |
| 12 | **Books Not Checked** | **0** | Every single one of the 34 records was evaluated and cataloged. |

---

## 2. In-Scope Book Details & All-Pages Comparison

| Term | Subject & Volume | Medium | Official Pages | Baseline Local Pages | All-Pages Comparison Metric | Split Pages Validated | Final Status |
|---|---|---|:---:|:---:|---|:---:|---|
| **Term-I** | **VOL-I (TAMIL& ENGLISH)** | Combined (`16,19`) | **176** | 146 (81p Tam + 65p Eng) | Compared 146p: text differs; +30 extra official pages | **176 / 176** | **SPLIT_VALIDATED** |
| **Term-I** | **VOL-II (MATHS & EVS)** | Tamil (`16`) | **144** | 130 (66p Mat + 64p Sci) | Compared 130p: text differs; +14 extra official pages | **144 / 144** | **SPLIT_VALIDATED** |
| **Term-I** | **VOL-II (MATHS & EVS)** | English (`19`) | **144** | 130 (66p Mat + 64p Sci) | Compared 130p: text differs; +14 extra official pages | **144 / 144** | **SPLIT_VALIDATED** |
| **Term-II** | **VOL-I (TAMIL& ENGLISH)** | Combined (`16,19`) | **144** | 112 (64p Tam + 48p Eng) | Compared 112p: text differs; +32 extra official pages | **144 / 144** | **SPLIT_VALIDATED** |
| **Term-II** | **VOL-II (MATHS & EVS)** | Tamil (`16`) | **120** | 90 (52p Mat + 38p Sci) | Compared 90p: text differs; +30 extra official pages | **120 / 120** | **SPLIT_VALIDATED** |
| **Term-II** | **VOL-II (MATHS & EVS)** | English (`19`) | **120** | 88 (52p Mat + 36p Sci) | Compared 88p: text differs; +32 extra official pages | **120 / 120** | **SPLIT_VALIDATED** |
| **Term-III** | **VOL-I (TAMIL& ENGLISH)** | Combined (`16,19`) | — | 134 (75p Tam + 59p Eng) | GET returned HTTP 403 AccessDenied | — | **GET_HTTP_403_FORBIDDEN** |
| **Term-III** | **VOL-II (MATHS & EVS)** | Tamil (`16`) | — | 116 (68p Mat + 48p Sci) | GET returned HTTP 403 AccessDenied | — | **GET_HTTP_403_FORBIDDEN** |
| **Term-III** | **VOL-II (MATHS & EVS)** | English (`19`) | — | 116 (67p Mat + 49p Sci) | GET returned HTTP 403 AccessDenied | — | **GET_HTTP_403_FORBIDDEN** |

---

## 3. Git Safety & Production Protection
- **Main Branch:** Completely protected. Zero changes to existing production folders (`tamil/`, `english/`, `maths_tm/`, `maths_em/`, `science_tm/`, `science_em/`, `index.html`, `viewer.html`).
- **Audit Branch:** All files stored strictly under `official_editions/2026-27/` and root audit manifests on `scert/class-01/audit-2026-27-term1-vol1`.
- **Master PDFs:** Zero master PDFs committed to Git. Downloaded strictly to runner temporary `/tmp/` and removed immediately after splitting.
