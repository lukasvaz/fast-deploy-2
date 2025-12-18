const subAreaView = (id) => {
  // Make invisible every subarea box
  var subareas_box = document.getElementsByClassName("subarea-box");
  for (var i = 0; i < subareas_box.length; i++) {
    subareas_box.item(i).classList.add("d-none");
  }
  var subarea_box = document.getElementById(`subarea-box-${id}`);
  subarea_box.classList.remove("d-none");
};

const toggleArea = (id) => {
  // Update value form
  var input_areas = document.getElementById("InputAreas");
  var areas_selected = input_areas.value.split(";");
  if (areas_selected.includes(id)) {
    areas_selected.splice(areas_selected.indexOf(id), 1);
  } else {
    areas_selected.push(id);
  }
  input_areas.value = areas_selected.join(";");

  // UX
  var area_button_name = document.getElementById(`area-button-name-${id}`);
  var area_button_sign = document.getElementById(`area-button-sign-${id}`);
  area_button_name.classList.toggle("btn-outline-dark");
  area_button_name.classList.toggle("btn-dark");
  area_button_sign.classList.toggle("btn-outline-dark");
  area_button_sign.classList.toggle("btn-dark");
  area_button_sign.innerText = area_button_sign.innerText == "+" ? "-" : "+";

  var area_selected = document.getElementById(`area-selected-${id}`);
  area_selected.classList.toggle("d-none");

  // Reset subareas
  var subareas_buttons = document.getElementsByClassName(
    `subarea-of-area-${id}`
  );
  for (var i = 0; i < subareas_buttons.length; i++) {
    subareas_buttons.item(i).classList.remove("btn-dark");
    subareas_buttons.item(i).classList.add("btn-outline-dark");
  }
  var subareas_selected_buttons = document.getElementsByClassName(
    `subarea-selected-of-area-${id}`
  );
  for (var i = 0; i < subareas_selected_buttons.length; i++) {
    subareas_selected_buttons.item(i).classList.add("d-none");
  }
};
const selectArea= (id)=>{
  // Update value form
  var input_areas = document.getElementById("InputAreas");
  var areas_selected = input_areas.value.split(";");
  // adding area
  if (!areas_selected.includes(id)) {
    areas_selected.push(id);
    input_areas.value = areas_selected.join(";");
    //area button on selection -> dark
    var area_button_name = document.getElementById(`area-button-name-${id}`);
    var area_button_sign = document.getElementById(`area-button-sign-${id}`);
    area_button_name.classList.add("btn-outline-dark");
    area_button_name.classList.add("btn-dark");
    area_button_sign.classList.add("btn-outline-dark");
    area_button_sign.classList.add("btn-dark");
    area_button_sign.innerText = "-";
    // area selected on input container
    var area_selected = document.getElementById(`area-selected-${id}`);
    area_selected.classList.remove("d-none");
  }
}
const deselectArea= (id)=>{ 
  // Update value form
  var input_areas = document.getElementById("InputAreas");
  var areas_selected = input_areas.value.split(";");
  // removing area  
  if (areas_selected.includes(id)) {
    areas_selected.splice(areas_selected.indexOf(id), 1);
    input_areas.value = areas_selected.join(";");
    //area button on selection dark -> normal
    var area_button_name = document.getElementById(`area-button-name-${id}`);
    var area_button_sign = document.getElementById(`area-button-sign-${id}`);
    area_button_name.classList.remove("btn-dark");
    area_button_name.classList.add("btn-outline-dark");
    area_button_sign.classList.remove("btn-dark");
    area_button_sign.classList.add("btn-outline-dark");
    area_button_sign.innerText = "+";
    // area selected on input container -> deselect
    var area_selected = document.getElementById(`area-selected-${id}`);
    area_selected.classList.add("d-none");
  }
}

