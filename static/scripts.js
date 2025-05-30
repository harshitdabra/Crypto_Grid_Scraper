async function fetchData(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error(`Failed to fetch data: ${response.status} ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return { error: error.message };
    }
}

function formatDateTime(dateString) {
    if (!dateString || typeof dateString !== 'string') return 'N/A';
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return 'N/A'; // Invalid date
        const pad = n => n.toString().padStart(2, '0');
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
    } catch (error) {
        console.error('Error formatting date:', dateString, error);
        return 'N/A';
    }
}


function createGeneralInfoCard(data) {
    return `
        <div class="card">
            <h3>${data.coin} - ${data.full_name}</h3>
            <p>Launch Date: ${data.launch_date}</p>
            <p>Algorithm: ${data.algorithm}</p>
            <p>Proof Type: ${data.proof_type}</p>
            <p>Price: $${data.price_usd}</p>
            <p>Market Cap: ${data.market_cap_usd}</p>
        </div>
    `;
}

function createPriceCard(data) {
    return `
        <div class="card price-card">
            <span>${data.coin}</span>
            <span>$${data.price_usd}</span>
        </div>
    `;
}

function createNewsCard(data) {
    return `
        <div class="card news-card">
            <h3>${data.title}</h3>
            <p>Source: ${data.source}</p>
            <a href="${data.link}" target="_blank">Read More</a>
            <p>Time: ${formatDateTime(data.time_utc)}</p>
            
        </div>
    `;
}

function createSentimentGauge(data) {
    const buzzLevel = data.score ? (data.score / 10000 * 100).toFixed(2) : 0;
    return `
        <div class="card">
            <h3>${data.symbol}</h3>
            <p>${data.interpretation}</p>
            <div class="sentiment-gauge">
                <div class="sentiment-bar" style="width: ${buzzLevel}%"></div>
            </div>
        </div>
    `;
}

async function loadGeneralInfo() {
    const data = await fetchData('/api/general_info');
    const container = document.getElementById('general-info-container');
    container.innerHTML = data ? data.map(createGeneralInfoCard).join('') : '<p class="text-red-500">Error loading data</p>';
}

async function loadPrices() {
    const data = await fetchData('/api/prices');
    const container = document.getElementById('prices-container');
    container.innerHTML = data ? data.map(createPriceCard).join('') : '<p class="text-red-500">Error loading data</p>';
}

async function loadNews() {
    const data = await fetchData('/api/news');
    const container = document.getElementById('news-container');
    container.innerHTML = data ? data.map(createNewsCard).join('') : '<p class="text-red-500">Error loading data</p>';
}

async function loadSentiment() {
    const data = await fetchData('/api/sentiment');
    const container = document.getElementById('sentiment-container');
    container.innerHTML = data ? data.map(createSentimentGauge).join('') : '<p class="text-red-500">Error loading data</p>';
}

document.getElementById('refresh-btn').addEventListener('click', () => {
    loadGeneralInfo();
    loadPrices();
    loadNews();
    loadSentiment();
});

window.onload = () => {
    loadGeneralInfo();
    loadPrices();
    loadNews();
    loadSentiment();
};