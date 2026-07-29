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
    const explanationText = document.getElementById('explanation-text');
    const evidenceContainer = document.getElementById('evidence-container');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const query = document.getElementById('query').value.trim();
        const llm_response = document.getElementById('llm_response').value.trim();

        if (!query || !llm_response) return;

        // UI Loading state
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

            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            const data = await response.json();
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
        const isSupported = (data.verdict || '').toLowerCase() === 'supported';
        
        verdictBanner.className = 'verdict-banner ' + (isSupported ? 'supported' : 'hallucinated');
        verdictText.textContent = data.verdict;
        
        const confScore = data.confidence || data.confidence_score || 0;
        confidenceVal.textContent = `${confScore}%`;
        confidenceBar.style.width = `${confScore}%`;
        confidenceBar.style.backgroundColor = isSupported ? '#10b981' : '#ef4444';

        explanationText.textContent = data.reason || data.explanation || 'No reason provided.';

        // Render Evidence Cards
        evidenceContainer.innerHTML = '';
        const evidenceList = data.retrieved_evidence || [];

        if (evidenceList.length === 0) {
            evidenceContainer.innerHTML = '<p class="text-secondary">No evidence matches found.</p>';
        } else {
            evidenceList.forEach((item, idx) => {
                const scorePercent = item.similarity_score ? Math.round(item.similarity_score * 100) : 85;
                const card = document.createElement('div');
                card.className = 'evidence-card';
                card.innerHTML = `
                    <div class="evidence-header">
                        <span>📄 ${item.document_name || `Doc Chunk #${idx + 1}`}</span>
                        <span>Similarity: ${scorePercent}%</span>
                    </div>
                    <div class="evidence-content">${escapeHtml(item.content)}</div>
                `;
                evidenceContainer.appendChild(card);
            });
        }

        resultContent.classList.remove('hidden');
    }

    function escapeHtml(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
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
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            if (res.ok) {
                uploadStatus.style.color = '#10b981';
                uploadStatus.textContent = `✅ ${data.message}`;
                fileInput.value = '';
                fileNameDisplay.textContent = 'No file selected';
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (err) {
            uploadStatus.style.color = '#ef4444';
            uploadStatus.textContent = `❌ Upload error: ${err.message}`;
        } finally {
            btnUpload.textContent = 'Upload & Index';
        }
    });
}