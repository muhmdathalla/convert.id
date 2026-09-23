// Convert.id — Monochromatic Workbench Application Controller

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const inspectorEmpty = document.getElementById("inspectorEmpty");
  const inspectorData = document.getElementById("inspectorData");
  const previewContainer = document.getElementById("previewContainer");
  const propFilename = document.getElementById("propFilename");
  const propFormat = document.getElementById("propFormat");
  const propSize = document.getElementById("propSize");
  const propMagic = document.getElementById("propMagic");
  const propCategory = document.getElementById("propCategory");
  const convertBtn = document.getElementById("convertBtn");
  const queueList = document.getElementById("queueList");
  const consoleOutput = document.getElementById("consoleOutput");
  const clearConsoleBtn = document.getElementById("clearConsoleBtn");

  // Superpower toggles
  const optTargetBudget = document.getElementById("optTargetBudget");
  const optBudgetVal = document.getElementById("optBudgetVal");
  const optTrueVector = document.getElementById("optTrueVector");
  const optExifScrub = document.getElementById("optExifScrub");
  const optBgRemove = document.getElementById("optBgRemove");
  const optAutoRedact = document.getElementById("optAutoRedact");
  const optLufsNormalizer = document.getElementById("optLufsNormalizer");
  const optStripSilence = document.getElementById("optStripSilence");
  const optSpritesheet = document.getElementById("optSpritesheet");
  const optRepairMoov = document.getElementById("optRepairMoov");

  let currentFile = null;
  let selectedTargetFormat = "png";

  // Check system status
  fetchStatus();

  // Format button selector
  document.querySelectorAll(".fmt-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".fmt-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedTargetFormat = btn.getAttribute("data-fmt");
      log(`[CONFIG] Target format switched to: .${selectedTargetFormat.toUpperCase()}`, "info");
      checkConvertState();
    });
  });

  // Toggle Budget Input
  optTargetBudget.addEventListener("change", () => {
    if (optTargetBudget.checked) {
      optBudgetVal.classList.remove("hidden");
      optBudgetVal.focus();
    } else {
      optBudgetVal.classList.add("hidden");
    }
  });

  // Dropzone Events
  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("drag-active");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("drag-active");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag-active");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  function handleFileSelected(file) {
    currentFile = file;
    log(`[INPUT] File loaded: ${file.name} (${formatBytes(file.size)})`, "info");

    inspectorEmpty.classList.add("hidden");
    inspectorData.classList.remove("hidden");

    propFilename.textContent = file.name;
    propSize.textContent = formatBytes(file.size);

    const ext = file.name.split(".").pop().toLowerCase();
    propFormat.textContent = ext.toUpperCase();

    // Read first bytes for signature
    const reader = new FileReader();
    reader.onload = function(evt) {
      const arr = new Uint8Array(evt.target.result).subarray(0, 8);
      let hex = Array.from(arr).map(b => b.toString(16).padStart(2, '0').toUpperCase()).join(' ');
      propMagic.textContent = hex;
    };
    reader.readAsArrayBuffer(file.slice(0, 8));

    // Determine category and preview
    previewContainer.innerHTML = "";
    if (file.type.startsWith("image/")) {
      propCategory.textContent = "IMAGE / RASTER";
      const img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      previewContainer.appendChild(img);
    } else if (file.type.startsWith("video/")) {
      propCategory.textContent = "VIDEO / CONTAINER";
      previewContainer.innerHTML = `<span class="preview-file-icon">▶ VIDEO</span>`;
    } else if (file.type.startsWith("audio/")) {
      propCategory.textContent = "AUDIO / WAVEFORM";
      previewContainer.innerHTML = `<span class="preview-file-icon">♫ AUDIO</span>`;
    } else {
      propCategory.textContent = "DOCUMENT / DATA";
      previewContainer.innerHTML = `<span class="preview-file-icon">📄 ${ext.toUpperCase()}</span>`;
    }

    // Auto-select smart complementary output format
    autoSuggestFormat(ext);
    checkConvertState();
  }

  function autoSuggestFormat(inExt) {
    const suggestions = {
      "jfif": "png",
      "webp": "jpg",
      "heic": "jpg",
      "png": "webp",
      "jpg": "png",
      "jpeg": "png",
      "mp4": "gif",
      "mkv": "mp4",
      "avi": "mp4",
      "mov": "mp4",
      "wav": "mp3",
      "docx": "md",
      "pdf": "md",
      "json": "yaml",
      "yaml": "json",
      "csv": "sql",
      "xlsx": "csv"
    };

    const target = suggestions[inExt] || "png";
    const btn = document.querySelector(`.fmt-btn[data-fmt="${target}"]`);
    if (btn) {
      btn.click();
    }
  }

  function checkConvertState() {
    convertBtn.disabled = !currentFile || !selectedTargetFormat;
  }

  // Keyboard shortcut Ctrl+Enter / Cmd+Enter
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      if (!convertBtn.disabled) {
        convertBtn.click();
      }
    }
  });

  // Execute Conversion
  convertBtn.addEventListener("click", async () => {
    if (!currentFile) return;

    convertBtn.disabled = true;
    convertBtn.querySelector(".btn-text").textContent = "CONVERTING IN PIPELINE...";
    log(`[PIPELINE] Initiating conversion: ${currentFile.name} -> .${selectedTargetFormat.toUpperCase()}`, "info");

    const formData = new FormData();
    formData.append("file", currentFile);
    formData.append("target_format", selectedTargetFormat);

    // Parse budget if enabled
    if (optTargetBudget.checked && optBudgetVal.value) {
      const bStr = optBudgetVal.value.trim().toUpperCase();
      let bytes = 0;
      if (bStr.endsWith("MB")) bytes = parseFloat(bStr) * 1024 * 1024;
      else if (bStr.endsWith("KB")) bytes = parseFloat(bStr) * 1024;
      else bytes = parseInt(bStr) || 0;
      if (bytes > 0) {
        formData.append("target_size_bytes", bytes);
        log(`[BUDGET] Strict limit enforced: ${bytes} bytes`, "info");
      }
    }

    if (optTrueVector.checked) formData.append("vector_mode", "monochrome");
    if (optExifScrub.checked) formData.append("strip_exif", "true");
    if (optBgRemove.checked) formData.append("remove_bg", "true");
    if (optAutoRedact.checked) formData.append("auto_redact", "true");
    if (optLufsNormalizer.checked) formData.append("normalize_lufs", "true");
    if (optStripSilence.checked) formData.append("strip_silence", "true");
    if (optSpritesheet.checked) formData.append("spritesheet", "true");
    if (optRepairMoov.checked) formData.append("repair_container", "true");

    try {
      const resp = await fetch("/api/convert", {
        method: "POST",
        body: formData
      });

      const result = await resp.json();

      if (result.success) {
        log(`[SUCCESS] Output generated: ${result.filename}`, "success");
        log(`[METRICS] Delta: ${formatBytes(result.original_size)} -> ${formatBytes(result.converted_size)} (${result.compression_ratio}% reduction)`, "success");
        addQueueItem(result);
      } else {
        log(`[ERROR] Conversion failed: ${result.message}`, "error");
      }
    } catch (err) {
      log(`[EXCEPTION] Network or engine failure: ${err.message}`, "error");
    } finally {
      convertBtn.disabled = false;
      convertBtn.querySelector(".btn-text").textContent = "EXECUTE CONVERSION";
    }
  });

  function addQueueItem(item) {
    const emptyNotice = queueList.querySelector(".queue-empty");
    if (emptyNotice) emptyNotice.remove();

    const card = document.createElement("div");
    card.className = "queue-card";
    
    const deltaBadge = item.compression_ratio > 0 
      ? `<span class="queue-delta">-${item.compression_ratio}%</span>` 
      : `<span class="queue-delta">+${Math.abs(item.compression_ratio)}%</span>`;

    card.innerHTML = `
      <div class="queue-header">
        <span class="queue-fn">${item.filename}</span>
        ${deltaBadge}
      </div>
      <div class="queue-meta">
        ${formatBytes(item.converted_size)} • ${item.message || "Completed"}
      </div>
      <div class="queue-actions">
        <a href="${item.download_url}" download="${item.filename}" class="download-btn">DOWNLOAD ⤓</a>
      </div>
    `;
    queueList.prepend(card);
  }

  function log(msg, type = "info") {
    const line = document.createElement("div");
    line.className = `log-line ${type}`;
    line.textContent = msg;
    consoleOutput.appendChild(line);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
  }

  clearConsoleBtn.addEventListener("click", () => {
    consoleOutput.innerHTML = "";
  });

  async function fetchStatus() {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      if (data.dependencies && data.dependencies.ffmpeg) {
        const ff = data.dependencies.ffmpeg;
        const ffEl = document.getElementById("ffmpegStatus");
        if (ff.installed) {
          ffEl.textContent = "READY";
          ffEl.className = "status-online";
        } else {
          ffEl.textContent = "MISSING";
          ffEl.style.color = "#f87171";
        }
      }
    } catch (e) {
      // Ignore if offline
    }
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }
});
