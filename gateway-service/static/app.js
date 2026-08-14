// Progressive enhancement only: all forms and pages work without JavaScript.
const select = document.querySelector("[data-monitoring-select]");
const panel = document.querySelector("[data-monitoring-panel]");

if (select && panel) {
    select.addEventListener("change", async (event) => {
        const farmId = event.target.value;
        if (!farmId) {
            window.location.href = "/monitoring";
            return;
        }

        panel.classList.add("loading");
        try {
            const response = await fetch(`/ajax/monitoring/${farmId}`);
            if (!response.ok) throw new Error("Monitoring service unavailable");
            const data = await response.json();
            panel.dataset.farmId = farmId;
            renderMonitoringPanel(data, farmId);
        } catch (error) {
            panel.innerHTML = `<div class="empty-state"><h2>Monitoring data unavailable</h2><p>${error.message}</p></div>`;
        } finally {
            panel.classList.remove("loading");
        }
    });
}

function renderMonitoringPanel(data, farmId) {
    const latest = data.latest;
    const summary = data.summary;
    const value = (item, suffix = "") => item === null || item === undefined ? "--" : `${Number(item).toFixed(1)}${suffix}`;
    panel.innerHTML = `
        <section class="metrics-grid">
            <article class="metric amber"><span>Temperature</span><strong>${value(latest?.temperature, " °C")}</strong></article>
            <article class="metric blue"><span>Humidity</span><strong>${value(latest?.humidity, " %")}</strong></article>
            <article class="metric green"><span>Soil moisture</span><strong>${value(latest?.soil_moisture, " %")}</strong></article>
            <article class="metric violet"><span>Rainfall total</span><strong>${value(summary?.total_rainfall, " mm")}</strong></article>
        </section>
        <section class="summary-bar"><div><b>${summary.readings_count}</b><span>readings</span></div><div><b>${value(summary.avg_temperature)}</b><span>avg temp C</span></div><div><b>${value(summary.avg_humidity)}</b><span>avg humidity %</span></div><div><b>${value(summary.avg_soil_moisture)}</b><span>avg moisture %</span></div></section>
        <section class="latest-note"><div><p class="eyebrow">LATEST SIGNAL</p><h2>${latest?.sensor_id || "No readings yet"}</h2></div><p>${latest?.timestamp || "Record a sensor reading to populate this panel."}</p><a class="text-link" href="/monitoring/history?farm_id=${farmId}">View complete history →</a></section>`;
}
