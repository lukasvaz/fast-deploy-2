const dropArea = document.getElementById("upload-file-stage-content");
const fileContainer = document.getElementById(
  "upload-file-stage-file-container"
);

const continueButton = document.getElementById("continue-button");

const uploadFileInfoContainer = document.getElementById(
  "upload-file-stage-content"
);
const fieldMappingInfoContainer = document.getElementById(
  "field-mapping-stage-content"
);
const sanitizeDataInfoContainer = document.getElementById(
  "sanitize-stage-content"
);

const firstProgressCircle = document.getElementById("progress-circle-1");
const secondProgressCircle = document.getElementById("progress-circle-2");
const thirdProgressCircle = document.getElementById("progress-circle-3");

const progressCircles = [
  firstProgressCircle,
  secondProgressCircle,
  thirdProgressCircle,
];
const infoContainers = [
  uploadFileInfoContainer,
  fieldMappingInfoContainer,
  sanitizeDataInfoContainer,
];
const errorToast = document.getElementById("error-toast");
const errorToastBody = document.getElementById("toast-body");

const successToast = document.getElementById("success-toast");
const successToastBody = document.getElementById("success-toast-body");

// fetching model fields
const modelFieldsContext = JSON.parse(
  document.getElementById("modelFieldsContext").textContent
);

const urls = {
  grados: {
    sanitize: sanitizeDataUrl,
    loadData: loadDataUrl,
  },
  academicos: {
    sanitize: academicosSanitizeDataUrl,
    loadData: academicosLoadDataUrl,
  },
  instituciones: {
    sanitize: institucionesSanitizeDataUrl, 
    loadData: institucionesLoadDataUrl, 
  },
};

// global variables
let fileElements = document.getElementById("fileElem");
let stagedFile = null;
let fieldMapping = null;
let sanitizedData = null;
let parsedJson = null;
let downloadableData = null;
// section vars
let currentSection = "grados";
let sectionUrls = urls[currentSection];

// define  event handlers and validators
function validateFile(file) {
  const validTypes = [
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ];
  const maxSize = 5 * 1024 * 1024;
  return validTypes.includes(file.type) && file.size <= maxSize;
}

function validateFieldMapping(mapping) {
  return modelFieldsContext[currentSection].required.every(
    (field) => mapping[field] && mapping[field].valid
  );
}
function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  handleFileUpload({ target: { files } });
}
/**
 * Parses a CSV file into a JSON object using PapaParse.
 *
 * @param {File|Blob} file - The CSV file to parse.
 * @param {function(Object):void} callback - Callback function to handle the parsed result.
 *   The callback receives an object with the following structure:
 *     {
 *       header: Array<string>, // Array of header field names
 *       data: Array<Object>    // Array of row objects, each representing a CSV row
 *     }
 *   If parsing fails, header will be an empty array and data will be an empty array.
 *
 * @returns {void}
 */
function parseCsvFileToJson(file, callback) {
  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: function (results) {
      callback({
        header: results.meta.fields || [],
        data: results.data || [],
      });
    },
    error: function (err) {
      console.error("Error parsing CSV:", err);
      callback({ header: [], data: [] });
    },
  });
}
function parseXLSXFileToJson(file, callback) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const data = new Uint8Array(e.target.result);
    const workbook = XLSX.read(data, { type: "array" });
    const sheetName = workbook.SheetNames[0]; 
    const sheet = workbook.Sheets[sheetName];
    const json = XLSX.utils.sheet_to_json(sheet, { header: 1,defval:"" }); // Parse as an array of arrays
    
    // Sanitize header
     const header = json[0].map((h) => {
      if (h === null || h.trim().toLowerCase() === "vacio") {
        return ""; // Replace null or "vacio" with an empty string
      }
      return h.trim();
    });

    // Sanitize data rows
    const dataRows = json.slice(1).map((row) =>
      header.reduce((acc, key, i) => {
        acc[key] = row[i] || ""; // Map header to row values
        return acc;
      }, {})
    );

    callback({
      header: header,
      data: dataRows,
    });
  };
  reader.readAsArrayBuffer(file);
}
function handleFileUpload(e) {
  const files = e.target.files;
  fileContainer.innerHTML = "";
  const file = files[0];
  if (validateFile(file)) {
    //updates global variables
    if (file !== stagedFile) {
      stagedFile = file;
      fieldMapping = null;
      sanitizedData = null;
      parsedJson = null;
    }
    
    renderUploadedFile();
    enableProgressCircles(0) // when back to stage 1
    updateContinueButton(0);
  } else {
    //not valid
    errorToastBody.textContent = `Formato de archivo "${file.name}" no es válido.`;
    toastBootstrap = bootstrap.Toast.getOrCreateInstance(errorToast);
    toastBootstrap.show();
  }
}
dropArea.addEventListener("drop", handleDrop, false);
fileElements.addEventListener("change", handleFileUpload, false);

