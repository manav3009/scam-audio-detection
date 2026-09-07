const scamPhrases = [
    "Your bank account has been compromised",
    "Please verify your social security number",
    "You've won a lottery prize",
    "We need your credit card details for verification",
    "Your account will be suspended",
    "Send money via gift cards immediately",
    "The IRS is filing a lawsuit against you",
    "Please share the OTP sent to your phone",
    "This is a limited time offer",
    "Your computer has a virus"
];

let simulationInterval = null;
let currentIndex = 0;

document.getElementById('startBtn').addEventListener('click', startSimulation);
document.getElementById('stopBtn').addEventListener('click', stopSimulation);

function startSimulation() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Simulating...';
    stopBtn.disabled = false;
    stopBtn.classList.remove('bg-red-600/50', 'cursor-not-allowed');
    stopBtn.classList.add('bg-red-600', 'hover:bg-red-700', 'text-white');
    
    currentIndex = 0;
    simulationInterval = setInterval(simulateCall, 3000);
    simulateCall(); // First call immediately
}

function stopSimulation() {
    if (simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
    }
    
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    startBtn.disabled = false;
    startBtn.innerHTML = '<i class="fas fa-play mr-2"></i>Start Simulation';
    stopBtn.disabled = true;
    stopBtn.classList.remove('bg-red-600', 'hover:bg-red-700', 'text-white');
    stopBtn.classList.add('bg-red-600/50', 'cursor-not-allowed', 'text-red-400');
    
    document.getElementById('transcript').innerHTML = 'Simulation stopped. Click "Start Simulation" to begin.';
}

async function simulateCall() {
    if (currentIndex >= scamPhrases.length) {
        currentIndex = 0;
    }
    
    const transcript = scamPhrases[currentIndex];
    document.getElementById('transcript').innerHTML = `<span class="text-blue-400">Caller:</span> "${transcript}"`;
    
    // Analyze the transcript
    const response = await fetch('/api/analyze_live', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript: transcript })
    });
    
    const data = await response.json();
    updateUI(data);
    
    currentIndex++;
}

function updateUI(data) {
    // Update risk score
    document.getElementById('riskScore').textContent = `${data.risk_score}%`;
    const riskBar = document.getElementById('riskBar');
    riskBar.style.width = `${data.risk_score}%`;
    
    // Change bar color based on risk
    if (data.risk_score >= 70) {
        riskBar.classList.remove('bg-yellow-500', 'bg-green-500');
        riskBar.classList.add('bg-red-500');
    } else if (data.risk_score >= 40) {
        riskBar.classList.remove('bg-red-500', 'bg-green-500');
        riskBar.classList.add('bg-yellow-500');
    } else {
        riskBar.classList.remove('bg-red-500', 'bg-yellow-500');
        riskBar.classList.add('bg-green-500');
    }
    
    // Update risk level
    const riskLevelElem = document.getElementById('riskLevel');
    riskLevelElem.textContent = data.risk_level;
    riskLevelElem.className = `text-lg font-semibold text-${data.color}-400`;
    
    // Update recommendation
    document.getElementById('recommendation').textContent = data.recommendation;
    
    // Update keywords
    const keywordsDiv = document.getElementById('keywords');
    if (data.detected_keywords.length > 0) {
        keywordsDiv.innerHTML = data.detected_keywords.map(kw => 
            `<span class="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">${kw}</span>`
        ).join('');
    } else {
        keywordsDiv.innerHTML = '<span class="text-gray-500 text-sm">No suspicious keywords detected</span>';
    }
}