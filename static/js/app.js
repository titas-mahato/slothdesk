/**
 * SlothDesk: Client-side application logic.
 * Handles desktop sandbox simulations, real-time AI tidying animations,
 * file inspector modals, and drag-and-drop file analysis.
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentFiles = [];
  let drawersMetadata = {};
  let lastPlan = null;

  // DOM Elements
  const desktopContainer = document.getElementById("desktopFilesContainer");
  const drawersContainer = document.getElementById("drawersContainer");
  const chaoticCount = document.getElementById("chaoticCount");
  const desktopStatus = document.getElementById("desktopStatus");
  const drawersStatus = document.getElementById("drawersStatus");

  // HUD
  const hudLaziness = document.getElementById("hudLaziness");
  const hudTimeSaved = document.getElementById("hudTimeSaved");
  const hudEgress = document.getElementById("hudEgress");
  const hudHoarding = document.getElementById("hudHoarding");

  // Buttons
  const btnMessify = document.getElementById("btnMessify");
  const btnTidy = document.getElementById("btnTidy");
  const btnOpenUpload = document.getElementById("btnOpenUpload");
  const uploadDropzone = document.getElementById("uploadDropzone");
  const realFileInput = document.getElementById("realFileInput");
  const mascotBadge = document.getElementById("mascotBadge");

  // Modals
  const localModal = document.getElementById("localModal");
  const btnOpenLocalModal = document.getElementById("btnOpenLocalModal");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const btnCancelScan = document.getElementById("btnCancelScan");
  const btnExecuteScan = document.getElementById("btnExecuteScan");
  const localFolderPath = document.getElementById("localFolderPath");
  const chkDryRun = document.getElementById("chkDryRun");
  const localScanResult = document.getElementById("localScanResult");

  // Inspector Modal
  const inspectorModal = document.getElementById("inspectorModal");
  const btnCloseInspector = document.getElementById("btnCloseInspector");
  const inspectOrigName = document.getElementById("inspectOrigName");
  const inspectProposedName = document.getElementById("inspectProposedName");
  const inspectDrawerBadge = document.getElementById("inspectDrawerBadge");
  const inspectConfidence = document.getElementById("inspectConfidence");
  const inspectReason = document.getElementById("inspectReason");
  const inspectTokens = document.getElementById("inspectTokens");

  // Initialize
  async function init() {
    try {
      const [drawersRes, filesRes] = await Promise.all([
        fetch("/api/drawers"),
        fetch("/api/sandbox/default"),
      ]);

      drawersMetadata = await drawersRes.json();
      currentFiles = await filesRes.json();

      renderDesktopFiles(currentFiles);
      renderEmptyDrawers();
      updateIcons();
    } catch (err) {
      console.error("Initialization failed:", err);
    }
  }

  function updateIcons() {
    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  function getFileIcon(ext) {
    const icons = {
      pdf: "file-text",
      png: "image",
      jpg: "image",
      jpeg: "image",
      docx: "file-type",
      csv: "table",
      yml: "code",
      yaml: "code",
      py: "terminal",
      msi: "package",
      zip: "archive",
    };
    return icons[ext] || "file";
  }

  // Render chaotic desktop grid
  function renderDesktopFiles(files) {
    desktopContainer.innerHTML = "";
    chaoticCount.textContent = `${files.length} items`;
    desktopStatus.textContent = "Needs Cleaning";
    desktopStatus.className = "panel-status-tag";

    if (files.length === 0) {
      desktopContainer.innerHTML = `<div class="drawer-empty">✨ Desktop is spotless! Total sloth bliss.</div>`;
      return;
    }

    files.forEach((file) => {
      const pill = document.createElement("div");
      pill.className = "file-pill";
      pill.dataset.fileId = file.id;

      const iconName = getFileIcon(file.extension);

      pill.innerHTML = `
        <div class="file-pill-icon"><i data-lucide="${iconName}"></i></div>
        <div class="file-pill-info">
          <span class="file-pill-name" title="${file.original_name}">${file.original_name}</span>
          <div class="file-pill-meta">
            <span>.${file.extension.toUpperCase()}</span>
            <span>&bull;</span>
            <span>${formatBytes(file.size_bytes)}</span>
          </div>
        </div>
      `;

      pill.addEventListener("click", () => inspectRawFile(file));
      desktopContainer.appendChild(pill);
    });

    updateIcons();
  }

  // Render empty smart drawers
  function renderEmptyDrawers() {
    drawersContainer.innerHTML = "";
    drawersStatus.classList.add("hidden");

    Object.values(drawersMetadata).forEach((meta) => {
      const card = document.createElement("div");
      card.className = "drawer-card";
      card.id = `drawer-${meta.key.replace(/[^a-zA-Z0-9]/g, "_")}`;

      card.innerHTML = `
        <div class="drawer-header">
          <div class="drawer-title-row">
            <span class="drawer-dot" style="background-color: ${meta.color_hex};"></span>
            <strong>${meta.key}</strong>
          </div>
          <span class="drawer-badge" id="count-${meta.key.replace(/[^a-zA-Z0-9]/g, "_")}">0 items</span>
        </div>
        <div class="drawer-body" id="body-${meta.key.replace(/[^a-zA-Z0-9]/g, "_")}">
          <div class="drawer-empty">${meta.description}</div>
        </div>
      `;
      drawersContainer.appendChild(card);
    });
    updateIcons();
  }

  // Messify (Generate Chaotic Files)
  btnMessify.addEventListener("click", async () => {
    btnMessify.disabled = true;
    btnMessify.innerHTML = `<i data-lucide="loader"></i> Messifying...`;
    updateIcons();

    try {
      const res = await fetch("/api/sandbox/messify", { method: "POST" });
      currentFiles = await res.json();
      renderDesktopFiles(currentFiles);
      renderEmptyDrawers();

      // Reset HUD
      hudLaziness.textContent = "--%";
      hudTimeSaved.textContent = "-- min";
      hudEgress.textContent = "0 MB";
      hudHoarding.textContent = "Procrastination Monarch";
    } catch (e) {
      console.error(e);
    } finally {
      btnMessify.disabled = false;
      btnMessify.innerHTML = `<i data-lucide="shuffle"></i> Generate Cluttered Desktop`;
      updateIcons();
    }
  });

  // Tidy (One-Click Clean)
  btnTidy.addEventListener("click", async () => {
    if (currentFiles.length === 0) return;

    btnTidy.disabled = true;
    btnTidy.innerHTML = `<i data-lucide="loader"></i> Sloth Sorting...`;
    updateIcons();

    // Trigger visual moving animation on desktop pills
    const pills = document.querySelectorAll(".file-pill");
    pills.forEach((p) => p.classList.add("tidy-moving"));

    try {
      const res = await fetch("/api/sandbox/tidy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files: currentFiles }),
      });
      lastPlan = await res.json();

      setTimeout(() => {
        populateDrawersWithPlan(lastPlan);
        updateHUD(lastPlan.metrics);

        desktopStatus.textContent = "Cleaned by Sloth";
        desktopStatus.className = "panel-status-tag success";
        drawersStatus.classList.remove("hidden");

        desktopContainer.innerHTML = `
          <div style="grid-column: 1 / -1; padding: 40px 20px; text-align: center; color: var(--text-muted);">
            <div style="font-size: 40px; margin-bottom: 8px;">🦥</div>
            <strong style="color: #ffffff; font-size: 15px;">Zero Desktop Clutter Remaining</strong>
            <p style="font-size: 12px; margin-top: 4px;">All files analyzed, normalized, and filed into the drawers on the right.</p>
          </div>
        `;
        chaoticCount.textContent = "0 items";

        btnTidy.disabled = false;
        btnTidy.innerHTML = `<i data-lucide="sparkles"></i> Channel Inner Sloth (One-Click Clean)`;
        updateIcons();
      }, 500);
    } catch (e) {
      console.error(e);
      btnTidy.disabled = false;
      btnTidy.innerHTML = `<i data-lucide="sparkles"></i> Channel Inner Sloth (One-Click Clean)`;
      updateIcons();
    }
  });

  // Populate Drawers with the AI Organization Plan
  function populateDrawersWithPlan(plan) {
    Object.entries(plan.drawers).forEach(([drawerKey, items]) => {
      const safeKey = drawerKey.replace(/[^a-zA-Z0-9]/g, "_");
      const body = document.getElementById(`body-${safeKey}`);
      const countBadge = document.getElementById(`count-${safeKey}`);

      if (!body) return;

      countBadge.textContent = `${items.length} items`;

      if (items.length === 0) {
        body.innerHTML = `<div class="drawer-empty">No items assigned to this drawer.</div>`;
        return;
      }

      body.innerHTML = "";
      items.forEach((item) => {
        const itemEl = document.createElement("div");
        itemEl.className = "drawer-item";
        itemEl.innerHTML = `
          <div class="drawer-item-names">
            <span class="proposed-name" title="${item.proposed_name}">${item.proposed_name}</span>
            <span class="orig-name-strikethrough" title="Original: ${item.original_name}">${item.original_name}</span>
          </div>
          <span class="item-score-badge">${Math.round(item.confidence * 100)}% match</span>
        `;
        itemEl.addEventListener("click", () => openInspector(item));
        body.appendChild(itemEl);
      });
    });
    updateIcons();
  }

  // Update HUD
  function updateHUD(metrics) {
    hudLaziness.textContent = `${metrics.laziness_score}%`;
    hudTimeSaved.textContent = `${metrics.manual_minutes_saved} min`;
    hudEgress.textContent = formatBytes(metrics.cloud_egress_bytes_prevented);
    hudHoarding.textContent = metrics.hoarding_status;
  }

  // Open Inspector
  function openInspector(item) {
    inspectOrigName.textContent = item.original_name;
    inspectProposedName.textContent = item.proposed_name;
    inspectDrawerBadge.textContent = item.target_drawer;
    inspectDrawerBadge.style.backgroundColor = item.drawer_metadata?.color_hex || "#3b82f6";
    inspectConfidence.textContent = `${Math.round(item.confidence * 100)}% Local Confidence`;
    inspectReason.textContent = item.reason;

    inspectTokens.innerHTML = "";
    if (item.detected_tags && item.detected_tags.length > 0) {
      item.detected_tags.forEach((tag) => {
        const span = document.createElement("span");
        span.className = "tag-badge";
        span.textContent = `#${tag}`;
        inspectTokens.appendChild(span);
      });
    } else {
      inspectTokens.innerHTML = `<span style="color: var(--text-muted); font-size: 11px;">None detected</span>`;
    }

    inspectorModal.classList.remove("hidden");
  }

  function inspectRawFile(file) {
    // If user clicks a raw file before tidying, run single classification
    fetch("/api/sandbox/tidy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ files: [file] }),
    })
      .then((r) => r.json())
      .then((plan) => {
        if (plan.items && plan.items.length > 0) {
          openInspector(plan.items[0]);
        }
      });
  }

  // Close Modals
  btnCloseInspector.addEventListener("click", () => inspectorModal.classList.add("hidden"));
  inspectorModal.addEventListener("click", (e) => {
    if (e.target === inspectorModal) inspectorModal.classList.add("hidden");
  });

  // Dropzone Toggling & Real File Upload
  btnOpenUpload.addEventListener("click", () => {
    uploadDropzone.classList.toggle("hidden");
  });

  uploadDropzone.addEventListener("click", () => realFileInput.click());

  uploadDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadDropzone.classList.add("dragover");
  });

  uploadDropzone.addEventListener("dragleave", () => {
    uploadDropzone.classList.remove("dragover");
  });

  uploadDropzone.addEventListener("drop", async (e) => {
    e.preventDefault();
    uploadDropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  realFileInput.addEventListener("change", async () => {
    if (realFileInput.files && realFileInput.files.length > 0) {
      await handleFileUpload(realFileInput.files[0]);
    }
  });

  async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload-analyze", {
        method: "POST",
        body: formData,
      });
      const classified = await res.json();
      openInspector(classified);
    } catch (err) {
      alert("Error analyzing file locally: " + err);
    }
  }

  // Local Folder Scan Modal
  btnOpenLocalModal.addEventListener("click", () => {
    localModal.classList.remove("hidden");
  });

  btnCloseModal.addEventListener("click", () => localModal.classList.add("hidden"));
  btnCancelScan.addEventListener("click", () => localModal.classList.add("hidden"));

  btnExecuteScan.addEventListener("click", async () => {
    const path = localFolderPath.value.trim();
    if (!path) {
      alert("Please enter a valid directory path.");
      return;
    }

    btnExecuteScan.disabled = true;
    btnExecuteScan.innerHTML = `<i data-lucide="loader"></i> Scanning...`;
    localScanResult.classList.remove("hidden");
    localScanResult.textContent = "Scanning directory and evaluating local semantic models...";
    updateIcons();

    try {
      const res = await fetch("/api/local/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: path,
          dry_run: chkDryRun.checked,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Scan failed");
      }

      localScanResult.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      localScanResult.textContent = `Error: ${err.message}`;
    } finally {
      btnExecuteScan.disabled = false;
      btnExecuteScan.innerHTML = `<i data-lucide="play"></i> Run Local Janitor`;
      updateIcons();
    }
  });

  // Mascot Easter Egg
  const slothQuotes = [
    "Sloths don't organize by hand. Sloths let open-source AI do it.",
    "Conserve energy. Your downloads will still be there tomorrow.",
    "100% offline. 0% stress.",
    "Why drag and drop when python can move it while you sleep?",
    "Happy International Sloth Day! Now go take a nap.",
  ];

  mascotBadge.addEventListener("click", () => {
    const quote = slothQuotes[Math.floor(Math.random() * slothQuotes.length)];
    alert(`🦥 Sloth Wisdom:\n\n"${quote}"`);
  });

  // Run
  init();
});
