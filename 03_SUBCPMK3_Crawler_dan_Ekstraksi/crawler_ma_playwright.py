"""Crawler browser Direktori Putusan MA untuk PN Tanjung Redeb.

Browser ditampilkan agar pengguna dapat menyelesaikan verifikasi situs secara
manual. Program tidak menyamarkan otomasi dan tidak melewati CAPTCHA.
"""
from __future__ import annotations

import asyncio
import csv
import json
import random
import re
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

BASE_URL = "https://putusan3.mahkamahagung.go.id"
START_URL = f"{BASE_URL}/direktori.html"
CATEGORY_TEMPLATE = (
    BASE_URL
    + "/direktori/index/pengadilan/pn-tanjung-redep/"
      "kategori/narkotika-dan-psikotropika-1/tahunjenis/putus/tahun/{year}.html"
)
DETAIL_SELECTOR = "a[href*='/direktori/putusan/']"
PDF_SELECTOR = "a[href*='download_file'][href*='/pdf/'], a[href$='.pdf'], a[href*='/pdf/']"
QUOTA_DEFAULT = {2025: 16, 2024: 17, 2023: 17}
NO_RE = re.compile(r"(\d{1,5})\s*/\s*Pid\s*\.\s*Sus(?:[-.]\w+)?\s*/\s*(20\d{2})\s*/\s*PN\s*\.?\s*Tnr", re.I)

META_JS = r"""() => {
  const out = {};
  document.querySelectorAll('table tr').forEach(tr => {
    const c = tr.querySelectorAll('th,td');
    if (c.length >= 2) {
      const k = c[0].innerText.trim().replace(/\s+/g, ' ');
      const v = Array.from(c).slice(1).map(x => x.innerText.trim().replace(/\s+/g, ' ')).join(' ');
      if (k && !(k in out)) out[k] = v;
    }
  });
  document.querySelectorAll('dt').forEach(dt => {
    const dd = dt.nextElementSibling;
    const k = dt.innerText.trim();
    if (dd && dd.tagName === 'DD' && k && !(k in out))
      out[k] = dd.innerText.trim().replace(/\s+/g, ' ');
  });
  return out;
}"""


def _challenge(page) -> bool:
    try:
        text = (page.title() + " " + page.inner_text("body")[:500]).lower()
    except Exception:
        return True
    markers = ("just a moment", "verify you are human", "verifying you are human",
               "attention required", "checking your browser", "security verification")
    return any(marker in text for marker in markers)


def _wait_for_manual_verification(page, max_seconds=300) -> bool:
    if not _challenge(page):
        return True
    print("Verifikasi situs muncul. Selesaikan secara manual di browser; menunggu maksimal 5 menit...")
    started = time.time()
    stable = 0
    while time.time() - started < max_seconds:
        time.sleep(2)
        stable = 0 if _challenge(page) else stable + 1
        if stable >= 2:
            print("Verifikasi selesai.")
            return True
    print("Verifikasi tidak selesai dalam batas waktu.")
    return False


def _go(page, url) -> bool:
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    except PlaywrightTimeout:
        print("Halaman lambat, mencoba melanjutkan:", url)
    except Exception as exc:
        print("Navigasi gagal:", url, "|", str(exc).splitlines()[0])
        return False
    return _wait_for_manual_verification(page)


def _page_url(base, number):
    return base if number == 1 else base.removesuffix(".html") + f"/page/{number}.html"


def _detail_links(page, url):
    if not _go(page, url):
        return []
    try:
        page.wait_for_selector(DETAIL_SELECTOR, timeout=15_000, state="attached")
    except PlaywrightTimeout:
        pass
    time.sleep(random.uniform(2, 4))
    links = page.eval_on_selector_all(DETAIL_SELECTOR, "els => els.map(e => e.href)")
    return [x for x in dict.fromkeys(links) if "/direktori/putusan/" in x]


def _last_page(page):
    numbers = []
    for anchor in page.query_selector_all("a[href*='/page/']"):
        match = re.search(r"/page/(\d+)\.html", anchor.get_attribute("href") or "")
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers, default=1)


def _metadata(page):
    try:
        return page.evaluate(META_JS) or {}
    except Exception:
        return {}


def _status(meta, body):
    for key, value in meta.items():
        if "status" in key.lower() and value:
            return value.strip()
    match = re.search(r"(Belum\s+Berkekuatan\s+Hukum\s+Tetap|Berkekuatan\s+Hukum\s+Tetap|Inkracht[^\n]{0,40})", body, re.I)
    return match.group(1).strip() if match else "BELUM DIVERIFIKASI"


def _is_bht(status):
    value = status.lower()
    if "belum" in value and "hukum tetap" in value:
        return False
    return "berkekuatan hukum tetap" in value or "inkracht" in value


def _number(meta, body):
    match = NO_RE.search(meta.get("Nomor", "")) or NO_RE.search(body)
    return f"{match.group(1)}/Pid.Sus/{match.group(2)}/PN Tnr" if match else ""


def _safe_filename(number, fallback):
    value = number.replace("/", "_").replace(" ", "_") if number else fallback
    return "Putusan_" + re.sub(r"[^A-Za-z0-9_.-]+", "_", value) + ".pdf"


def _unique_path(folder, filename):
    target = folder / filename
    counter = 2
    while target.exists():
        target = folder / f"{Path(filename).stem}_{counter}.pdf"
        counter += 1
    return target


