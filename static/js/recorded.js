const dropZone = document.getElementById('dropZone');
const audioInput = document.getElementById('audioFile');
const analyzeBtn = document.getElementById('analyzeBtn');
let selectedFile = null;

dropZone.addEventListener('click', () => audioInput.click());
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-purple-500', 'bg-purple-500/10');
});
dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-purple-500', 'bg-purple-500/10');
});
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-purple-500', 'bg-purple-500/10');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('audio/')) {
        handleFile(file);
    } else {
        alert('Please upload a valid audio file');
    }
});

audioInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
    }
    selectedFile = file;
    analyzeBtn.disabled = false;
    dropZone.innerHTML = `
        <i class="fas fa-check-circle text-4xl text-green-500 mb-3"></i>
        <p class="text-gray-300">File selected: ${file.name}</p>
        <p class="text-gray-500 text-sm mt-2">${(file.size / 1024 / 1024).toFixed(2)} MB</p>
    `;
}

analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    const formData = new FormData();
    formData.append('audio_file', selectedFile);
    
    // Show loading overlay
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.classList.remove('hidden');
    loadingOverlay.classList.add('flex');
    
    try {
        const response = await fetch('/api/analyze_recorded', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.report);
        } else {
            alert('Analysis failed: ' + data.message);
        }
    } catch (error) {
        alert('Error during analysis: ' + error.message);
    } finally {
        loadingOverlay.classList.add('hidden');
        loadingOverlay.classList.remove('flex');
    }
});

function displayResults(report) {
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.classList.remove('hidden');
    
    // Update risk score with color
    const scoreElem = document.getElementById('reportScore');
    scoreElem.textContent = `${report.risk_score}%`;
    if (report.risk_score >= 70) {
        scoreElem.className = 'text-2xl font-bold text-red-400';
    } else if (report.risk_score >= 40) {
        scoreElem.className = 'text-2xl font-bold text-yellow-400';
    } else {
        scoreElem.className = 'text-2xl font-bold text-green-400';
    }
    
    // Risk level
    const levelElem = document.getElementById('reportLevel');
    levelElem.textContent = report.risk_level;
    if (report.risk_level === 'HIGH') {
        levelElem.className = 'text-lg font-semibold text-red-400';
    } else if (report.risk_level === 'MEDIUM') {
        levelElem.className = 'text-lg font-semibold text-yellow-400';
    } else {
        levelElem.className = 'text-lg font-semibold text-green-400';
    }
    
    // Transcript
    document.getElementById('reportTranscript').textContent = `"${report.transcript}"`;
    
    // Scam indicators
    const indicatorsList = document.getElementById('reportIndicators');
    indicatorsList.innerHTML = report.scam_indicators.map(ind => 
        `<li class="text-gray-300">• ${ind}</li>`
    ).join('');
    
    // Recommended action
    document.getElementById('reportAction').textContent = report.recommended_action;
    
    // Analysis time
    document.getElementById('analysisTime').textContent = report.analysis_duration;
    
    // Smooth scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}