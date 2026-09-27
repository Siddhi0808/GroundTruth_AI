// All server/user-controlled values are rendered with textContent / DOM nodes, never innerHTML.

function apiErrorMessage(data, status) {
    const detail = data && data.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map(d => d.msg).join('; ');
    if (detail && detail.message) return detail.message + (detail.error_id ? ` (ref ${detail.error_id})` : '');
    return `Server returned status ${status}`;
}

function verdictClass(verdict) {
    const v = (verdict || '').toLowerCase();
    if (v === 'supported') return 'supported';
    if (v === 'hallucinated') return 'hallucinated';
    return 'insufficient';
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('detect-form');
    const btnSubmit = document.getElementById('btn-submit');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');

    const placeholderState = document.getElementById('placeholder-state');
    const pipelineStatus = document.getElementById('pipeline-status');
    const resultContent = document.getElementById('result-content');

    const verdictBanner = document.getElementById('verdict-banner');
    const verdictText = document.getElementById('verdict-text');
    const confidenceVal = document.getElementById('confidence-val');
    const confidenceBar = document.getElementById('confidence-bar');
    const engineNote = document.getElementById('engine-note');
    const explanationText = document.getElementById('explanation-text');
    const evidenceContainer = document.getElementById('evidence-container');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const query = document.getElementById('query').value.trim();
        const llm_response = document.getElementById('llm_response').value.trim();

        if (!query || !llm_response) return;

        btnSubmit.disabled = true;
        btnText.textContent = "Analyzing...";
        btnSpinner.classList.remove('hidden');

        placeholderState.classList.add('hidden');
        resultContent.classList.add('hidden');
        pipelineStatus.classList.remove('hidden');

        try {
            const response = await fetch('/detect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, llm_response, top_k: 3 })
            });
            const data = await response.json().catch(() => null);
            if (!response.ok) {
                throw new Error(apiErrorMessage(data, response.status));
            }
            renderResults(data);
        } catch (err) {
            alert(`Detection failed: ${err.message}`);
            placeholderState.classList.remove('hidden');
        } finally {
            btnSubmit.disabled = false;
            btnText.textContent = "Detect Hallucination";
            btnSpinner.classList.add('hidden');
            pipelineStatus.classList.add('hidden');
        }
    });

    function renderResults(data) {
        const cls = verdictClass(data.verdict);
        const colors = { supported: '#10b981', hallucinated: '#ef4444', insufficient: '#f59e0b' };

        verdictBanner.className = 'verdict-banner ' + cls;
        verdictText.textContent = data.verdict;

        const confScore = data.confidence ?? data.confidence_score ?? 0;
        confidenceVal.textContent = `${confScore}%`;
        confidenceBar.style.width = `${confScore}%`;
        confidenceBar.style.backgroundColor = colors[cls];

        const meta = data.metadata || {};
        let note = meta.engine === 'llm' ? `Judged by LLM (${meta.model_used})`
                 : meta.engine === 'heuristic' ? `Judged by deterministic rules (${meta.model_used}; LLM not used: ${meta.fallback_reason})`
                 : 'No judge ran (no evidence retrieved)';
        if (meta.retrieval_mode === 'keyword') note += ' · Degraded retrieval: SQLite keyword mode';
        engineNote.textContent = note;

        explanationText.textContent = data.reason || data.explanation || 'No reason provided.';

        evidenceContainer.replaceChildren();
        const evidenceList = data.retrieved_evidence || [];
        if (evidenceList.length === 0) {
            const p = document.createElement('p');
            p.className = 'text-secondary';
            p.textContent = 'No evidence matches found.';
            evidenceContainer.appendChild(p);
        } else {
            evidenceList.forEach((item, idx) => {
                const score = typeof item.similarity_score === 'number' ? Math.round(item.similarity_score * 100) : null;
                const card = document.createElement('div');
                card.className = 'evidence-card';

                const header = document.createElement('div');
                header.className = 'evidence-header';
                const name = document.createElement('span');
                name.textContent = `📄 ${item.document_name || `Doc Chunk #${idx + 1}`}`;
                const sim = document.createElement('span');
                sim.textContent = score === null ? 'Score: n/a' : `Score: ${score}%`;
                header.append(name, sim);

                const content = document.createElement('div');
                content.className = 'evidence-content';
                content.textContent = item.content || '';

                card.append(header, content);
                evidenceContainer.appendChild(card);
            });
        }

        resultContent.classList.remove('hidden');
    }
});

// File Upload Integration
const fileInput = document.getElementById('file-input');
const fileNameDisplay = document.getElementById('file-name-display');
const btnUpload = document.getElementById('btn-upload');
const uploadForm = document.getElementById('upload-form');
const uploadStatus = document.getElementById('upload-status');

if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = e.target.files[0].name;
            btnUpload.disabled = false;
        } else {
            fileNameDisplay.textContent = 'No file selected';
            btnUpload.disabled = true;
        }
    });
}

if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = fileInput.files[0];
        if (!file) return;

        btnUpload.disabled = true;
        btnUpload.textContent = 'Indexing...';
        uploadStatus.style.display = 'block';
        uploadStatus.style.color = '#9ca3af';
        uploadStatus.textContent = 'Parsing text and embedding vectors into database...';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            const data = await res.json().catch(() => null);
            if (!res.ok) {
                throw new Error(apiErrorMessage(data, res.status));
            }
            uploadStatus.style.color = data.status === 'duplicate' ? '#f59e0b' : '#10b981';
            uploadStatus.textContent = `${data.status === 'duplicate' ? 'ℹ️' : '✅'} ${data.message}`;
            fileInput.value = '';
            fileNameDisplay.textContent = 'No file selected';
        } catch (err) {
            uploadStatus.style.color = '#ef4444';
            uploadStatus.textContent = `❌ Upload error: ${err.message}`;
        } finally {
            btnUpload.textContent = 'Upload & Index';
        }
    });
}