// Prevent default drag behaviors
function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(eventName, preventDefaults, false);
});

// Styling when dragging files over the drop area
["dragenter", "dragover"].forEach((eventName) => {
  dropArea.addEventListener(
    eventName,
    () => dropArea.classList.add("bg-light"),
    false
  );
});
["dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(
    eventName,
    () => dropArea.classList.remove("bg-light"),
    false
  );
});

async function triggerHeaderMapping() {
  updateCircleStyle(1);
  changeInfoContainer(1);
  renderFieldMappingStage();
  // Get the selected file
  const file = stagedFile;
  if (!file) {
    return;
  }
  
  parsedJson = await new Promise((resolve, reject) => {
    if (file.type === "text/csv") {
      parseCsvFileToJson(file, (parsedData) => {
        if (!parsedData || parsedData.length === 0) {
        reject(new Error("Archivo vacío o inválido"));
      } else {
        resolve(parsedData);
      }
      });
    } else if (
      file.type ===
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ) {
      parseXLSXFileToJson(file, (parsedData) => {
        if (!parsedData || parsedData.length === 0) {
          reject(new Error("Archivo vacío o inválido"));
        } else {
          resolve(parsedData);
        }
      });
    }});
  // Render mapping in the UI
  enableProgressCircles(1);
  renderFieldMappingStage();
  updateContinueButton(1);
}

/* Sanitize data function
    - sends the file and mapping to the server
    - receives sanitized data
    - updates the UI
*/
async function sanitizeData() {
  if (!validateFieldMapping(fieldMapping)) {
    const toastBootstrap = bootstrap.Toast.getOrCreateInstance(errorToast);
    errorToastBody.innerHTML = `Campos obligatorios: <strong>${modelFieldsContext[
      currentSection
    ].required.join(", ")}</strong>`;
    toastBootstrap.show();
    enableInteraction(true);
    return;
  }

  // updating global variable
  updateCircleStyle(2);
  changeInfoContainer(2);
  renderSanitizeDataStage();
  enableInteraction(false);

  const file = stagedFile;
  if (!file) {
    return;
  }
  // Prepare FormData
  const formData = new FormData();
  formData.append("parsedData", JSON.stringify(parsedJson.data));
  const mapping = {};
  // sending just the valid field names
  Object.keys(fieldMapping).forEach((key) => {
    mapping[key] = fieldMapping[key].valid ? fieldMapping[key].field : "";
  });
  formData.append("mapping", JSON.stringify(mapping));
  try {
    const response = await fetch(sectionUrls.sanitize, {
      method: "POST",
      credentials: "same-origin",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrftoken,
      },
    });

    if (!response.ok) {
      throw new Error("Error al enviar datos para sanitización");
    }

    const data = await response.json();
    sanitizedData = data;
    enableInteraction(true);
    enableProgressCircles(2);
    renderSanitizeDataStage();
    updateContinueButton(2);
  } catch (error) {
    sanitizeDataInfoContainer.innerHTML =
      "Ocurrió un error al sanitizar los datos.";
    console.error(error);
  }
}
function selectStage(index) {
  updateCircleStyle(index);
  changeInfoContainer(index);
  updateContinueButton(index);
  if (index === 0) {
    renderUploadedFile();
  }
  if (index === 1) {

    renderFieldMappingStage();
  }
}
function enableProgressCircles(index) {
  progressCircles[index].disabled = false;
  progressCircles
    .filter((_, i) => i > index)
    .forEach((circle) => {
      circle.disabled = true;
    });
}

function enableInteraction(activate) {
  continueButton.disabled = !activate;
  progressCircles.forEach((circle) => {
    circle.disabled = !activate;
  });
}