const toggleSubarea = (area_id, subarea_id) => {
  // Update value form
  var input_subareas = document.getElementById("InputSubareas");
  var subareas_selected = input_subareas.value.split(";");
  // Remove subarea
  if (subareas_selected.includes(subarea_id)) {
    subareas_selected.splice(subareas_selected.indexOf(subarea_id), 1);
  } else { // Add subarea
    subareas_selected.push(subarea_id);
  }
  input_subareas.value = subareas_selected.join(";");
  //button on selection -> dark
  var subarea_button = document.getElementById(`subarea-button-${subarea_id}`);
  subarea_button.classList.toggle("btn-outline-dark");
  subarea_button.classList.toggle("btn-dark");
  var subarea_selected = document.getElementById(
    `subarea-selected-${subarea_id}`
  );
  subarea_selected.classList.toggle("d-none");

  // Check if activating subarea
  if (!subarea_selected.classList.contains("d-none")) {
    // Update slected subareas in form 
    var input_areas = document.getElementById("InputAreas");
    var areas_selected = input_areas.value.split(";");
    if (!areas_selected.includes(area_id)) {
      areas_selected.push(area_id);
    }
    input_areas.value = areas_selected.join(";");
    // UX
    var area_button_name = document.getElementById(
      `area-button-name-${area_id}`
    );
    var area_button_sign = document.getElementById(
      `area-button-sign-${area_id}`
    );
    area_button_name.classList.remove("btn-outline-dark");
    area_button_name.classList.add("btn-dark");
    area_button_sign.classList.remove("btn-outline-dark");
    area_button_sign.classList.add("btn-dark");
    area_button_sign.innerText = "-";

    var area_selected = document.getElementById(`area-selected-${area_id}`);
    area_selected.classList.remove("d-none");
  }
};
const selectSubarea =(area_id,subarea_id)=>{
  // Update value form
  var input_subareas = document.getElementById("InputSubareas");
  var subareas_selected = input_subareas.value.split(";");
  // adding subarea
  if (!subareas_selected.includes(subarea_id)) {
    subareas_selected.push(subarea_id);
    input_subareas.value = subareas_selected.join(";");
    //subareabutton on selection -> dark
    var subarea_button = document.getElementById(`subarea-button-${subarea_id}`);
    subarea_button.classList.add("btn-outline-dark");
    subarea_button.classList.add("btn-dark");
    // selectedsubarea on  input container
    var subarea_selected = document.getElementById(
      `subarea-selected-${subarea_id}`
    );
    subarea_selected.classList.remove("d-none");
    // Check if activating subarea
    var input_areas = document.getElementById("InputAreas");
    var areas_selected = input_areas.value.split(";");
    if (!areas_selected.includes(area_id)) {
      areas_selected.push(area_id);
    }
    // Update areas in form
    input_areas.value = areas_selected.join(";");
    var area_button_name = document.getElementById(
      `area-button-name-${area_id}`
    );
    var area_button_sign = document.getElementById(
      `area-button-sign-${area_id}`
    );
    // area UX
    area_button_name.classList.remove("btn-outline-dark");
    area_button_name.classList.add("btn-dark");
    area_button_sign.classList.remove("btn-outline-dark");
    area_button_sign.classList.add("btn-dark");
    area_button_sign.innerText = "-";
    var area_selected = document.getElementById(`area-selected-${area_id}`);
    area_selected.classList.remove("d-none");
  } 

}

const deselectSubarea =(area_id,subarea_id)=>{
  // Update value form
  var input_subareas = document.getElementById("InputSubareas");
  var subareas_selected = input_subareas.value.split(";");
  // removing subarea
  if (subareas_selected.includes(subarea_id)) {
    subareas_selected.splice(subareas_selected.indexOf(subarea_id), 1);
    input_subareas.value = subareas_selected.join(";");
    //subareabutton on selection dark -> normal
    var subarea_button = document.getElementById(`subarea-button-${subarea_id}`);
    subarea_button.classList.remove("btn-dark");
    subarea_button.classList.add("btn-outline-dark");
    // selectedsubarea on  input container -> deselect
    var subarea_selected = document.getElementById(`subarea-selected-${subarea_id}`);
    subarea_selected.classList.add("d-none");
    // area UX check
    var input_areas = document.getElementById("InputAreas");
    var areas_selected = input_areas.value.split(";");
    input_areas.value = areas_selected.join(";");
    var area_button_name = document.getElementById(`area-button-name-${area_id}`);
    var area_button_sign = document.getElementById(`area-button-sign-${area_id}`);
    
    // if area is empty -> deselect area
    const areaSubareas = document.querySelectorAll(`.subarea-selected-of-area-${area_id}`);
    const hasSubareas = Array.from(areaSubareas).some(
      (subarea) => !subarea.classList.contains("d-none")
    );
    if (!hasSubareas && areas_selected.includes(area_id)) {
      //form buttons
      area_button_name.classList.add("btn-outline-dark");
      area_button_name.classList.remove("btn-dark");
      area_button_sign.classList.add("btn-outline-dark");
      area_button_sign.classList.remove("btn-dark");
      area_button_sign.innerText = "+";
      // input buttons area-selected{}
      var area_selected = document.getElementById(`area-selected-${area_id}`);
      area_selected.classList.add("d-none");
      input_areas.value = areas_selected.filter(a => a !== area_id).join(";");
    }
  
    }
}
const selectOldAreas = () => {
  if (ambitos_areas_old[0] !== "") {
    ambitos_areas_old.forEach((area_id) => {
      toggleArea(area_id);
    });

    ambitos_subareas_old.forEach((subarea_group) => {
      toggleSubarea(subarea_group.split(":")[1], subarea_group.split(":")[0]);
    });
  }
};

