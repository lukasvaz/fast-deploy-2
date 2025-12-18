const groupByChoices = JSON.parse(document.getElementById('group_by_choices_data').textContent);
const filterByChoices = JSON.parse(document.getElementById('filter_by_choices_data').textContent);
const filterValues = JSON.parse(document.getElementById('filter_values_data').textContent);
const objectsQs = JSON.parse(document.getElementById('objects_qs_data').textContent);
const calcularButton = document.getElementById('btn_compute');
var fetchedData = null;

async function fetchIndicadores() {    
    // build URL with query params
    const params = {
                model: document.getElementById('model')?.value || '',
                group_by: document.getElementById('group_by')?.value || '',
                filter_by: document.getElementById('filter_by')?.value || '',
                filter_values: $('#filter_values').val() || [], 
            };
    // TODO use request.scheme to build full URL 
    const url = new URL(computeIndicadoresUrl, window.location.origin);
    Object.keys(params).forEach(key => {
        const value = params[key];
        if (value !== undefined && value !== null) url.searchParams.append(key, value);
    });
    // block button to avoid multiple requests
    calcularButton.disabled = true;
    
    const resp = fetch(url.toString(), {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin'
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }).then(data => {
        fetchedData = data;
        calcularButton.disabled = false;
        const resultContainer= document.getElementById('chart-container');
        // enabling buttons
        resultContainer.classList.remove('d-none');
        const countButton= document.getElementById('count-chart-section');
        const pieButton= document.getElementById('pie-chart-section');
        countButton.disabled = false;
        pieButton.disabled = false;
        
        toggleSectionVisibility('countChart');
        renderIndicadoresResults(data);
    }).catch(error => {
        calcularButton.disabled = false;
        console.error('Error fetching indicadores:', error);    
    })

}