function updateContinueButton(index) {
  if (index === 0) {
    continueButton.disabled = !stagedFile;
    continueButton.innerText = "Continuar";
    continueButton.onclick = !fieldMapping
    ? triggerHeaderMapping
    : () => {
      selectStage(1);
    };
  } else if (index === 1) {
    continueButton.disabled = !fieldMapping;
    continueButton.innerText = "Sanitizar datos";
    continueButton.onclick = !sanitizedData
    ? sanitizeData
    : () => {
      selectStage(2);
    };
  } else if (index === 2) {
    continueButton.disabled = false;
    continueButton.innerText = "Guardar";
    continueButton.onclick = loadData;
  
  } else if (index === 3) {
    continueButton.disabled = true;
    continueButton.innerText = "Sanitizar datos";
  }
  }


function loadData() {
  if (!sanitizedData || !sanitizedData.valid_entries) {
    return;
  }
  const valid_entries = (sanitizedData.valid_entries || []).map((entry) => {
    // If entry has suggested_value, replace fields with suggested values
    if (entry.suggested_value && typeof entry.suggested_value === "object") {
      return {
        ...entry.data,
        ...entry.suggested_value
      }
    }
    return { 
      ...entry.data ,
    };
  });
  const corrupted_entries = (sanitizedData.corrupted_entries || []).map(entry => entry.data);
  const raw_entries = (sanitizedData.valid_entries|| []).map(entry => entry.data);
  enableInteraction(false);
  fetch(sectionUrls.loadData, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
    body: JSON.stringify({ valid_entries: valid_entries, corrupted_entries: corrupted_entries,raw_entries:raw_entries  }),
  })
    .then((response) => {
      if (!response.ok) throw new Error("Error al cargar los datos");
      return response.json();
    })
    .then((data) => {
      // Show summary modal
      const modalBody = document.getElementById("uploadSummaryModalBody");
      modalBody.innerHTML = `
        <ul class="list-group mb-3">
          <li class="list-group-item d-flex justify-content-between align-items-center">
            <span>Entradas subidas</span>
            <span class="badge bg-success rounded-pill">${data.entries_count}</span>
          </li>
          <li class="list-group-item d-flex justify-content-between align-items-center">
            <span>Entradas duplicadas</span>
            <span class="badge bg-warning rounded-pill">${data.duplicated_count}</span>
          </li>
          <li class="list-group-item d-flex justify-content-between align-items-center">
            <span>Entradas corruptas</span>
            <span class="badge bg-danger rounded-pill">${corrupted_entries.length}</span>
          </li>
        </ul>
      `;
      //set downloadable data
      downloadableData = {
        created_entries: data.created_entries,
        duplicated_entries: data.duplicated_entries,
        corrupted_entries: data.corrupted_entries,
      };
      const summaryModal = new bootstrap.Modal(document.getElementById('uploadSummaryModal'));
      const summaryModalEl = document.getElementById('uploadSummaryModal');
      summaryModal.show();
    })
    .catch((error) => {
      enableInteraction(true);
      const toastBootstrap = bootstrap.Toast.getOrCreateInstance(errorToast);
      errorToastBody.textContent = "Error al cargar los datos.";
      toastBootstrap.show();
      console.error(error);
    }).finally(() => {
        stagedFile = null;
        fieldMapping = null;
        sanitizedData = null;
        parsedJson = null;
        fileElements.value = null;
        selectStage(0);
    })
    
    ;
}
function exportToExcel() {
  if (!downloadableData) return;
  const workbook = XLSX.utils.book_new();
  Object.keys(downloadableData).forEach((key) => {
    const data = downloadableData[key];
    const worksheet = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(workbook, worksheet, key);
  }); 
  XLSX.writeFile(workbook, "resumen_carga_datos.xlsx");
}
function updateCircleStyle(index) {
  const selectedCircle = progressCircles[index];
  selectedCircle.classList.add("btn-danger");
  selectedCircle.classList.remove("btn-secondary");

  progressCircles
    .filter((_, i) => i !== index)
    .forEach((circle) => {
      circle.classList.remove("btn-danger");
      circle.classList.add("btn-secondary");
    });
}

