// Filtros
  const table = document.getElementById("corruptTable");
  const rows = Array.from(table.querySelectorAll("tbody tr"));
  const pagination = document.getElementById("pagination");
  const PAGE_SIZE = 10;
  let currentPage = 1;

  // error  toast
  function showErrorToast(message) {
  const toastBody = document.getElementById("errorToastBody");
  toastBody.textContent = message;
  const toastEl = document.getElementById("errorToast");
  const toast = new bootstrap.Toast(toastEl);
  toast.show();
  }  

// Table settings
const dt = $(table).DataTable({
  pageLength: PAGE_SIZE,
  lengthChange: false,
  ordering: false,
  autoWidth: false,
  columnDefs: [{ targets: -1, orderable: false }],
  language: {
    paginate: { previous: 'Anterior', next: 'Siguiente' },
    info: 'Mostrando _START_-_END_ de _TOTAL_',
    zeroRecords: 'No hay registros'
  },
   dom: "<'row'<'col-sm-12'tr>>" + // Remove the default search bar
       "<'row'<'col-sm-6'i><'col-sm-6'p>>", // Keep info and pagination
});
  //filters section
  const gradosCheckbox = document.getElementById("filterGrados");
  const academicosCheckbox = document.getElementById("filterAcademicos");
  const selectAllFiltered = document.getElementById("selectAllFiltered");
  const universidadSearch = document.getElementById("universidadSearch");
  const paisSearch = document.getElementById("paisSearch");

  function defineFilterQuery() {
    let selectedTipo = "";
    if (gradosCheckbox.checked && !academicosCheckbox.checked) {
      selectedTipo = "Programa";
    } else if (!gradosCheckbox.checked && academicosCheckbox.checked) {
      selectedTipo = "Académico";
    }else if (!gradosCheckbox.checked && !academicosCheckbox.checked) {
      selectedTipo = "---No match---"; // No match
    }
    return selectedTipo;
  } 
  gradosCheckbox.addEventListener("change", function() {
    let query = defineFilterQuery();
    dt.column(1).search(query).draw()
  });

  academicosCheckbox.addEventListener("change", function() {
    let query = defineFilterQuery();
    dt.column(1).search(query).draw()
  });
  universidadSearch.addEventListener("input", function() {  
    const searchTerm = universidadSearch.value.trim();
    dt.column(3).search(searchTerm).draw();
  });
  paisSearch.addEventListener("input", function() {
    const searchTerm = paisSearch.value.trim();
    dt.column(4).search(searchTerm).draw();
  });
  
  selectAllFiltered.addEventListener("change", function() {
    rows.forEach(row => {
      const isGrado = row.classList.contains("row-grado") && gradosCheckbox.checked;
      const isAcademico = row.classList.contains("row-academico") && academicosCheckbox.checked;
      if (isGrado || isAcademico) {
        const checkbox = row.querySelector(".select-row");
        if (checkbox) {
          checkbox.checked = selectAllFiltered.checked;
          row.setAttribute("data-selected", selectAllFiltered.checked ? "true" : "false");
        }
      }
    });
  });

  function getSelectedRows() {
      const selectedRows = [];
      dt.rows({ search: 'applied' }).every(function () {
        const row = this.node(); 
        const checkbox = $(row).find('.select-row'); 
        if (checkbox.prop('checked')) {
          selectedRows.push({
            data: {
              nombre: row.children[2].textContent,
              universidad: row.children[3].textContent,
              pais: row.children[4].textContent
            },
            id: checkbox.data('entry-id'), 
            type: checkbox.data('entry-type'), 
          });
        }
      });
      return selectedRows;
    }
  // Single and bulk review modal
  const modal = document.getElementById("revisarModal");
  const modalBody = document.getElementById("corrupted-data");
  const modalSaveBtn = document.getElementById("revisarModalSave");

  function updateUnidadesDropdown() {
    const paisDropdown = document.getElementById("InputPais");
    const unidadDropdown = document.getElementById("InputUnidad");
    const unidadesData = JSON.parse(document.getElementById("unidades_context").textContent);//  {pais_code : {country_label: "", unidades: {id: "uni - unidad"}}}  
    // Clear existing options in Unidades dropdown
    unidadDropdown.innerHTML = '<option value="">Seleccione una unidad académica</option>';

    // Get selected País
    const selectedPais = paisDropdown.value;

    // Populate Unidades dropdown based on selected País
    if (selectedPais) {
      const paisUnidades = unidadesData[selectedPais];
      if (paisUnidades) {
        const unidades = paisUnidades.unidades;
        for (const u of unidades) {
          const option = document.createElement("option");
          option.value = u.id;
          option.textContent = u.label;
          unidadDropdown.appendChild(option);
      }
      }
  }
  }
  function openModal(entriesData) {
    //entriesData: {data: {nombre,universidad ,pais}, id: entryId, type: entryType}
    modalBody.innerHTML = "";
    let html = "<h6>Datos corruptos:</h6>";
    const corruptedDataDiv = document.getElementById("corrupted-data");

    entriesData.forEach(entry => {
      const entryId = entry.id;
      const data = entry.data;
      const entryType = entry.type;
      html += "<div class='mb-3 p-2 border rounded'>";
      if (entryType === "grado") {
        html += `<div><strong>Nombre:</strong> ${data.nombre}</div>`;
        html += `<div><strong>Universidad:</strong> ${data.universidad}</div>`;
        html += `<div><strong>País universidad:</strong> ${data.pais}</div>`;

      } else if (entryType === "academico") {
        html += `<div><strong>Nombre:</strong> ${data.nombre}</div>`;
        html += `<div><strong>Universidad:</strong> ${data.universidad}</div>`;
        html += `<div><strong>País universidad:</strong> ${data.pais}</div>`;
      }
      html += "</div>";
    });
    corruptedDataDiv.innerHTML = html;

    // ui updates
    $('#revisarModal').on('shown.bs.modal', function () {
        $('#InputPais').select2({
            width: '100%',
            placeholder: 'Seleccione un país',
            allowClear: true,
            dropdownParent: $('#revisarModal')
        });
        $('#InputUnidad').select2({
            width: '100%',
            placeholder: 'Seleccione una unidad académica',
            allowClear: true,
            dropdownParent: $('#revisarModal')
        });
    });
    updateUnidadesDropdown();

    // Save selection
    modalSaveBtn.onclick = function() {
      const unidadDropdown = document.getElementById("InputUnidad");
      const selectedUnidadId = unidadDropdown.value;

      if (!selectedUnidadId) {
        showErrorToast("Debe seleccionar una unidad académica.");
        return;
      }
      
      let endpoint= bulkEditUrl;
      let bodyParams = {
        grados: entriesData.filter(e => e.type === "grado").map(e => e.id),
        academicos: entriesData.filter(e => e.type === "academico").map(e => e.id),
        unidad_id: selectedUnidadId
      }
      fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrftoken
        },
        body: JSON.stringify(bodyParams)
      })
        .then(res => res.json())
        .then(data => {
          if (data.status === "success") {
            bsModal.hide();
            window.location.reload();
          } else {
            showErrorToast(data.message || "Error al guardar la corrección.");
          }
        })
        .catch(() => {
          showErrorToast("Error al guardar la corrección.");
        });
    };

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
  }

  function attachReviewHandlers() {
    document.querySelectorAll("a[id^='revisar-grado-']").forEach(btn => {
      btn.onclick = function(e) {
        e.preventDefault();
        const entryId = this.id.replace("revisar-grado-", "");
        const row = document.getElementById("grado-" + entryId);
        openModal(
          [{ 
            data: {
              nombre: row.children[2].textContent,
              universidad: row.children[3].textContent,
              pais: row.children[4].textContent

            },
            id: entryId,
            type: "grado"
          }]);
      };
    });

    document.querySelectorAll("a[id^='revisar-academico-']").forEach(btn => {
      btn.onclick = function(e) {
        e.preventDefault();
        const entryId = this.id.replace("revisar-academico-", "");
        const row = document.getElementById("academico-" + entryId);
        const invalidType = row.dataset.invalidType || "invalid_university";
        openModal(
          [{ 
            data: {
              nombre: row.children[2].textContent,
              universidad: row.children[3].textContent,
              pais: row.children[4].textContent
            },
            id: entryId,
            type: "academico"
          }]);
      };
    });
  }
  function attachBulkReviewHandler() {
    document.getElementById("bulkReviewBtn").onclick = function() {
      const selected = getSelectedRows();

      if (selected.length === 0) return;
      openModal(selected);
    }
  }
