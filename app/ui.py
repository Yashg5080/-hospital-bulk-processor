UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Paribus Hospital Bulk Processing System</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; }
    code, pre { font-family: 'JetBrains Mono', monospace; }
  </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen">
  <header class="border-b border-slate-800 bg-slate-950/70 backdrop-blur sticky top-0 z-50">
    <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-lg">
          +
        </div>
        <div>
          <h1 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            Paribus Hospital Bulk Processor
            <span class="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">v1.0.0</span>
          </h1>
          <p class="text-xs text-slate-400">High-Performance Asynchronous Bulk Processing Microservice</p>
        </div>
      </div>
      <div class="flex items-center space-x-4 text-sm">
        <a href="/docs" target="_blank" class="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 transition text-xs font-medium flex items-center gap-1.5 border border-slate-700">
          <span>Swagger UI</span>
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
        </a>
        <a href="https://hospital-directory.onrender.com/docs" target="_blank" class="px-3 py-1.5 rounded-md bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 transition text-xs font-medium flex items-center gap-1.5 border border-emerald-800/40">
          <span>Upstream API Docs</span>
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
        </a>
      </div>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-6 py-8 space-y-8">
    <!-- Architecture Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
        <div class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Max Batch Size</div>
        <div class="text-2xl font-bold text-white mt-1">20 Records</div>
        <div class="text-xs text-slate-500 mt-1">Strict CSV size validation</div>
      </div>
      <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
        <div class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Concurrency</div>
        <div class="text-2xl font-bold text-emerald-400 mt-1">10 Workers</div>
        <div class="text-xs text-slate-500 mt-1">Bounded asyncio semaphore</div>
      </div>
      <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
        <div class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Fault Tolerance</div>
        <div class="text-2xl font-bold text-cyan-400 mt-1">3x Retry + Jitter</div>
        <div class="text-xs text-slate-500 mt-1">Exponential backoff on 5xx</div>
      </div>
      <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
        <div class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Recovery</div>
        <div class="text-2xl font-bold text-amber-400 mt-1">Resumable</div>
        <div class="text-xs text-slate-500 mt-1">Idempotent batch retry</div>
      </div>
    </div>

    <!-- Main Upload & Control Section -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <div class="lg:col-span-5 space-y-6">
        <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-5">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-white">Upload Hospitals CSV</h2>
            <button id="useSampleBtn" class="text-xs text-emerald-400 hover:text-emerald-300 font-medium underline">
              Use Sample CSV
            </button>
          </div>

          <!-- Drag and drop zone -->
          <div id="dropzone" class="border-2 border-dashed border-slate-700 hover:border-emerald-500/60 rounded-xl p-6 text-center cursor-pointer transition bg-slate-900/50">
            <input type="file" id="fileInput" accept=".csv" class="hidden" />
            <div class="flex flex-col items-center justify-center space-y-2">
              <div class="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
              </div>
              <p class="text-sm font-medium text-slate-200" id="fileName">Drop your CSV file here or click to browse</p>
              <p class="text-xs text-slate-500">Expected columns: <code class="text-slate-400">name, address, phone</code> (phone is optional)</p>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="grid grid-cols-2 gap-3">
            <button id="validateBtn" disabled class="w-full py-2.5 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed border border-slate-700">
              Validate Only
            </button>
            <button id="uploadBtn" disabled class="w-full py-2.5 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-950">
              Bulk Upload
            </button>
          </div>

          <div id="resumeContainer" class="hidden pt-2 border-t border-slate-800">
            <button id="resumeBtn" class="w-full py-2.5 px-4 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-sm font-semibold transition flex items-center justify-center gap-2">
              <span>Resume Failed Operations</span>
            </button>
          </div>
        </div>

        <!-- CSV Content Preview -->
        <div class="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">CSV Data Preview</h3>
            <span id="rowCountBadge" class="text-xs text-slate-500">0 rows</span>
          </div>
          <pre id="csvPreview" class="text-xs text-slate-300 bg-slate-900 p-3 rounded-lg overflow-x-auto max-h-48 border border-slate-800">No file selected.</pre>
        </div>
      </div>

      <!-- Live Monitoring & Results -->
      <div class="lg:col-span-7 space-y-6">
        <!-- Progress Bar Card -->
        <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-base font-semibold text-white">Execution Progress</h2>
              <p class="text-xs text-slate-400 mt-0.5" id="batchIdLabel">Batch ID: <span class="font-mono text-slate-500">None</span></p>
            </div>
            <span id="statusBadge" class="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
              Idle
            </span>
          </div>

          <!-- Progress bar -->
          <div class="space-y-2">
            <div class="w-full bg-slate-900 rounded-full h-3 border border-slate-800 overflow-hidden">
              <div id="progressBar" class="bg-emerald-500 h-3 rounded-full transition-all duration-300 w-0"></div>
            </div>
            <div class="flex justify-between text-xs text-slate-400">
              <span id="progressPercent">0%</span>
              <span id="progressStats">0 / 0 hospitals</span>
              <span id="timerLabel">0.00s</span>
            </div>
          </div>
        </div>

        <!-- Table of Hospital Results -->
        <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-white">Batch Hospital Results</h2>
            <span id="activationBadge" class="hidden px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Batch Activated
            </span>
          </div>

          <div class="overflow-x-auto max-h-64 border border-slate-800 rounded-xl">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-900 text-slate-400 sticky top-0 border-b border-slate-800">
                <tr>
                  <th class="p-3 font-semibold">Row</th>
                  <th class="p-3 font-semibold">ID</th>
                  <th class="p-3 font-semibold">Hospital Name</th>
                  <th class="p-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody id="resultsTableBody" class="divide-y divide-slate-800 text-slate-300">
                <tr>
                  <td colspan="4" class="p-4 text-center text-slate-500">No batch processed yet.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- JSON Response Viewer -->
        <div class="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Exact JSON Response</h3>
            <button id="copyJsonBtn" class="text-xs text-slate-400 hover:text-slate-200">Copy JSON</button>
          </div>
          <pre id="jsonViewer" class="text-xs text-emerald-400 bg-slate-900 p-3 rounded-lg overflow-x-auto max-h-56 border border-slate-800">{ "message": "Awaiting execution..." }</pre>
        </div>
      </div>
    </div>
  </main>

  <script>
    const sampleCSV = `name,address,phone
General Hospital,123 Main St,555-1234
City Medical Center,456 Oak Ave,555-5678
Sunrise Community Clinic,789 Pine Rd,
Metro Heart Institute,321 Elm Blvd,555-9012
Green Valley Hospital,654 Maple Dr,555-3456`;

    let selectedFile = null;
    let activeBatchId = null;
    let websocket = null;

    const fileInput = document.getElementById('fileInput');
    const dropzone = document.getElementById('dropzone');
    const fileName = document.getElementById('fileName');
    const csvPreview = document.getElementById('csvPreview');
    const rowCountBadge = document.getElementById('rowCountBadge');
    const validateBtn = document.getElementById('validateBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const useSampleBtn = document.getElementById('useSampleBtn');
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressStats = document.getElementById('progressStats');
    const timerLabel = document.getElementById('timerLabel');
    const statusBadge = document.getElementById('statusBadge');
    const batchIdLabel = document.getElementById('batchIdLabel');
    const resultsTableBody = document.getElementById('resultsTableBody');
    const jsonViewer = document.getElementById('jsonViewer');
    const activationBadge = document.getElementById('activationBadge');
    const resumeContainer = document.getElementById('resumeContainer');
    const resumeBtn = document.getElementById('resumeBtn');

    function handleFile(file) {
      if (!file) return;
      selectedFile = file;
      fileName.textContent = file.name;
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target.result;
        csvPreview.textContent = text;
        const lines = text.trim().split('\\n').filter(l => l.trim().length > 0);
        const rows = Math.max(0, lines.length - 1);
        rowCountBadge.textContent = `${rows} record${rows === 1 ? '' : 's'}`;
        validateBtn.disabled = false;
        uploadBtn.disabled = false;
      };
      reader.readAsText(file);
    }

    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('border-emerald-500'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('border-emerald-500'));
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('border-emerald-500');
      if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });

    useSampleBtn.addEventListener('click', () => {
      const blob = new Blob([sampleCSV], { type: 'text/csv' });
      const file = new File([blob], 'sample_hospitals.csv', { type: 'text/csv' });
      handleFile(file);
    });

    validateBtn.addEventListener('click', async () => {
      if (!selectedFile) return;
      validateBtn.disabled = true;
      validateBtn.textContent = 'Validating...';
      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const res = await fetch('/hospitals/bulk/validate', { method: 'POST', body: formData });
        const data = await res.json();
        jsonViewer.textContent = JSON.stringify(data, null, 2);
        if (data.valid) {
          alert(`Validation Successful! Found ${data.total_rows} valid records.`);
        } else {
          alert(`Validation Failed with ${data.issues.length} issue(s). Check JSON viewer.`);
        }
      } catch (err) {
        alert('Validation error: ' + err.message);
      } finally {
        validateBtn.disabled = false;
        validateBtn.textContent = 'Validate Only';
      }
    });

    uploadBtn.addEventListener('click', async () => {
      if (!selectedFile) return;
      uploadBtn.disabled = true;
      validateBtn.disabled = true;
      uploadBtn.textContent = 'Processing...';
      resumeContainer.classList.add('hidden');
      statusBadge.textContent = 'Processing';
      statusBadge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';

      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const res = await fetch('/hospitals/bulk', { method: 'POST', body: formData });
        const data = await res.json();
        jsonViewer.textContent = JSON.stringify(data, null, 2);
        renderResponse(data);
      } catch (err) {
        alert('Bulk upload error: ' + err.message);
        statusBadge.textContent = 'Failed';
        statusBadge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/40';
      } finally {
        uploadBtn.disabled = false;
        validateBtn.disabled = false;
        uploadBtn.textContent = 'Bulk Upload';
      }
    });

    resumeBtn.addEventListener('click', async () => {
      if (!activeBatchId) return;
      resumeBtn.disabled = true;
      resumeBtn.textContent = 'Resuming...';
      try {
        const res = await fetch(`/hospitals/bulk/${activeBatchId}/resume`, { method: 'POST' });
        const data = await res.json();
        jsonViewer.textContent = JSON.stringify(data, null, 2);
        renderResponse(data);
      } catch (err) {
        alert('Resume error: ' + err.message);
      } finally {
        resumeBtn.disabled = false;
        resumeBtn.textContent = 'Resume Failed Operations';
      }
    });

    function renderResponse(data) {
      if (!data || !data.batch_id) return;
      activeBatchId = data.batch_id;
      batchIdLabel.innerHTML = `Batch ID: <span class="font-mono text-emerald-400">${data.batch_id}</span>`;
      timerLabel.textContent = `${data.processing_time_seconds || 0}s`;

      const total = data.total_hospitals || 0;
      const processed = data.processed_hospitals || 0;
      const failed = data.failed_hospitals || 0;
      const pct = total > 0 ? Math.round((processed / total) * 100) : 0;

      progressBar.style.width = `${pct}%`;
      progressPercent.textContent = `${pct}%`;
      progressStats.textContent = `${processed} / ${total} hospitals`;

      if (data.batch_activated) {
        activationBadge.classList.remove('hidden');
        statusBadge.textContent = 'Completed & Activated';
        statusBadge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';
        resumeContainer.classList.add('hidden');
      } else if (failed > 0) {
        activationBadge.classList.add('hidden');
        statusBadge.textContent = 'Partially Failed';
        statusBadge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/40';
        resumeContainer.classList.remove('hidden');
      }

      if (data.hospitals && data.hospitals.length > 0) {
        resultsTableBody.innerHTML = data.hospitals.map(h => {
          let badge = '<span class="px-2 py-0.5 rounded text-emerald-400 bg-emerald-500/10">Active</span>';
          if (h.status === 'failed') {
            badge = `<span class="px-2 py-0.5 rounded text-rose-400 bg-rose-500/10" title="${h.error || ''}">Failed</span>`;
          } else if (h.status === 'created_inactive') {
            badge = '<span class="px-2 py-0.5 rounded text-amber-400 bg-amber-500/10">Inactive</span>';
          }
          return `
            <tr class="hover:bg-slate-900/50">
              <td class="p-3 text-slate-400 font-mono">#${h.row}</td>
              <td class="p-3 text-slate-300 font-mono">${h.hospital_id || '-'}</td>
              <td class="p-3 font-medium text-white">${h.name}</td>
              <td class="p-3">${badge}</td>
            </tr>
          `;
        }).join('');
      }
    }

    document.getElementById('copyJsonBtn').addEventListener('click', () => {
      navigator.clipboard.writeText(jsonViewer.textContent);
      alert('Copied JSON to clipboard!');
    });
  </script>
</body>
</html>
"""