function changeInfoContainer(index) {
  infoContainers[index].style.display = "block";
  infoContainers
    .filter((_, i) => i !== index)
    .forEach((container) => {
      container.style.display = "none";
    });
}
function manualFieldMapping(field, value, valid) {
  if (fieldMapping[field]) {
    fieldMapping[field].field = value;
    fieldMapping[field].valid = valid;
    // updating global variable
    sanitizedData= null;
    updateContinueButton(1);
  }
}
function renderUploadedFile() {
  if (stagedFile) {
    fileContainer.innerHTML = "";
    const item = document.createElement("span");
    item.style.cssText = `
    line-height: 18px;
    `;
    item.textContent = `Archivo seleccionado: ${stagedFile.name}`;
    const checkIcon = document.createElement("span");
    checkIcon.innerHTML = "&#10003;";
    checkIcon.style.cssText = `
    color: green;
    margin-right: 8px;
    display: inline-block;
    border: 1px solid green;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    text-align: center;
    line-height: 18px;
    font-weight: bold;
  `;
    fileContainer.appendChild(checkIcon);
    fileContainer.appendChild(item);
  } else {
    fileContainer.innerHTML = "";
  }
}

/*
Renders the field mapping stage with dropdowns for each model field.
Updates FieldMapping structure based on user selections.

Type definition for fieldMapping:

type FieldMapping = {
  [modelField: string]: {
    field: string; // The matched column name from the uploaded file, or "" if not mapped
    valid: boolean; // true if a valid mapping exists, false otherwise
  }
};
*/

