#!/usr/bin/env python3
"""Fetch only the first 40 split pages from the immutable audit commit and extract Page 2/TOC text."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import requests
import fitz

REPO = "Eaglesiva/tn-class-01"
SOURCE_COMMIT = "838d5c2f335810ed95753327fe0a0b94ad298a63"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{SOURCE_COMMIT}/"
MAX_FRONT_PAGES = 40
TOC_TERMS = ["பொருளடக்கம்", "பொருளடக்க", "உள்ளடக்கம்", "contents", "table of contents"]
BOOKS = [
    ("term1-vol1-tamil-english", "official_editions/2026-27/term1/vol1_tamil_english", "Term-I · VOL-I (TAMIL & ENGLISH)"),
    ("term1-vol2-maths-evs-tm", "official_editions/2026-27/term1/vol2_maths_evs_tm", "Term-I · VOL-II (MATHS & EVS) · Tamil"),
    ("term1-vol2-maths-evs-em", "official_editions/2026-27/term1/vol2_maths_evs_em", "Term-I · VOL-II (MATHS & EVS) · English"),
    ("term2-vol1-tamil-english", "official_editions/2026-27/term2/vol1_tamil_english", "Term-II · VOL-I (TAMIL & ENGLISH)"),
    ("term2-vol2-maths-evs-tm", "official_editions/2026-27/term2/vol2_maths_evs_tm", "Term-II · VOL-II (MATHS & EVS) · Tamil"),
    ("term2-vol2-maths-evs-em", "official_editions/2026-27/term2/vol2_maths_evs_em", "Term-II · VOL-II (MATHS & EVS) · English"),
]

def get_bytes(url):
    response = requests.get(url, timeout=(15, 90))
    response.raise_for_status()
    return response.content

def get_json(url):
    return json.loads(get_bytes(url).decode("utf-8"))

def pdf_text(data, render=False):
    with fitz.open(stream=data, filetype="pdf") as doc:
        if len(doc) == 0:
            return "", 0, None
        text = (doc[0].get_text("text") or "").strip()
        image_png = None
        if render:
            image_png = doc[0].get_pixmap(dpi=120, alpha=False).tobytes("png")
        return text, len(doc), image_png

def download_page(job):
    book_slug, rel_dir, page_number, rel_page = job
    url = RAW_BASE + rel_dir + "/" + rel_page
    data = get_bytes(url)
    render = page_number == 2 or (book_slug.startswith("term2-") and page_number <= 20)
    text, pdf_page_count, image_png = pdf_text(data, render=render)
    return {
        "book_slug": book_slug,
        "book_page": page_number,
        "path": rel_dir + "/" + rel_page,
        "text": text,
        "pdf_page_count": pdf_page_count,
        "byte_count": len(data),
        "url": url,
        "image_png": image_png,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    text_dir = output / "extracted-text"
    text_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Class01-MicroEditionTextAudit/1.0"})

    jobs = []
    book_meta = {}
    for slug, rel_dir, label in BOOKS:
        edition = get_json(RAW_BASE + rel_dir + "/edition.json")
        page_list = get_json(RAW_BASE + rel_dir + "/pages.json")
        page2_rel = next((p for p in page_list if Path(p).name == "page-002.pdf"), None)
        if not page2_rel:
            raise RuntimeError(f"page-002.pdf is absent from pages.json for {label}")
        book_meta[slug] = {
            "slug": slug, "path": rel_dir, "label": label,
            "edition": edition, "page_list": page_list,
            "page2_rel": page2_rel,
        }
        for number, rel_page in enumerate(page_list[:MAX_FRONT_PAGES], start=1):
            jobs.append((slug, rel_dir, number, rel_page))

    page_results = []
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {pool.submit(download_page, job): job for job in jobs}
        for future in concurrent.futures.as_completed(future_map):
            job = future_map[future]
            try:
                page_results.append(future.result())
            except Exception as exc:
                errors.append({
                    "book_slug": job[0], "book_page": job[2],
                    "path": job[1] + "/" + job[3], "error": str(exc)
                })

    page_results.sort(key=lambda x: (x["book_slug"], x["book_page"]))
    rendered_dir = output / "rendered-pages"
    rendered_count = 0
    for page in page_results:
        if page.get("image_png"):
            book_render_dir = rendered_dir / page["book_slug"]
            book_render_dir.mkdir(parents=True, exist_ok=True)
            image_path = book_render_dir / f"page-{page['book_page']:03d}.png"
            image_path.write_bytes(page["image_png"])
            page["rendered_image_path"] = str(image_path.relative_to(output))
            page["image_png"] = None
            rendered_count += 1
    results = []
    md = [
        "# Class 01 — Page 2 and TOC Text Extraction",
        "",
        f"**Immutable source commit:** {SOURCE_COMMIT}",
        f"**Method:** Downloaded only the first {MAX_FRONT_PAGES} existing split pages per book from GitHub and extracted text with PyMuPDF.",
        "**Scope:** Read-only. No PDFs were generated or rewritten; no production branch or source audit branch was changed.",
        "",
        "The Page 2 PDF already exists in each book's pages directory. This run validates and extracts that existing file; it does not create a duplicate.",
        "",
    ]

    for slug, rel_dir, label in BOOKS:
        meta = book_meta[slug]
        pages = [p for p in page_results if p["book_slug"] == slug]
        page2 = next((p for p in pages if p["path"] == rel_dir + "/" + meta["page2_rel"]), None)
        if page2 is None:
            page2_error = next((e for e in errors if e["book_slug"] == slug and e["book_page"] == 2), None)
            raise RuntimeError(f"Unable to extract Page 2 for {label}: {page2_error}")
        candidates = []
        for p in pages:
            lowered = p["text"].casefold()
            hits = [term for term in TOC_TERMS if term.casefold() in lowered]
            if hits:
                candidates.append({
                    "book_page": p["book_page"],
                    "path": p["path"],
                    "matched_terms": hits,
                    "text": p["text"],
                    "url": p["url"],
                })
        status = "KEYWORD_CANDIDATES_FOUND" if candidates else f"NO_KEYWORD_MATCH_IN_FIRST_{MAX_FRONT_PAGES}_PAGES"

        txt = [
            "# " + label,
            "",
            "Book folder: " + rel_dir,
            "Page 2 PDF: " + page2["path"],
            "",
            "## Extracted Page 2 text",
            page2["text"] or "[NO SELECTABLE TEXT — visual review required]",
            "",
            "## TOC keyword candidates",
        ]
        if candidates:
            for c in candidates:
                txt.extend([
                    "",
                    f"### Printed PDF page {c['book_page']} — {', '.join(c['matched_terms'])}",
                    c["text"] or "[NO SELECTABLE TEXT]",
                    "Source: " + c["url"],
                ])
        else:
            txt.extend(["", "[No explicit TOC keyword detected in the first 40 pages.]"])
        txt.extend(["", "## First 40 page text"])
        for p in pages:
            txt.extend([
                "",
                f"### Printed PDF page {p['book_page']}",
                p["text"] or "[NO SELECTABLE TEXT]",
            ])
        text_path = text_dir / f"{slug}.txt"
        text_path.write_text("\n".join(txt) + "\n", encoding="utf-8")

        result = {
            "slug": slug, "label": label, "book_path": rel_dir,
            "manifest_total_pages": len(meta["page_list"]),
            "page2_path": page2["path"],
            "page2_url": page2["url"],
            "page2_is_single_page_pdf": page2["pdf_page_count"] == 1,
            "page2_rendered_image": page2.get("rendered_image_path"),
            "page2_text_status": "EXTRACTED" if page2["text"] else "IMAGE_ONLY_OR_NO_TEXT",
            "page2_text": page2["text"],
            "toc_status": status,
            "toc_candidates": candidates,
            "front_pages_downloaded": len(pages),
            "download_errors": [e for e in errors if e["book_slug"] == slug],
            "edition_json": meta["edition"],
            "extracted_text_file": str(text_path.relative_to(output)),
        }
        results.append(result)
        md.extend([
            f"## {label}",
            "",
            f"- PDF folder: {rel_dir}",
            f"- Total book pages from manifest: **{len(meta['page_list'])}**",
            f"- Page 2 PDF: [{page2['path']}]({page2['url']})",
            f"- Page 2 is a one-page PDF: **{page2['pdf_page_count'] == 1}**",
            f"- Page 2 rendered image: {page2.get('rendered_image_path', 'not rendered')}",
            f"- Page 2 extraction status: **{result['page2_text_status']}**",
            f"- Existing edition.json imprint field: {meta['edition'].get('printed_imprint', 'UNKNOWN')}",
            f"- TOC status: **{status}**",
            f"- TOC candidate PDF pages: {', '.join(str(c['book_page']) for c in candidates) if candidates else 'Not found in first 40 pages'}",
            f"- Extracted text file: {result['extracted_text_file']}",
            "",
            "### Page 2 extracted text",
            "",
            page2["text"] or "[NO SELECTABLE TEXT — visual review required]",
            "",
            "### TOC candidate text",
            "",
        ])
        if candidates:
            for c in candidates:
                md.extend([
                    f"**Printed PDF page {c['book_page']}** — " + ", ".join(c["matched_terms"]),
                    "",
                    c["text"] or "[NO SELECTABLE TEXT]",
                    "",
                ])
        else:
            md.extend(["No explicit TOC keyword was detected in the first 40 pages. Review companion TXT before marking TOC.", ""])

    report_json = output / "class_01_page2_toc_extraction.json"
    report_md = output / "class_01_page2_toc_extraction.md"
    report_json.write_text(json.dumps({"books": results, "download_errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("BOOKS_PROCESSED=" + str(len(results)))
    print("PAGE2_SINGLE_PAGE_FILES=" + str(sum(1 for x in results if x["page2_is_single_page_pdf"])))
    print("TOTAL_PAGES_IN_BOOKS=" + str(sum(x["manifest_total_pages"] for x in results)))
    print("FRONT_PAGE_PDFS_DOWNLOADED=" + str(len(page_results)))
    print("DOWNLOAD_ERRORS=" + str(len(errors)))
    print("RENDERED_PNG_FILES=" + str(rendered_count))
    for item in results:
        print("\n### " + item["label"])
        print("Page 2 status: " + item["page2_text_status"])
        print("Page 2 text:\n" + (item["page2_text"] or "[NO SELECTABLE TEXT]"))
        print("TOC status: " + item["toc_status"])
        for candidate in item["toc_candidates"]:
            print(f"TOC CANDIDATE PAGE {candidate['book_page']}:\n{candidate['text']}")
    print("REPORT_MD=" + str(report_md))
    print("REPORT_JSON=" + str(report_json))

if __name__ == "__main__":
    main()
