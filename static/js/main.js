function renderExpensesChart(labels, totals){
	const ctx = document.getElementById('expensesChart');
	if(!ctx){ return; }
	const d = {
		labels,
		datasets: [{
			label: 'Monthly Spend (₹)',
			data: totals,
			borderColor: '#4f7cff',
			backgroundColor: 'rgba(79,124,255,0.2)',
			tension: 0.3,
			fill: true,
			pointRadius: 3
		}]
	};
	new Chart(ctx, { type: 'line', data: d, options: { plugins: { legend: { labels: { color: '#e7ecff' } } }, scales: { x: { ticks:{ color:'#9cb0da' }, grid:{ color:'rgba(255,255,255,0.06)'} }, y: { ticks:{ color:'#9cb0da' }, grid:{ color:'rgba(255,255,255,0.06)'} } } } });
}