function renderFieldMappingStage() {
let tableTemplate = (headersHtml, bodyHtml) => {
  return `
        <div class="table-responsive" style="max-width:100vw; overflow-x:auto;">
      <table class="table table-bordered mt-3" style="min-width:900px;">
        <thead>
          <tr>
            ${headersHtml}
          </tr>
        </thead>
        <tbody>
          ${bodyHtml}
        </tbody>
      </table>
    </div>
  `;
};
let headerTemplate = (field, idx, fieldDescription,optionsHtml) => {
  const isRequired = modelFieldsContext[currentSection].required.includes(field);
  const isAssigned = fieldMapping[field].valid;
   return `
    <th class="px-3${!isAssigned ? ' text-muted' : ''}" style="white-space:nowrap; position:relative; max-width:100px;">
    
    <div style="">
        <div class="d-flex align-items-center justify-content-center">
        <button 
                  class="border-0 bg-transparent p-0 m-0"
                  data-bs-toggle="tooltip"
                  data-bs-placement="top"
                  data-bs-html="true"
                  title="${fieldDescription}">  
          <span style="font-weight:bold; color:#008080">
            ${field}${isRequired ? ' <span style="color:red">*</span>' : ''}
            ${isAssigned ? '<span style="color:green; font-size:1.2em;">&#10003;</span>' : ''}
            </span>
            </button>
          
          </div>
          </div>
          
          ${
            optionsHtml
            ? `<div class="dropdown mt-1 d-flex justify-content-center" style="min-width:120px;max-width:300px;">
            <button style="max-width:90px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;"
            class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
            ${fieldMapping[field].field || "-- Sin asignar --"}
            </button>
            <ul class="dropdown-menu" data-idx="${idx}">
            ${optionsHtml
            .replace(/<option/g, '<li><a class="dropdown-item"')
            .replace(/<\/option>/g, '</a></li>')
            }
            </ul>
            </div>`
            : ""
      }
      
    </th>
    `;
};
let optionsTemplate = (valid, fields, modelField) => {
  return `
          <option value="" ${
            !valid ? "selected" : ""
          }>-- Sin asignar --</option>
        ${fields
          .map(
            (opt) =>
              `<option value="${opt.replace(/"/g, "&quot;")}"` +
              (fieldMapping[modelField].field === opt &&
              fieldMapping[modelField].valid
                ? " selected"
                : "") +
              `>${opt.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</option>`
          )
          .join("")}
          `;
};

  if (parsedJson) {
    const fileFields = parsedJson.header;
    const modelFields = [
      ...modelFieldsContext[currentSection].required,
      ...modelFieldsContext[currentSection].optional,
    ];

    // Initialize mapping if not present
    if (!fieldMapping) {
      const fieldtags = modelFieldsContext[currentSection].tags;
      fieldMapping = {};
      modelFields.forEach((field) => {
        const tags = fieldtags[field] || [];
        // Try exact match first
        let matched = fileFields.find((f) =>
          tags.some(
            (tag) => f.trim().toLowerCase() === tag.trim().toLowerCase()
          )
        );
        // If no exact match, try partial match (includes)
        if (!matched) {
          matched = fileFields.find((f) =>
            tags.some(
              (tag) =>
                f.trim().toLowerCase().includes(tag.trim().toLowerCase()) ||
                tag.trim().toLowerCase().includes(f.trim().toLowerCase())
            )
          );
        }
        fieldMapping[field] = {
          field: matched || "",
          valid: !!matched,
        };
      });
    }

    // Render top data preview
    const previewRows = parsedJson.data.slice(0, 5);
    const fieldDescriptions = modelFieldsContext[currentSection].field_descriptions
    let theadersHtml = modelFields
      .map((modelField, idx) => {
        let optionsHtml = optionsTemplate(
          fieldMapping[modelField].valid,
          fileFields,
          modelField
        );
        return headerTemplate(modelField, idx,fieldDescriptions[modelField], optionsHtml);
      })
      .join("");
    
    fieldMappingInfoContainer.innerHTML = `
      <div class="mb-3 p-2 bg-light ">
        <span>
          Selecciona a qué columna del archivo corresponde cada campo del modelo. Los campos marcados con <span style="color:red">*</span> son obligatorios y deben ser asignados para continuar.
        </span>
      </div> ${
    tableTemplate(
      theadersHtml,
      previewRows
        .map(
          (row) =>
            `<tr>
              ${modelFields
                .map((field) => {
                  return `<td style="max-width:90px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${
                    row[fieldMapping[field].field] && fieldMapping[field].valid
                      ? String(row[fieldMapping[field].field])
                          .replace(/</g, "&lt;")
                          .replace(/>/g, "&gt;")
                      : ""
                  }</td>`;
                })
                .join("")}
            </tr>`
        )
        .join("")
    )}`;
    // Add event listeners for dropdowns
    const dropdowns =
  fieldMappingInfoContainer.querySelectorAll(".field-dropdown");
  dropdowns.forEach((dropdown, idx) => {
    dropdown.addEventListener("change", (e) => {
      const field = modelFields[idx];
      manualFieldMapping(field, e.target.value, e.target.value !== "");
      renderFieldMappingStage();
    });
  });
    const dropdownMenus = fieldMappingInfoContainer.querySelectorAll(".dropdown-menu");
    dropdownMenus.forEach((menu, idx) => {
      menu.querySelectorAll(".dropdown-item").forEach((item) => {
        item.addEventListener("click", (e) => {
          e.preventDefault();
          const value = item.textContent.trim();
          const field = modelFields[idx];
          manualFieldMapping(field, value, value !== "-- Sin asignar --");
          renderFieldMappingStage();
        });
      });
    });
    var tooltipTriggerList = [].slice.call(fieldMappingInfoContainer.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    return;
  } else {
    fieldMappingInfoContainer.textContent =
      "No se pudo obtener el mapeo de campos.";
  }
}
function renderSanitizeDataStage() {
  sanitizeDataInfoContainer.innerHTML = "";
  if (sanitizedData) {
    const validCount = sanitizedData.valid_entries?.length ?? 0;
    const corruptedCount = sanitizedData.corrupted_entries?.length ?? 0;
    const confirmationCount = sanitizedData.confirmation_entries?.length ?? 0;
    sanitizeDataInfoContainer.innerHTML = `
      <div class="mb-3 p-2">
      ${currentSection !== "instituciones"
        ? `<span>
            Cada entrada debe ser asociada a una institución. El sistema intentará asociar automáticamente cada entrada a una institución existente en la base de datos, basándose en el nombre y país proporcionados.
           </span>`
        : `<span class="text-muted">
            Limpieza de datos completada para instituciones.
           </span>`}
      </div>
      <div class="mt-3 mx-auto" style="max-width:800px;">
        <ul class="nav nav-tabs mb-2" id="entriesTab" role="tablist" style="max-width:820px;">
          <li class="nav-item" role="presentation">
            <button class="nav-link active" id="valid-tab" data-bs-toggle="tab" data-bs-target="#valid-entries" type="button" role="tab" aria-controls="valid-entries" aria-selected="true">
              Entradas válidas (${validCount + confirmationCount})
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link" id="corrupted-tab" data-bs-toggle="tab" data-bs-target="#corrupted-entries" type="button" role="tab" aria-controls="corrupted-entries" aria-selected="false">
              Entradas corruptas (${corruptedCount})
            </button>
          </li>
        </ul>
        <div class="tab-content" id="entriesTabContent" style="max-width:820px;">
          <div class="tab-pane fade show active" id="valid-entries" role="tabpanel" aria-labelledby="valid-tab">
            <div id="validEntriesContainer"></div>
          </div>
          <div class="tab-pane fade" id="corrupted-entries" role="tabpanel" aria-labelledby="corrupted-tab">
            <div id="corruptedEntriesContainer"></div>
          </div>
        </div>
      </div>
    `;
    /**
     * Renders the table for sanitized data entries.
     * @param {Array} entries - The list of entry objects to render. example: [{data: {...}, errors: null, suggested_value: {...}}]
     * @returns {string} HTML string for the table.
     */
    function renderEntryCards(entries) {
      if (!entries || entries.length === 0) {
        return `<em>No hay entradas para mostrar.</em>`;
      }
      return `
          ${entries
            .map((entry, idx) => {
        let mainValueHtml =''
        if (currentSection === "academicos") {
          mainValueHtml = `<div><strong>Nombre:</strong> ${entry.data['nombre']}  ${entry.data['apellido']}</div>`;        
        }
        else if (currentSection === "grados") {
          mainValueHtml = `<div style="max-width:250px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${entry.data['nombre']}</div>`;
        }
        else if (currentSection === "instituciones") {
          mainValueHtml = `<div style="">${entry.data['nombre']} - ${entry.data['pais']}</div>`;
        }
       
      // Universidad y país
      const originalUni = entry.data["universidad"] || "";
      const originalPais = entry.data["pais"] || "";
              
      let matchedHtml = "";
      if (entry.suggested_value && !entry.suggested_value.is_direct) {
        matchedHtml = `
          <div>
            <div class="d-flex align-items-center gap-1">
              <span class="text-muted" >Original:</span>  
              <span style="max-width:350px; display:inline-block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
              ${originalUni} - ${originalPais}
            </span>
            </div>
            <div class="d-flex align-items-center gap-1">
              <span class="text-primary">Sugerido:</span>
              <span style="max-width:350px; display:inline-block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
              ${entry.suggested_value.universidad} - ${entry.suggested_value.pais}
              </span>
            </div>
          </div>
        `;
      }
      else if (entry.suggested_value && entry.suggested_value.is_direct) {
        matchedHtml = `
          <div class="mt-2">
            <div>
              <span class="text-muted">Universidad:</span> ${originalUni} (${originalPais})
            </div>
          </div>
        `;
      }
      else if(entry.errors && entry.errors.some(e => e.universidad)){
        // Error
      if (entry.errors && entry.errors.length > 0 && entry.errors.some(e => e.universidad)) {
        matchedHtml = `
        <div class="d-flex gap-1">
            <span class="text-danger fw-bold">Error:</span>
            <span class="text-danger">${originalUni} - ${originalPais}</span>
        </div>
        `;
      }
    }
      return `
        <div class="card shadow-sm my-1" style="max-width:800px; height: 80px;">
          <div class="card-body d-flex flex-row align-items-center p-3">
            <div class="d-flex align-items-center  gap-3">
              ${mainValueHtml}
              ${matchedHtml ? `<span style="font-size:1.5em;vertical-align:middle;margin:0 12px;">&#8594;</span>` : ""}
              ${matchedHtml}
            </div>
          </div>
        </div>
      `;
    })
              .join("")}
          
        `;
      }
    let currentPage = 1;
    const pageSize = 6;

    function renderPaginatedCards(entries) {
      const totalPages = Math.ceil(entries.length / pageSize);
      const startIdx = (currentPage - 1) * pageSize;
      const endIdx = startIdx + pageSize;
      const pageEntries = entries.slice(startIdx, endIdx);
      let cardsHtml = renderEntryCards(pageEntries);

      // Pagination window logic (show 3 pages at a time)
      let windowSize = 5;
      let windowStart = Math.max(1, currentPage - Math.floor(windowSize / 2));
      let windowEnd = Math.min(totalPages, windowStart + windowSize - 1);
      if (windowEnd - windowStart + 1 < windowSize) {
        windowStart = Math.max(1, windowEnd - windowSize + 1);
      }

      let paginationHtml = `
        <nav>
          <ul class="pagination justify-content-center">
            ${windowStart > 1 ? `<li class="page-item"><a class="page-link" href="#" data-page="${windowStart - 1}">Anterior</a></li>` : ""}
            ${Array.from({ length: windowEnd - windowStart + 1 }, (_, i) => {
              const pageNum = windowStart + i;
              return `<li class="page-item${pageNum === currentPage ? ' active' : ''}"><a class="page-link" href="#" data-page="${pageNum}">${pageNum}</a></li>`;
            }).join('')}
            ${windowEnd < totalPages ? `<li class="page-item"><a class="page-link" href="#" data-page="${windowEnd + 1}">Siguiente</a></li>` : ""}
          </ul>
        </nav>
      `;
      return cardsHtml + paginationHtml;
    }
          
    document.getElementById("validEntriesContainer").innerHTML =
    renderPaginatedCards(sanitizedData.valid_entries || []);
    document.getElementById("corruptedEntriesContainer").innerHTML =
    renderPaginatedCards(sanitizedData.corrupted_entries || []);

    ["validEntriesContainer", "corruptedEntriesContainer"].forEach(containerId => {
  const container = document.getElementById(containerId);
  if (container) {
    container.addEventListener("click", function(e) {
      if (e.target.classList.contains("page-link")) {
        e.preventDefault();
        currentPage = parseInt(e.target.getAttribute("data-page"));
        if (containerId === "validEntriesContainer") {
          container.innerHTML = renderPaginatedCards(sanitizedData.valid_entries || []);
        } else {
          container.innerHTML = renderPaginatedCards(sanitizedData.corrupted_entries || []);
        }
      }
    });
  }
});
    
  } else {
    sanitizeDataInfoContainer.innerHTML = `
      <div class="d-flex justify-content-center align-items-center" style="height: 60px;">
        <div class="spinner-border text-primary" role="status" aria-label="Cargando...">
          <span class="visually-hidden">Cargando...</span>
        </div>
        <span class="ms-2">Procesando datos...</span>
      </div>
    `;
  }
}