const dblp_by_name = () => {
  var inputNombre = document.getElementById("InputNombre");
  var inputNombreFeedback = document.getElementById("inputNombreFeedback");

  if (!inputNombre.value) {
    inputNombre.classList.add("is-invalid");
    inputNombreFeedback.innerText =
      "Este campo es necesario para determinar por nombre.";
    return;
  }

  // Toast Error
  const toast_error = document.getElementById("toast_error");
  const toastBootstrap_error = bootstrap.Toast.getOrCreateInstance(toast_error);
  const toas_error_msg_box = document.getElementById("toast_error_msg");

  // Spinner
  const spinner = document.getElementById("spinnerSearchDBLP");
  spinner.classList.remove("d-none");

  // Button and Select and Link
  var buttonDeterminar = document.getElementById("determinarButton");
  var selectDeterminarBox = document.getElementById(
    "inputDBLPAcademicoNuevoBox"
  );
  var selectDeterminar = document.getElementById("inputDBLPAcademicoNuevo");
  const dblpFeedback = document.getElementById("DblpFeedBack");
  const url= new URL(ajaxUrl1, window.location.origin);
  url.searchParams.append("academicoId", academicoId);
  console
  fetch(url.toString(), {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      toas_error_msg_box.innerText = "Ha ocurrido un error inesperado.";
      toastBootstrap_error.show();
    })
    .then((data) => {
      spinner.classList.add("d-none");
      if (data["error"]) {
        toas_error_msg_box.innerText = data["error"];
        toastBootstrap_error.show();
        return;
      }
      if (data["dblp_cand"].length === 0) {
        dblpFeedback.innerText =
          "No se encontraron candidatos en DBLP para el nombre ingresado.";
        dblpFeedback.classList.remove("d-none");
        return;
      }
      buttonDeterminar.classList.add("d-none");
      selectDeterminarBox.classList.remove("d-none");
      data["dblp_cand"].forEach((cand) => {
        let newOption = new Option(
          cand["nombre"] + " - " + cand["dblp_id"],
          cand["dblp_id"]
        );
        selectDeterminar.add(newOption, undefined);
      });
    })
    .catch((error) => {
      spinner.classList.add("d-none");
      console.error("There was an error", error);
    });
};

const determinarDBLPselectChange = () => {
  const selectDeterminar = document.getElementById("inputDBLPAcademicoNuevo");
  const linkDeterminar = document.getElementById("dblp-nav-icon");
  const inputDblpBox = document.getElementById("InputDblp");

  if (selectDeterminar.value === "0") {
    linkDeterminar.innerText = null;
    linkDeterminar.href = null;
    inputDblpBox.value = null;
  } else {
    const dblpId = selectDeterminar.value;
    linkDeterminar.innerText = "https://dblp.org/pid/" + dblpId;
    linkDeterminar.href = "https://dblp.org/pid/" + dblpId;
    inputDblpBox.value = dblpId; // Update the input field with the selected DBLP ID
  }
};