//Single deletion
   function attachDeleteHandlers() {
    document.querySelectorAll("a[id^='eliminar-grado-']").forEach(btn => {
      btn.onclick = function(e) {
        e.preventDefault();
        const entryId = this.id.replace("eliminar-grado-", "");
        fetch(deleteCorruptedGradoUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrftoken
          },
          body: "id=" + entryId
        })
            .then(res => res.json())
            .then(data => {
              if (data.status === "success") {
            const row = document.getElementById("grado-" + entryId);
            if (row) {
                row.remove();
                const idx = rows.indexOf(row);
                if (idx !== -1) rows.splice(idx, 1);
            }
        // renderTable();
      }
      }).catch(err => {
        showErrorToast("Error al eliminar el grado.");
      })
      ;
      };
    });

    document.querySelectorAll("a[id^='eliminar-academico-']").forEach(btn => {
      btn.onclick = function(e) {
        e.preventDefault();
        const entryId = this.id.replace("eliminar-academico-", "");
        fetch(deleteCorruptedAcademicoUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrftoken
          },
          body: "id=" + entryId
        })
        .then(res => res.json())
        .then(data => {
        if (data.status === "success") {
  const row = document.getElementById("academico-" + entryId);
  if (row) {
    row.remove();
    const idx = rows.indexOf(row);
    if (idx !== -1) rows.splice(idx, 1);
  }
  // renderTable();
}
        }).catch(err => {   
        showErrorToast("Error al eliminar el académico.");
        })
      };
    });
  }
  
//Bulk deletion
//Deletion modal for bulk delete
document.getElementById("bulkActionModal").addEventListener("show.bs.modal", function () {
  const selected = getSelectedRows();
  document.getElementById("bulkSelectedCount").textContent =
    selected.length > 0
      ? `Filas seleccionadas: ${selected.length}`
      : "No hay filas seleccionadas.";
});

// Bulk delete logic
document.getElementById("confirmBulkDelete").onclick = function () {
  const selected = getSelectedRows();
    if (selected.length === 0) return;

    const grados = selected.filter(r => r.type === "grado").map(r => r.id);
    const academicos = selected.filter(r => r.type === "academico").map(r => r.id);

    fetch(bulkDeleteUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken
      },
      body: JSON.stringify({ grados, academicos })
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === "success") {
        window.location.reload();
      } else {
        showErrorToast("Error al eliminar seleccionados.");
      }
    })
    .catch(() => showErrorToast("Error al eliminar seleccionados."));
  };

// Handlers
  dt.on('draw', function () {
    attachReviewHandlers();
    attachDeleteHandlers();
  })
  //Document loading
  document.addEventListener("DOMContentLoaded", function() {
    attachReviewHandlers();
    attachDeleteHandlers();
    attachBulkReviewHandler();
  })