function selectSection(section) {
  currentSection = section;
  sectionUrls = urls[section];
  //updating global variables
  stagedFile = null;
  fileElements.value = null;
  fieldMapping = null;
  sanitizedData = null;
  parsedJson = null;
  
  document
    .getElementById("grados-section")
    .classList.toggle("selected", section === "grados");
  document
    .getElementById("academicos-section")
    .classList.toggle("selected", section === "academicos");
    document.getElementById("instituciones-section")
  .classList.toggle("selected", section === "instituciones");

    selectStage(0);

  }

function downloadTemplates() {
  // Define the data for each template
  const templates = {
    grados: [
      { nombre: "Nombre", nombre_es: "Nombre español", tipo: "Grado(MSC,PHD,LIC,TECH)", universidad: "Nombre de la Universidad", pais: "País",fecha_creacion:"fecha_creación" },
    ],
    academicos: [
      { nombre: "Nombre", apellido: "Apellido", universidad: "Nombre de la Universidad", pais: "País", webpage: "Página web", email: "Correo electrónico", orcid_id: "ORCID ID", grado_maximo: "Grado máximo (MSC, PHD, LIC, TECH)" },
    ],
    instituciones: [
      { nombre: "Nombre de la Institución", sigla: "Sigla", pais: "País", webpage: "Página web" },
    ],
  };

  // Create and download each template
  Object.keys(templates).forEach((key) => {
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(templates[key]);
    XLSX.utils.book_append_sheet(workbook, worksheet, key);
    XLSX.writeFile(workbook, `plantilla_${key}.xlsx`);
  });
}

document.getElementById('uploadSummaryModal').addEventListener('hidden.bs.modal', () => {
    location.reload(); // Reload the page
  });