const changeDBLPmanual = () => {
  var inputDblpBox = document.getElementById("InputDblp");
  var link = document.getElementById("dblp-nav-icon");
  var id= inputDblpBox.value.trim();
  if (id) {
    link.href = 'https://dblp.org/pid/' + id;
    return true; 
  } else {
    link.href = '#';
    return false; 
};
}
const changeOrcidManual = () => { 
  var inputOrcidBox = document.getElementById("InputOrcid");
  var link = document.getElementById("orcid-nav-icon");
  var id= inputOrcidBox.value.trim();
  if (id) {
    link.href = 'https://orcid.org/' + id;
    return true; 
  } else {
    link.href = '#';
    return false; 
};
}
// const changeAminerManual = () => {  
//   var inputAminerBox = document.getElementById("InputAminer");
//   var link = document.getElementById("aminer-nav-icon");
//   var id= inputAminerBox.value.trim();
//   if (id) {
//     link.href = 'https://www.aminer.org/profile/' + id;
//     return true; 
//   } else {
//     link.href = '#';
//     return false; 
// };
// }
const validate_form_academico_new = () => {
  // Spinner
  var spinner = document.getElementById("spinner-button-guardar");
  spinner.classList.remove("d-none");
  // Button
  var button_guardar = document.getElementById("button-guardar");
  button_guardar.disabled = true;
  // Inputs
  var inputNombre = document.getElementById("InputNombre");
  var inputNombreFeedback = document.getElementById("InputNombreFeedback");
  var inputApellido = document.getElementById("InputApellido");
  var inputApellidoFeedback = document.getElementById("InputApellidoFeedback");
  var inputGrado = document.getElementById("InputGrado");
  var inputGradoFeedback = document.getElementById("InputGradoFeedback");
  var inputEmail = document.getElementById("InputEmail");
  var inputEmailFeedback = document.getElementById("InputEmailFeedback");
  var inputWebpage = document.getElementById("InputWeb");
  var inputWebpageFeedback = document.getElementById("InputWebFeedback");
  var inputDBLP = document.getElementById("InputDblp");  
  var inputDBLPFeedback = document.getElementById("InputDblpFeedback"); 
  var inputOpenAlex = document.getElementById("inputOpenAlexEditAcademico");
  var inputOpenAlexFeedback = document.getElementById("InputOpenAlexFeedback");
  var inputOrcid = document.getElementById("InputOrcid");
  var inputOrcidFeedback = document.getElementById("InputOrcidFeedback");
  var inputAminer = document.getElementById("InputAminer");
  var inputAminerFeedback = document.getElementById("InputAminerFeedback");


  // Validate
  var is_valid = true;
  //nombre
  if (!inputNombre.value) {
    inputNombre.classList.add("is-invalid");
    inputNombreFeedback.innerText = "Este campo es obligatorio.";
    is_valid = false;
  } else {
    if (inputNombre.value.length > 200) {
      inputNombre.classList.add("is-invalid");
      inputNombreFeedback.innerText =
        "Este campo tiene un largo máximo de 200 caracteres.";
      is_valid = false;
    }
    if (inputNombre.value.length < 2) {
      inputNombre.classList.add("is-invalid");
      inputNombreFeedback.innerText = "Nombre muy corto.";
      is_valid = false;
    }
  }
  //apellido
  if (inputApellido.value) {
    if (inputApellido.value.length > 200) {
      inputApellido.classList.add("is-invalid");
      inputApellidoFeedback.innerText =
        "Este campo tiene un largo máximo de 200 caracteres.";
      is_valid = false;
    }
    if (inputApellido.value.length < 2) {
      inputApellido.classList.add("is-invalid");
      inputApellidoFeedback.innerText = "Apellido muy corto.";
      is_valid = false;
    }
  }
  // gradomaximo
   if (!["", "PHD", "MSC", "LIC", "BACH", "TECH"].includes(inputGrado.value)) {
    is_valid = false;
    inputGrado.classList.add("is-invalid");
    inputGradoFeedback.innerText = "Grado académico inválido.";
}
  //correo electronico
  if (inputEmail.value) {
      var email = inputEmail.value.trim();
      // Simple, practical email regex (local@domain.tld)
      var emailRegex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
      if (email.length > 320) {
        inputEmail.classList.add("is-invalid");
        if (inputEmailFeedback) inputEmailFeedback.innerText = "Correo electrónico demasiado largo.";
        is_valid = false;
      } else if (!emailRegex.test(email)) {
        inputEmail.classList.add("is-invalid");
        if (inputEmailFeedback) inputEmailFeedback.innerText = "Formato de correo electrónico inválido.";
        is_valid = false;
      }
    }
  //webpage
  if (inputWebpage.value) {
    var webpage = inputWebpage.value.trim();
    // Practical URL regex: optional http(s), domain with labels, optional port and path/query/fragment
    var urlRegex = /^(https?:\/\/)?([A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,}(?::\d{1,5})?(\/[^\s]*)?$/;
    if (webpage.length > 2000) {
      inputWebpage.classList.add("is-invalid");
      if (inputWebpageFeedback) inputWebpageFeedback.innerText = "Sitio web demasiado largo.";
      is_valid = false;
    } else if (!urlRegex.test(webpage)) {
      inputWebpage.classList.add("is-invalid");
      if (inputWebpageFeedback) inputWebpageFeedback.innerText = "Formato de sitio web inválido. Ej: https://example.com";
      is_valid = false;
    }
  }
  //dblp
  if (inputDBLP.value) {
    var dblp = inputDBLP.value.trim();
    // Examples: 123/456, abc/123, johndoe/001, a/b123, 12/ab
    var dblpRegex = /^[A-Za-z0-9]+\/[A-Za-z0-9]+$/;
    
    if (dblp.length > 100) {  
        inputDBLP.classList.add("is-invalid");
        if (inputDBLPFeedback) inputDBLPFeedback.innerText = "DBLP ID demasiado largo.";
        is_valid = false;
    } else if (!dblpRegex.test(dblp)) {
        inputDBLP.classList.add("is-invalid");
        if (inputDBLPFeedback) inputDBLPFeedback.innerText = "Formato de DBLP ID inválido. Ej: 123/456 o autor/001";
        is_valid = false;
    }
}
//openalex
if (inputOpenAlex.value) {
    var openalexId = inputOpenAlex.value.trim();
    //5-20 characters
    var openalexRegex = /^[A-Za-z0-9]{5,20}$/;   
    if (!openalexRegex.test(openalexId)) {
        inputOpenAlex.classList.add("is-invalid");
        if (inputOpenAlexFeedback) inputOpenAlexFeedback.innerText = "OpenAlex ID debe ser alfanumérico con 5-20 caracteres. Ej: A1234567890";
        is_valid = false;
    }
}
//orcid

if (inputOrcid.value) {
    var orcidId = inputOrcid.value.trim();
    // Example: 0000-0002-1825-0097
    var orcidRegex = /^[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}$/;
    
    if (!orcidRegex.test(orcidId)) {
        inputOrcid.classList.add("is-invalid");
        if (inputOrcidFeedback) inputOrcidFeedback.innerText = "ORCID ID debe tener formato 0000-0000-0000-0000. Ej: 0000-0002-1825-0097";
        is_valid = false;
    }
}

//aminer
if (inputAminer.value) {
    var aminerId = inputAminer.value.trim();
    if (aminerId.length > 50) {  
        inputAminer.classList.add("is-invalid");
        if (inputAminerFeedback) inputAminerFeedback.innerText = "AMiner ID demasiado largo.";
        is_valid = false;
    }
    if (aminerId.length < 10){
        inputAminer.classList.add("is-invalid");
        if (inputAminerFeedback) inputAminerFeedback.innerText = "AMiner ID demasiado corto.";
        is_valid = false;
    }
  }
  
  if (!is_valid) {
    spinner.classList.add("d-none");
    button_guardar.disabled = false;
    return;
  }

  // Submit (validate with html attributes)
  const form = document.getElementById("academico-edit-form");
  if (form.checkValidity()) {
    form.submit();
  }
};

const remove_feedback = (inputID) => {
  var input = document.getElementById(inputID);
  input.classList.remove("is-invalid");
};
function determinarOpenAlexIDAcademico(academicoID) {
  const spinner = document.getElementById("spinnerSearchOpenAlexAcademico");
  const button = document.getElementById("determinarOpenAlexButtonAcademico");
  if (spinner) spinner.classList.remove("d-none");
  const url = `${openalexSuggestionsUrl}?academicoId=${encodeURIComponent(academicoID)}`;
  fetch(url, {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
  })
    .then((response) => response.ok ? response.json() : null)
    .then((data) => {
      if (spinner) spinner.classList.add("d-none");
      const box = document.getElementById("openalex-suggestions-box-academico");
      const openalexFeedBack= document.getElementById("OpenAlexFeedBack");
      if (data && data.status === "success" && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
        openalexFeedBack.classList.add("d-none");
        button.classList.add("d-none");
        box.classList.remove("d-none");
        const select = document.getElementById("openalex-suggestions-select-academico");
        select.innerHTML = `<option value="0" selected>Seleccione una opción</option>`;
        data.suggestions.forEach(sug => {
          select.innerHTML += `<option value="${sug.openalex_id}">${sug.openalex_display_name} -(${sug.openalex_id})</option>`;
        });
        select.onchange = function() {
          document.getElementById("inputOpenAlexEditAcademico").value = this.value;
        };
      } else {
        openalexFeedBack.classList.remove("d-none");
        openalexFeedBack.innerHTML = 'No se encontraron sugerencias en OpenAlex. <a href="https://openalex.org/authors" target="_blank" rel="noopener">Buscar manualmente aquí</a>';
      }
    })
    .catch((error) => {
      if (spinner) spinner.classList.add("d-none");
      console.error("Error fetching OpenAlex suggestions", error);
    });
}
const handleOpenAlexNavClick = () => {
  var input = document.getElementById('inputOpenAlexEditAcademico');
  var link = document.getElementById('openalex-nav-icon');
  var id = input.value.trim();
  if (id) {
    link.href = 'https://openalex.org/authors/' + id;
    return true; // allow navigation
  } else {
    link.href = '#';
    return false; // prevent navigation
  }
}
window.onload = () => {
  selectOldAreas();
};

// Unidad Edit
// let selectedUnidad = null;
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
        if (String(u.id) === String(initialUnidadId)) option.selected = true;
        unidadDropdown.appendChild(option);
    }
    }
}
}