function toggleSectionVisibility(sectionId) {
const countSection= document.getElementById('count-chart-stage-content');
const pieSection= document.getElementById('pie-chart-stage-content');

const countButton= document.getElementById('count-chart-section');
const pieButton= document.getElementById('pie-chart-section');

if (sectionId === 'countChart') {
    countSection.classList.remove('d-none');
    countButton.classList.add('selected');
    
    pieSection.classList.add('d-none');
    pieButton.classList.remove('selected');
}
else if (sectionId === 'pieChart') {
    pieSection.classList.remove('d-none');
    pieButton.classList.add('selected');

    countSection.classList.add('d-none');
    countButton.classList.remove('selected');
}
}
function renderIndicadoresResults(response) {
    const countData = [...response.count_data];
    const percData = [...response.percentage_data];
    
    // preprocesing raw data when more than 15 groups
    if (countData.length >= 15 && percData.length >= 15) {
        const topCountData = countData.slice(0, 15);
        const otherCount = countData.slice(15).reduce((sum, item) => sum + Number(item.count), 0);
        if (otherCount > 0) {
            topCountData.push({ label: 'Otros', count: otherCount });
        }
        countData.length = 0;
        countData.push(...topCountData);

        const topPercData = percData.slice(0, 15);
        const otherPerc = percData.slice(15).reduce((sum, item) => sum + Number(item.percentage), 0);
        if (otherPerc > 0) {
            topPercData.push({ label: 'Otros', percentage: otherPerc });
        }
        percData.length = 0;
        percData.push(...topPercData);
    }

    const countLabels = countData.map(i => i.label) 
    const counts = countData.map(i => Number(i.count));
    countDataMapped=countData.map(i => ({
                x: i.key,        
                y: Number(i.count),
                key: i.label         
            }))
    const countCtx = document.getElementById('indicadoresCountChart');
    if (window.countChart && typeof window.countChart.destroy === 'function') {
        window.countChart.destroy();
    }

    if (countCtx) {
        window.countChart = new Chart(countCtx, {
    type: 'bar',
    data: {
        datasets: [{
            label: 'Cantidad',
            data:countDataMapped,
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        // parsing: false, 
        plugins: {
            tooltip: {
                callbacks: {
                    label: ctx => {
                        const p = ctx.raw;
                        return `${p.key}: ${p.y}`;
                    }
                }
            }
        },
        scales: {
            x: { type: 'category' },
            y: {
                beginAtZero: true,
                title: { display: true, text: 'Cantidad' }
            }
        }
    }
});

    }
    const pieCtx = document.getElementById('indicadoresPieChart');
    const percLabels = percData.map(i => i.label);
    const percentages = percData.map(i => Number(i.percentage));
    if (window.pieChart && typeof window.pieChart.destroy === 'function') {
        window.pieChart.destroy();
    }

    if (pieCtx) {
        // para el pie usamos los porcentajes; si no hay percentages, calcular a partir de counts
        const pieData = (percentages && percentages.length && percentages.some(p => p > 0))
            ? percentages
            : (function() {
                const total = counts.reduce((s, v) => s + v, 0) || 1;
                return counts.map(c => (c / total) * 100);
            })();

        const bg = percLabels.map((_, i) => `hsl(${(i * 45) % 360} 70% 50% / 0.8)`);
        const border = percLabels.map((_, i) => `hsl(${(i * 45) % 360} 70% 40% / 1)`);

        window.pieChart = new Chart(pieCtx, {
            type: 'pie',
            data: {
                labels:percLabels,
                datasets: [{
                    data: pieData,
                    backgroundColor: bg,
                    borderColor: border,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 12 } },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                const v = ctx.raw;
                                return `${ctx.label}: ${Number(v).toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
    }
}
function populateGroupByOptions(modelValue) {
    const groupBySelect = document.getElementById('group_by');
    groupBySelect.innerHTML = '';
    groupByChoices[modelValue].forEach(choice => {
        const option = document.createElement('option');
        option.value = choice.value;
        option.textContent = choice.label;
        groupBySelect.appendChild(option);
    });
}
function populateFilterOptions(modelValue) {
    const filterSelect = document.getElementById('filter_by');
    filterSelect.innerHTML = '';
    const option = document.createElement('option');
        option.value = "";
        option.textContent = "Omitir filtro";
        option.selected = true;
        filterSelect.appendChild(option);
    filterByChoices[modelValue].forEach(choice => {
        const option = document.createElement('option');
        option.value = choice.value;
        option.textContent = choice.label;
        filterSelect.appendChild(option);
    }
);
}
function populateFilterValuesOptions(filterValue) {
    const container = document.getElementById('filter_values');
    const choices = filterValues[filterValue] || [];

    // Clear existing options
    container.innerHTML = '';

    // If no choices are available, disable the Select2 dropdown
    if (!choices.length) {
        const btn = $('#filter_values');
        btn.select2({
            placeholder: 'Seleccione un Filtro',
            allowClear: true,
        });
        btn.prop('disabled', true);
    } else {
        // Enable the Select2 dropdown
        const btn = $('#filter_values');
        btn.prop('disabled', false);

        // Populate the Select2 options
        const options = choices.map(ch => {
            return { id: ch.value, text: ch.label };
        });

        // Initialize or reinitialize Select2
        btn.select2({
            data: options,
            width: '100%',
            placeholder: 'Seleccione valores',
            allowClear: true,
        });
    }
}
function exportToExcel() {
    if (!fetchedData) {
        return;
    }

    const countData = fetchedData.count_data || [];
    const percData = fetchedData.percentage_data || [];
    const objectsQs = fetchedData.objects_qs || [];

    // Prepare data for the first sheet (Grouped Data)
    const groupedDataSheet = [["Label", "Count", "Percentage"]]; // Header row
    countData.forEach((item, index) => {
        const percentage = percData[index] ? percData[index].percentage : 0;
        groupedDataSheet.push([item.label, item.count, percentage.toFixed(2)]);
    });

    // Prepare data for the second sheet (Raw Data)
    const rawDataSheet = [];
    if (objectsQs.length > 0) {
        // Dynamically generate headers based on the keys of the first object
        const headers = Object.keys(objectsQs[0]);
        rawDataSheet.push(headers);

        // Add rows dynamically based on the attributes in each object
        objectsQs.forEach(item => {
            const row = headers.map(header => item[header] || ""); // Use empty string for missing values
            rawDataSheet.push(row);
        });
    }

    // Create workbook and append sheets
    const workbook = XLSX.utils.book_new();
    const groupedDataWorksheet = XLSX.utils.aoa_to_sheet(groupedDataSheet);
    const rawDataWorksheet = XLSX.utils.aoa_to_sheet(rawDataSheet);

    XLSX.utils.book_append_sheet(workbook, groupedDataWorksheet, "Grouped Data");
    XLSX.utils.book_append_sheet(workbook, rawDataWorksheet, "Raw Data");

    // Export to Excel file
    XLSX.writeFile(workbook, "indicadores.xlsx");
}

window.addEventListener('load', () => {
    const modelSelect = document.getElementById('model');
    const filterBySelect = document.getElementById('filter_by');
    populateGroupByOptions(modelSelect.value);
    populateFilterOptions(modelSelect.value);
    populateFilterValuesOptions(filterBySelect.value);
    
    modelSelect.addEventListener('change', (e) => {
        populateGroupByOptions(e.target.value);
        populateFilterOptions(e.target.value);
    });

    filterBySelect.addEventListener('change', (e) => {
        populateFilterValuesOptions(e.target.value);
    });
$('#filter_values').select2({
    width: '100%',
    placeholder: 'Seleccione un Filtro',
    allowClear: true,
    multiple: true, 
  });    
    
});