def _download_pdf(page, context, anchor, detail_url, target):
    href = urljoin(detail_url, anchor.get_attribute("href") or "")
    try:
        with page.expect_download(timeout=60_000) as event:
            anchor.click(timeout=10_000)
        event.value.save_as(target)
    except Exception as click_error:
        print("Klik download gagal; mencoba request dalam sesi browser:", str(click_error).splitlines()[0])
        response = context.request.get(href, timeout=90_000)
        body = response.body()
        if not response.ok or body[:4] != b"%PDF":
            raise RuntimeError(f"respons bukan PDF (HTTP {response.status})")
        target.write_bytes(body)
    if target.read_bytes()[:4] != b"%PDF":
        target.unlink(missing_ok=True)
        raise RuntimeError("file hasil bukan PDF")
    return href


def _save_log(path, rows):
    columns = ["No", "Tahun", "No Putusan", "File", "Status BHT", "URL Detail", "URL PDF", "Hasil"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _open_context(playwright, profile):
    options = dict(user_data_dir=str(profile), headless=False, accept_downloads=True, viewport=None)
    try:
        return playwright.chromium.launch_persistent_context(channel="chrome", **options)
    except Exception as exc:
        print("Chrome sistem tidak tersedia; mencoba Chromium Playwright:", str(exc).splitlines()[0])
        return playwright.chromium.launch_persistent_context(**options)


def crawl(root, quotas=None, skip_bht=True):
    root = Path(root)
    pdf_dir = root / "pdf_crawler"
    output_dir = root / "hasil_subcpmk3"
    profile = root / "browser_profile_ma"
    for folder in (pdf_dir, output_dir, profile):
        folder.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "log_crawling.csv"
    quotas = quotas or QUOTA_DEFAULT
    rows, seen = [], set()

    with sync_playwright() as playwright:
        context = _open_context(playwright, profile)
        page = context.pages[0] if context.pages else context.new_page()
        if not _go(page, START_URL):
            context.close()
            return []
        print("Titik masuk berhasil dibuka:", START_URL)

        for year, quota in quotas.items():
            base = CATEGORY_TEMPLATE.format(year=year)
            first = _detail_links(page, base)
            if not first:
                print(f"Tahun {year}: daftar putusan tidak ditemukan.")
                continue
            total_pages = _last_page(page)
            pending, page_number, downloaded = list(first), 1, 0
            print(f"Tahun {year}: {total_pages} halaman, target {quota} PDF")

            while downloaded < quota:
                if not pending:
                    page_number += 1
                    if page_number > total_pages:
                        break
                    pending = _detail_links(page, _page_url(base, page_number))
                    continue
                detail_url = pending.pop(0)
                if detail_url in seen:
                    continue
                seen.add(detail_url)
                result = {"No": len(rows) + 1, "Tahun": year, "No Putusan": "", "File": "",
                          "Status BHT": "BELUM DIVERIFIKASI", "URL Detail": detail_url,
                          "URL PDF": "", "Hasil": "GAGAL"}
                try:
                    if not _go(page, detail_url):
                        result["Hasil"] = "NAVIGASI GAGAL"; rows.append(result); _save_log(log_path, rows); continue
                    body = page.inner_text("body")
                    meta = _metadata(page)
                    lower = body.lower()
                    if not (re.search(r"(pn|pengadilan negeri)\s+tanjung\s+rede[bp]|/pn\s*tnr", lower)
                            and ("narkotika" in lower or "psikotropika" in lower)):
                        result["Hasil"] = "BUKAN TARGET"; rows.append(result); _save_log(log_path, rows); continue
                    status = _status(meta, body)
                    number = _number(meta, body)
                    result["Status BHT"], result["No Putusan"] = status, number
                    if skip_bht and _is_bht(status):
                        result["Hasil"] = "DILEWATI: BHT"; rows.append(result); _save_log(log_path, rows); continue
                    anchor = page.query_selector(PDF_SELECTOR)
                    if not anchor:
                        result["Hasil"] = "TAUTAN PDF TIDAK ADA"; rows.append(result); _save_log(log_path, rows); continue
                    filename = _safe_filename(number, f"{year}_{len(rows)+1:03d}")
                    target = pdf_dir / filename
                    if target.exists() and target.read_bytes()[:4] == b"%PDF":
                        result["File"], result["Hasil"] = target.name, "SUDAH ADA"
                    else:
                        result["URL PDF"] = _download_pdf(page, context, anchor, detail_url, target)
                        result["File"], result["Hasil"] = target.name, "TERUNDUH"
                    downloaded += 1
                    print(f"{year}: {downloaded}/{quota} | {target.name} | {status}")
                except Exception as exc:
                    result["Hasil"] = "GAGAL: " + str(exc)[:160]
                    print(result["Hasil"])
                rows.append(result)
                _save_log(log_path, rows)
                time.sleep(random.uniform(3, 5))
        context.close()
    print("Crawler selesai. PDF tersedia:", sum(row["Hasil"] in ("TERUNDUH", "SUDAH ADA") for row in rows), "| log:", log_path)
    return rows


def run_in_notebook(root, quotas=None, skip_bht=True):
    """Jalankan Playwright sync dalam thread agar kompatibel dengan Jupyter."""
    errors, result = [], []

    def target():
        try:
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            result.extend(crawl(root, quotas, skip_bht))
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()
    if errors:
        raise errors[0]
    return result