// Error toast function (same as revision.js)
function showErrorToast(message) {
  const toastBody = document.getElementById("errorToastBody");
  if (toastBody) {
    toastBody.textContent = message;
    const toastEl = document.getElementById("errorToast");
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
  } else {
    // Fallback if toast doesn't exist
    alert(message);
  }
}

let suggestionsApplied=false;
const toggleOpenAlexSubareasSuggestions = () => {
  const openalexSubareasIDs = JSON.parse(document.getElementById("openalex_ambitos_suggestion").textContent);
  const inputSubareas = document.getElementById("InputSubareas");
  const currentSubareas = inputSubareas.value ? inputSubareas.value.split(";") : [];
  const inputAreas = document.getElementById("InputAreas");
  const currentAreas = inputAreas.value ? inputAreas.value.split(";") : [];
  // Toggle suggestions
  if (suggestionsApplied) {
    // Remove OpenAlex suggestions
    for (const areaId in openalexSubareasIDs) {
      const subareasList = openalexSubareasIDs[areaId];
      subareasList.forEach((subareaId) => {
        if (currentSubareas.includes(subareaId.toString())) {
          deselectSubarea(areaId, subareaId.toString());
        }
      deselectArea(areaId); 
      });
    }
    suggestionsApplied = false;
  } else {
    // Add OpenAlex suggestions
    for (const areaId in openalexSubareasIDs) {
      const subareasList = openalexSubareasIDs[areaId];
      subareasList.forEach((subareaId) => {
        if (!currentSubareas.includes(subareaId.toString())) {
          selectSubarea(areaId, subareaId.toString());
        }
      });
    }

    suggestionsApplied = true;
  }
};
document.addEventListener("DOMContentLoaded", function() {
  updateUnidadesDropdown();
  //select 2 
  $('#InputUnidad').select2({
    width: '100%',
    placeholder: 'Seleccione una unidad académica',
    allowClear: true
  });  
  $('#InputPais').select2({
    width: '100%',
    placeholder: 'Seleccione un país',
    allowClear: true
  });
}); 