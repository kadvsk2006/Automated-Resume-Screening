const fileInput = document.getElementById('fileInput');
const dropzone = document.getElementById('dropzone');
let files = [];

// Global store of current combined results (PDF + CSV)
window.currentResults = [];

dropzone.onclick = () => fileInput.click();

fileInput.onchange = (e) => {
    files = [...files, ...Array.from(e.target.files)];
    document.getElementById('fileList').innerText = `${files.length} file(s) selected`;
    dropzone.style.borderColor = "#0ea5e9";
    dropzone.style.background = "#f0f9ff";
};

// Drag and drop
dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "#0ea5e9";
    dropzone.style.background = "#e0f2fe";
});

dropzone.addEventListener('dragleave', () => {
    dropzone.style.borderColor = "#cbd5e1";
    dropzone.style.background = "#f1f5f9";
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "#cbd5e1";
    dropzone.style.background = "#f1f5f9";
    
    if (e.dataTransfer.files.length > 0) {
        files = [...files, ...Array.from(e.dataTransfer.files)];
        document.getElementById('fileList').innerText = `${files.length} file(s) selected`;
        dropzone.style.borderColor = "#0ea5e9";
        dropzone.style.background = "#f0f9ff";
    }
});

document.getElementById('rankBtn').onclick = async () => {
    const jd = document.getElementById('jd').value;
    if (!jd || jd.trim().length < 50) {
        return alert("Please enter a Job Description (minimum 50 characters)");
    }

    const formData = new FormData();
    formData.append('job_description', jd);
    formData.append('include_csv', document.getElementById('csvCheck').checked);
    formData.append('threshold', 0); // No threshold filter
    
    files.forEach(f => formData.append('files', f));

    const btn = document.getElementById('rankBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/screen-resumes', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server error: ${res.status}`);
        }

        const data = await res.json();
        renderTables(data);
    } catch (e) {
        console.error('Error:', e);
        alert("Error processing request: " + e.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
};

function renderTables(data) {
    document.getElementById('resultsArea').classList.remove('d-none');

    // 1. PDF Results
    const pdfs = data.uploaded_results || [];
    const pdfSection = document.getElementById('pdfSection');
    if (pdfs.length > 0) {
        pdfSection.classList.remove('d-none');
        document.getElementById('pdfTableBody').innerHTML = pdfs.map(r => rowHtml(r, 'pdf')).join('');
    } else {
        pdfSection.classList.add('d-none');
    }

    // 2. CSV Results
    const csvs = data.database_results || [];
    const csvSection = document.getElementById('csvSection');
    if (csvs.length > 0) {
        csvSection.classList.remove('d-none');
        document.getElementById('csvTableBody').innerHTML = csvs.map(r => rowHtml(r, 'csv')).join('');
    } else {
        csvSection.classList.add('d-none');
    }

    // Store combined results for explainability & export
    window.currentResults = [...pdfs, ...csvs];
}

function rowHtml(res, type) {
    console.log("Rendering row:", res.candidate_name || res.filename, res.skills);

    let skillsValue = res.skills;

    // If skills is a serialized string (e.g., "['Python', 'Java']"), try to parse it
    if (typeof skillsValue === 'string') {
        try {
            const normalized = skillsValue.replace(/'/g, '"');
            const parsed = JSON.parse(normalized);
            skillsValue = parsed;
        } catch (e) {
            console.warn('Failed to parse skills string:', skillsValue, e);
            skillsValue = [];
        }
    }

    let skillBadges = '<span class="badge bg-warning text-dark">No Skills</span>';
    if (skillsValue && Array.isArray(skillsValue) && skillsValue.length > 0) {
        const visibleSkills = skillsValue.slice(0, 4);
        skillBadges = visibleSkills
            .map((s) => `<span class="skill-tag">${escapeHtml(String(s))}</span>`)
            .join('');

        if (skillsValue.length > 4) {
            skillBadges += `<span class="skill-tag">+${skillsValue.length - 4}</span>`;
        }
    }

    const badge = type === 'pdf' 
        ? '<span class="badge-pdf">PDF Upload</span>' 
        : '<span class="badge-csv">Database</span>';

    const encodedFilename = encodeURIComponent(res.filename || '');
    const viewBtn = `<button onclick="showDetails('${encodedFilename}')" class="btn btn-sm btn-light border me-1">View Details</button>`;

    const downloadBtn = type === 'pdf' 
        ? `<a href="/download/${encodeURIComponent(res.filename)}" class="btn btn-sm btn-outline-primary"><i class="fas fa-download"></i></a>` 
        : '';

    const actionButtons = `${viewBtn}${downloadBtn}`;
    
    const scoreColor = res.match_score >= 75 ? 'bg-success' : res.match_score >= 40 ? 'bg-warning' : 'bg-danger';
    const candidateName = escapeHtml(res.candidate_name || res.filename || 'Unknown');
    const matchScore = res.match_score || res.score || 0;
    const rank = res.rank || 0;

    return `<tr>
        <td class="fw-bold text-muted">#${rank}</td>
        <td>
            <div class="fw-bold text-dark">${candidateName}</div>
            ${badge}
        </td>
        <td style="width: 200px;">
            <div class="d-flex align-items-center">
                <span class="fw-bold me-2">${matchScore.toFixed(1)}%</span>
                <div class="progress flex-grow-1" style="height:6px;">
                    <div class="progress-bar ${scoreColor}" style="width:${matchScore}%"></div>
                </div>
            </div>
        </td>
        <td>${skillBadges}</td>
        <td>${actionButtons || '<span class="text-muted">No actions</span>'}</td>
    </tr>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show match explainability details in modal
function showDetails(encodedFilename) {
    try {
        const filename = decodeURIComponent(encodedFilename || '');
        if (!window.currentResults || !window.currentResults.length) {
            alert('No results available. Please run screening first.');
            return;
        }

        const candidate = window.currentResults.find(
            (r) => (r.filename || '') === filename
        );

        if (!candidate) {
            alert('Candidate details not found for this row.');
            return;
        }

        const modalTitleEl = document.getElementById('detailsModalLabel');
        const previewBox = document.getElementById('resumePreviewBox');

        const candidateName = candidate.candidate_name || candidate.filename || 'Unknown Candidate';
        const score = (candidate.match_score || candidate.score || 0).toFixed(1);

        if (modalTitleEl) {
            modalTitleEl.textContent = `${candidateName} – ${score}% match`;
        }

        if (previewBox) {
            const text = candidate.resume_text || '';
            if (!text || !text.trim()) {
                previewBox.innerHTML = '<span class="text-muted small">Resume text not available.</span>';
            } else {
                const preview = text.slice(0, 500);
                previewBox.textContent = preview + (text.length > 500 ? '…' : '');
            }
        }

        const modalEl = document.getElementById('detailsModal');
        if (modalEl && window.bootstrap && window.bootstrap.Modal) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        } else if (modalEl) {
            // Fallback if bootstrap JS not available
            modalEl.classList.add('show');
            modalEl.style.display = 'block';
        }
    } catch (err) {
        console.error('Error showing details modal:', err);
        alert('Unable to show candidate details.');
    }
}

// Export current results to CSV
function exportToCSV() {
    const results = window.currentResults || [];
    if (!results.length) {
        alert('No results to export. Please run screening first.');
        return;
    }

    const headers = [
        'rank',
        'filename',
        'source',
        'candidate_name',
        'match_score',
    ];

    const escapeCsv = (value) => {
        if (value === null || value === undefined) return '';
        const str = String(value);
        if (/[",\n]/.test(str)) {
            return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
    };

    const lines = [];
    lines.push(headers.map(escapeCsv).join(','));

    results.forEach((res) => {
        const row = [
            res.rank || '',
            res.filename || '',
            res.source || '',
            res.candidate_name || '',
            res.match_score || res.score || 0,
        ];
        lines.push(row.map(escapeCsv).join(','));
    });

    const csvContent = lines.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'resume_screening_results.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
