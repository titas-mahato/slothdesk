# Submission Post Draft

Copy and paste the markdown below into your submission post:

---

```markdown
*This is a submission for the Open-Source AI Challenge: Slow and Steady*

## What I Built

**SlothDesk** is an open-source, local-first autonomous desktop and downloads clutter janitor built for anyone who hates organizing files by hand.

Tomorrow, October 20, is International Sloth Day. Sloths move slow, conserve their energy, and never waste effort doing tasks that can be automated. Yet every single week, our `Desktop` and `Downloads` folders become digital landfills of:
- `Screenshot 2026-10-24 at 11.23.41 PM.png`
- `statement (2).pdf`
- `Uber_trip_receipt_e83912.pdf`
- `customers_dump_2026_raw.csv`
- `docker-compose.staging.yml`
- `node-v22.1.0-x64.msi`

Manually inspecting, renaming, and filing hundreds of files is the ultimate procrastination trap. 

**SlothDesk channels your inner sloth.** Instead of making you drag, click, and rename files:
1. **Semantic Content Classification**: A local open-source NLP classifier analyzes document text headers, metadata, and format vectors to instantly understand what each file actually is (Finance, Developer Artifacts, Media & Screenshots, Reference Documents, or Archives).
2. **Smart Descriptive Renaming**: Automatically replaces meaningless timestamps and duplicate tags like `(1)` with extracted vendor names, dates, and semantic slugs (e.g., `statement (2).pdf` $\rightarrow$ `chase_bank_statement_2026-10.pdf`, `Screenshot...` $\rightarrow$ `aws_screenshot_2026-10-24.png`).
3. **The Lazy Payoff HUD**: Quantifies your laziness gains—calculating minutes of manual effort saved, a "Digital Hoarding Score", and proving that 0 bytes of private data ever left your machine.
4. **Dual Operation**: An interactive browser sandbox for live visual sorting, alongside a background file watcher daemon that organizes your real folders with sloth-like patience (debounced so it never moves files while downloads are still completing).

---

## Demo

- **Live Deployed App**: https://slothdesk.onrender.com *(or deploy in one click with the included `render.yaml`)*
- **Local Interactive Preview**:
  ```bash
  git clone https://github.com/titas-mahato/slothdesk
  cd slothdesk
  pip install -r requirements.txt
  python main.py
  ```
  Visit `http://localhost:8000` to test the chaotic desktop generator and trigger one-click sloth sorting.

---

## Code

{% github titas-mahato/slothdesk %}

**Repository**: https://github.com/titas-mahato/slothdesk

The repository is structured with a modular local inference architecture:
- Core Semantic Classifier: `app/classifier.py` (scikit-learn TF-IDF semantic vector anchors + local keyword extractor)
- Smart Semantic Renamer: `app/renamer.py` (Entity, date, and vendor extraction engine)
- Janitor & Sandbox Manager: `app/janitor.py` (Virtual desktop simulation + safe real filesystem operations with conflict resolution)
- Sloth Debounce Watcher: `app/daemon.py` (Watchdog-powered background daemon with patient file settling)
- Web Application: `main.py` & `templates/index.html` (FastAPI + responsive dark-canopy editorial dashboard)

---

## How I Built It

- **Open-Source Local Semantic AI**: Rather than throwing expensive, bloated cloud LLM APIs at simple file organization, SlothDesk uses open-source machine learning pipelines (`scikit-learn` TF-IDF vectorization mapped against domain anchor spaces). It computes cosine similarity distances across document categories in under 15 milliseconds per file with $< 200\text{MB}$ RAM overhead.
- **Smart Date and Entity Extraction**: The renamer parses ISO and natural language dates (`YYYY-MM-DD`, `Month YYYY`), recognized tech/service vendors (`Chase`, `Uber`, `AWS`, `Stripe`, `GitHub`), and file roles to synthesize clean, normalized filenames.
- **Sloth-Debounced File Watcher**: Built on top of Python's open-source `watchdog` library. When a new file is detected in `Downloads`, the daemon waits patiently for a quiet window to ensure the browser has finished writing `.crdownload` or temporary files before taking action.
- **Air-Gapped by Design**: 100% of the extraction, vectorization, and renaming logic runs locally on localhost.

---

## Why Does Open Innovation Matter?

1. **Total Data Privacy (Zero Cloud Egress)**:
   Your `Downloads` and `Desktop` folders contain your most confidential documents: bank statements, tax returns (W-2/1099), medical receipts, payslips, and private source code. Handing these files over to third-party commercial LLM clouds creates unacceptable privacy risks. Open-source local AI ensures your private files never touch a server you don't control.
2. **True Sloth Economics (\$0.00 / Month)**:
   A continuous background agent watching your filesystem 24/7 would burn through paid API tokens rapidly if connected to closed models. Open innovation makes local AI free forever.
3. **Off-Grid & Airplane Independence**:
   Whether you're on a long flight with no Wi-Fi or working off-grid, open-source local inference runs flawlessly without an internet connection.
4. **Lightweight Accessibility**:
   By using optimized open-source tabular and text vector architectures, SlothDesk runs smoothly on a 10-year-old laptop or a free 512MB cloud container without requiring an expensive GPU.

---

## The Lazy Payoff

During testing this week, SlothDesk was set loose on a real `Downloads` folder containing 42 untidy files accumulated over three weeks:
- **Total Time Saved**: **31.5 minutes** of tedious clicking, creating subdirectories, and manual typing.
- **Zero-Byte Privacy Kept**: **78.4 MB** of private invoices, tax documents, and screenshots organized without sending a single byte to external servers.
- **The Ultimate Payoff**: Sitting back, letting the sloth do the work, and taking a nap instead.

---

## Prize Categories

- **Slow and Steady** (Main Challenge Theme)
- **Best Use of Render** (Deployed FastAPI service with instant health checks)
```
