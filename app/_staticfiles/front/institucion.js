UNIDADES = unidades_id.split(",");
UNIDADES.pop();

const chooseInitTab = () => {
  if (UNIDADES) {
    var box_tab = document.getElementById(`unidad-${UNIDADES[0]}-box-tab`);
    var button_tab = document.getElementById(
      `unidad-${UNIDADES[0]}-button-tab`
    );
    box_tab.classList.remove("d-none");
    button_tab.classList.add("selected");
  }
};

const toggletab = (tab) => {
  UNIDADES.forEach((uni) => {
    var box_tab = document.getElementById(`unidad-${uni}-box-tab`);
    var button_tab = document.getElementById(`unidad-${uni}-button-tab`);
    if (uni === tab) {
      box_tab.classList.remove("d-none");
      button_tab.classList.add("selected");
    } else {
      box_tab.classList.add("d-none");
      button_tab.classList.remove("selected");
    }
  });
};

const validate_form_new_unidad = () => {
  // Validate by hand (add warnings in case of errors)

  // Inputs
  var inputNombre = document.getElementById("inputNombre");
  var inputNombreFeedback = document.getElementById("inputNombreFeedback");
  var inputSigla = document.getElementById("inputSigla");
  var inputSiglaFeedback = document.getElementById("inputSiglaFeedback");
  var inputWebpage = document.getElementById("inputWebpage");
  var inputWebpageFeedback = document.getElementById("inputWebpageFeedback");

  // Validate
  var is_valid = true;
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
  if (!inputSigla) {
    if (inputSigla.value.length > 10) {
      inputSigla.classList.add("is-invalid");
      inputSiglaFeedback.innerText =
        "Este campo tiene un largo máximo de 10 caracteres.";
      is_valid = false;
    }
    if (inputSigla.value.length < 1) {
      inputSigla.classList.add("is-invalid");
      inputSiglaFeedback.innerText = "Sigla muy corta.";
      is_valid = false;
    }
  }

  if (!is_valid) return;

  // Submit (validate with html attributes)
  const form = document.getElementById("unidad-nueva-form");
  if (form.checkValidity()) {
    form.submit();
  }
};

const validate_form_update_unidad = (unidadID) => {
  // Validate by hand (add warnings in case of errors)

  // Inputs
  var inputNombre = document.getElementById("inputNombreEdit" + unidadID);
  var inputNombreFeedback = document.getElementById(
    "inputNombreEdit" + unidadID + "Feedback"
  );
  var inputSigla = document.getElementById("inputSiglaEdit" + unidadID);
  var inputSiglaFeedback = document.getElementById(
    "inputSiglaEdit" + unidadID + "Feedback"
  );
  var inputWebpage = document.getElementById("inputWebpageEdit" + unidadID);
  var inputWebpageFeedback = document.getElementById(
    "inputWebpageEdit" + unidadID + "Feedback"
  );

  // Validate
  var is_valid = true;
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
  if (!inputSigla.value) {
    inputSigla.classList.add("is-invalid");
    inputSiglaFeedback.innerText = "Este campo es obligatorio.";
    is_valid = false;
  } else {
    if (inputSigla.value.length > 10) {
      inputSigla.classList.add("is-invalid");
      inputSiglaFeedback.innerText =
        "Este campo tiene un largo máximo de 10 caracteres.";
      is_valid = false;
    }
    if (inputSigla.value.length < 1) {
      inputSigla.classList.add("is-invalid");
      inputSiglaFeedback.innerText = "Sigla muy corta.";
      is_valid = false;
    }
  }

  if (!is_valid) return;

  // Submit (validate with html attributes)
  const form = document.getElementById("unidad-edit-form-" + unidadID);
  if (form.checkValidity()) {
    form.submit();
  }
};

const save_academico_new_ajax = () => {
  // Toast Error
  const toast_error = document.getElementById("toast_error");
  const toastBootstrap_error = bootstrap.Toast.getOrCreateInstance(toast_error);
  const toast_error_msg_box = document.getElementById("toast_error_msg");

  // Toast Spinner
  const toast_spinner = document.getElementById("toast_spinner");
  const toastBootstrap_spinner =
    bootstrap.Toast.getOrCreateInstance(toast_spinner);
  const toast_spinner_msg_box = document.getElementById("toast_spinner_msg");

  toast_spinner_msg_box.innerText = "Guardando académico en base datos.";
  toastBootstrap_spinner.show();

  // Modal
  var modalNuevoAcademico = document.getElementById("nuevoAcademicoModal");
  var modal = bootstrap.Modal.getInstance(modalNuevoAcademico);
  modal.hide();

  var academico_data = {
    nombre: document.getElementById("inputNombreAcademicoNuevo").value,
    institucion_id: document.getElementById("inputInstitucionAcademicoNuevo").value,
    unidad_id: document.getElementById("inputUnidadAcademicoNuevo").value,
    apellido: document.getElementById("inputApellidoAcademicoNuevo").value,
    email: document.getElementById("inputCorreoAcademicoNuevo").value,
    webpage: document.getElementById("inputWebpageAcademicoNuevo").value
  };

  fetch(ajaxUrl2, {
    method: "POST",
    body: JSON.stringify(academico_data),
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      toast_error_msg_box.innerText = "Ha ocurrido un error inesperado.";
      toastBootstrap_error.show();
      toastBootstrap_spinner.hide();
    })
    .then((data) => {
      toastBootstrap_spinner.hide();
      if (data["error"]) {
        toast_error_msg_box.innerText = data["error"];
        toastBootstrap_error.show();
        return;
      }
      setTimeout(function () {
        window.location.reload();
      }, 1500);
    })
    .catch((error) => {
      toastBootstrap_spinner.hide();
      console.error("There was an error", error);
    });
};

const validate_form_academico_new = () => {
  // Validate by hand (add warnings in case of errors)
  // Inputs
  var inputNombre = document.getElementById("inputNombreAcademicoNuevo");
  var inputNombreFeedback = document.getElementById(
    "inputNombreAcademicoNuevoFeedback"
  );
  var inputUnidad = document.getElementById("inputUnidadAcademicoNuevo");
  var inputUnidadFeedback = document.getElementById(
    "inputUnidadAcademicoNuevoFeedback"
  );
  var inputDBLP = document.getElementById("inputDBLPAcademicoNuevo");
  var inputCorreo = document.getElementById("inputCorreoAcademicoNuevo");
  var inputCorreoFeedback = document.getElementById("inputCorreoAcademicoNuevoFeedback");
  var inputWebpage = document.getElementById("inputWebpageAcademicoNuevo");
  var inputWebpageFeedback = document.getElementById("inputWebpageAcademicoNuevoFeedback");
  // Regular expressions
  const emailRegex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
  const urlRegex = /^(https?:\/\/)?([A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,}(?::\d{1,5})?(\/[^\s]*)?$/;


  // Validate
  var is_valid = true;
  // nombre
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
  // unidad
  if (!inputUnidad.value || inputUnidad.value === "0") {
    inputUnidad.classList.add("is-invalid");
    inputUnidadFeedback.innerText = "Este campo es obligatorio.";
    is_valid = false;
  }
  
  // Correo electrónico
  if (inputCorreo.value) {
    if (inputCorreo.value.length > 320) {
      inputCorreo.classList.add("is-invalid");
      inputCorreoFeedback.innerText = "Correo electrónico demasiado largo.";
      is_valid = false;
    } else if (!emailRegex.test(inputCorreo.value)) {
      inputCorreo.classList.add("is-invalid");
      inputCorreoFeedback.innerText = "Formato de correo electrónico inválido.";
      is_valid = false;
    }
  }

  // Página web
  if (inputWebpage.value) {
    if (inputWebpage.value.length > 2000) {
      inputWebpage.classList.add("is-invalid");
      inputWebpageFeedback.innerText = "Sitio web demasiado largo.";
      is_valid = false;
    } else if (!urlRegex.test(inputWebpage.value)) {
      inputWebpage.classList.add("is-invalid");
      inputWebpageFeedback.innerText = "Formato de sitio web inválido. Ej: https://example.com";
      is_valid = false;
    }
  }


  if (!is_valid) return;

  // Submit (validate with html attributes)
  const form = document.getElementById("academico-new-form");
  form.submit();
  
};

const validate_form_institucion_edit = () => {
  // Inputs
  var inputNombre = document.getElementById("inputNombreEditInst");
  var inputNombreFeedback = document.getElementById(
    "input-nombre-feedback-edit-inst"
  );
  var inputSigla = document.getElementById("inputSiglaEditInst");
  var inputSiglaFeedback = document.getElementById(
    "input-sigla-feedback-edit-inst"
  );
  var inputWebpage = document.getElementById("inputWebpageEditInst");
  var inputWebpageFeedback = document.getElementById(
    "input-webpage-feedback-edit-inst"
  );
  var inputPais = document.getElementById("inputPaisEditInst");
  var inputPaisFeedback = document.getElementById(
    "input-pais-feedback-edit-inst"
  );
  var inputFileEscudo = document.getElementById("inputFileEscudo");
  var inputFileEscudoFeedback = document.getElementById(
    "input-escudo-feedback-edit-inst"
  );
  var inputIDRinggold = document.getElementById("inputIDRinggoldEditInst");
  var inputIDRinggoldFeedback = document.getElementById(
    "input-ringgold-feedback-edit-inst"
  );
  var inputIDROR = document.getElementById("inputIDROREditInst");
  var inputIDRORFeedback = document.getElementById(
    "input-ror-feedback-edit-inst"
  );
  var inputIDCrossref = document.getElementById("inputIDCrossrefEditInst");
  var inputIDCrossrefFeedback = document.getElementById(
    "input-crossref-feedback-edit-inst"
  );
  var inputIDWikidata = document.getElementById("inputIDWikidataEditInst");
  var inputIDWikidataFeedback = document.getElementById(
    "input-wikidata-feedback-edit-inst"
  );
  var inputIDISNI = document.getElementById("inputIDISNIEditInst");
  var inputIDISNIFeedback = document.getElementById(
    "input-isni-feedback-edit-inst"
  );
  var inputOpenAlex = document.getElementById("inputOpenAlexEditInst");
  var inputOpenAlexFeedback = document.getElementById("OpenAlexInvalidFeedback");

  // Validate
  var is_valid = true;
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
    if (inputNombre.value.length < 5) {
      inputNombre.classList.add("is-invalid");
      inputNombreFeedback.innerText = "Nombre muy corto.";
      is_valid = false;
    }
  }
  if (!inputSigla.value) {
    inputSigla.classList.add("is-invalid");
    inputSiglaFeedback.innerText = "Este campo es obligatorio.";
    is_valid = false;
  } else {
    if (inputSigla.value.length > 10) {
      inputSigla.classList.add("is-invalid");
      inputSiglaFeedback.innerText =
        "Este campo tiene un largo máximo de 10 caracteres.";
      is_valid = false;
    }
    if (inputSigla.value.length < 1) {
      inputSigla.classList.add("is-invalid");
      inputSiglaFeedback.innerText = "Sigla muy corta.";
      is_valid = false;
    }
  }
  if (inputWebpage.value.length > 200) {
    inputWebpage.classList.add("is-invalid");
    inputWebpageFeedback.innerText = "Este campo tiene un largo de 200 caracteres.";
    is_valid = false;
  }
  if (!inputPais.value || inputPais.value === "0") {
    inputPais.classList.add("is-invalid");
    inputPaisFeedback.innerText = "Este campo es obligatorio.";
    is_valid = false;
  }

  if (inputIDRinggold.value.length > 20) {
    inputIDRinggold.classList.add("is-invalid");
    inputIDRinggoldFeedback.innerText =
      "Este campo tiene un largo máximo de 20 caracteres.";
    is_valid = false;
  }

  if (inputIDROR.value.length > 20) {
    inputIDROR.classList.add("is-invalid");
    inputIDRORFeedback.innerText =
      "Este campo tiene un largo máximo de 20 caracteres.";
    is_valid = false;
  }

  if (inputIDCrossref.value.length > 20) {
    inputIDCrossref.classList.add("is-invalid");
    inputIDCrossrefFeedback.innerText =
      "Este campo tiene un largo máximo de 20 caracteres.";
    is_valid = false;
  }

  if (inputIDWikidata.value.length > 20) {
    inputIDWikidata.classList.add("is-invalid");
    inputIDWikidataFeedback.innerText =
      "Este campo tiene un largo máximo de 20 caracteres.";
    is_valid = false;
  }

  if (inputIDISNI.value.length > 20) {
    inputIDISNI.classList.add("is-invalid");
    inputIDISNIFeedback.innerText =
      "Este campo tiene un largo máximo de 20 caracteres.";
    is_valid = false;
  }
  if (inputOpenAlex.value.length > 20) {
    inputOpenAlex.classList.add("is-invalid");
    inputOpenAlexFeedback.innerText =
      "Este campo tiene un largo máximo de 20 caracteres.";
    is_valid = false;
  }
  if (!is_valid) return;

  // Submit (validate with html attributes)
  const form = document.getElementById("institucion-edit-form");
    form.submit();
};

const remove_feedback = (inputID) => {
  var input = document.getElementById(inputID);
  input.classList.remove("is-invalid");
};

const dblp_by_name = () => {
  var inputNombre = document.getElementById("inputNombreAcademicoNuevo");
  var inputNombreFeedback = document.getElementById(
    "inputNombreAcademicoNuevoFeedback"
  );

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

  const nombre_academico = inputNombre.value;
  // Make request to ETL
  fetch(ajaxUrl1, {
    method: "POST",
    body: JSON.stringify(nombre_academico),
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
  var linkDeterminar = document.getElementById("determinarDBLPlink");
  if (selectDeterminar.value === "0") {
    linkDeterminar.innerText = null;
    linkDeterminar.href = null;
  } else {
    linkDeterminar.innerText = "https://dblp.org/pid/" + selectDeterminar.value;
    linkDeterminar.href = "https://dblp.org/pid/" + selectDeterminar.value;
  }
};

const determinarOpenAlexID = (institucionID) => {
  const spinner = document.getElementById("spinnerSearchOpenAlex");
  const buttonContent= document.getElementById("openalex-button-text");
  const button = document.getElementById("determinarOpenAlexButton");
  const box = document.getElementById("openalex-suggestions-box");
  const feedback_box = document.getElementById("OpenAlexFeedback");
  // when pressing  button
  if (spinner) spinner.classList.remove("d-none");
  buttonContent.innerHTML = ''
  const url = `${openalexSuggestionsUrl}?Institution_name=${encodeURIComponent(document.getElementById("inputNombreEditInst").value)}&Insitution_country_code=${encodeURIComponent(document.getElementById("inputPaisEditInst").value)}`;
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
      if (data && data.status === "success" && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
        // Create the select element
        feedback_box.classList.add("d-none");
        box.classList.remove("d-none");
        buttonContent.innerHTML = `<i class="bi bi-arrow-clockwise"></i>`;
        const select = document.getElementById("openalex-suggestions-select");
        select.innerHTML = `<option value="0" selected>Seleccione una opción</option>`;
        data.suggestions.forEach(sug => {
          select.innerHTML += `<option value="${sug.openalex_id}">${sug.openalex_display_name}- ${sug.openalex_country_code} (${sug.openalex_id})</option>`;
        });
        select.onchange = function() {
          document.getElementById("inputOpenAlexEditInst").value = this.value;
        };
      } else {   
          feedback_box.innerHTML = 'No se encontraron sugerencias en OpenAlex. <a href="https://openalex.org/institutions" target="_blank" rel="noopener">Buscar manualmente aquí</a>';
          feedback_box.classList.remove("d-none");
            }
          })
      .catch((error) => {
        if (spinner) spinner.classList.add("d-none");
        console.error("Error fetching OpenAlex suggestions", error);
      });
      };

const  handleOpenAlexNavClick= ()=> {
  var input = document.getElementById('inputOpenAlexEditInst');
  var link = document.getElementById('openalex-nav-icon');
  var id = input.value.trim();
  if (id) {
    link.href = 'https://openalex.org/institutions/' + id;
    return true; // allow navigation
  } else {
    link.href = '#';
    return false; // prevent navigation
  }
}

// Update href live as user types
var inputOpenAlex = document.getElementById('inputOpenAlexEditInst');
if (inputOpenAlex) {
  inputOpenAlex.addEventListener('input', function() {
    var link = document.getElementById('openalex-nav-icon');
    var id = this.value.trim();
    link.href = id ? 'https://openalex.org/institutions/' + id : '#';
    link.setAttribute('aria-disabled', id ? 'false' : 'true');
  });
}

function determinarRORID() {
  const spinner = document.getElementById("spinnerSearchROR");
  const feedbackBox = document.getElementById("RORFeedback");
  const button = document.getElementById("determinarRORButton");
  const buttonContent= document.getElementById("ror-button-text");
  const selectBox = document.getElementById("ror-suggestions-box");
  const select = document.getElementById("ror-suggestions-select");
  const inputNombre = document.getElementById("inputNombreEditInst");
  const inputPais = document.getElementById("inputPaisEditInst");

  const institutionName = inputNombre.value;
  const institutionCountry = inputPais.value;

  if (spinner) spinner.classList.remove("d-none");
  buttonContent.innerHTML = '';
  feedbackBox.classList.add("d-none");
  selectBox.classList.add("d-none");
  select.innerHTML = "";
  const url = `${rorSuggestionsUrl}?Institution_name=${encodeURIComponent(institutionName)}&Insitution_country_code=${encodeURIComponent(institutionCountry)}`;
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
      if (data && data.status === "success" && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
        buttonContent.innerHTML = `<i class="bi bi-arrow-clockwise"></i>`;
        selectBox.classList.remove("d-none");
        select.innerHTML = `<option value="" selected>Seleccione una opción</option>`;
        data.suggestions.forEach(sug => {
          select.innerHTML += `<option value="${sug.ror_id}">${sug.ror_name ? sug.ror_name : ''} - ${sug.ror_country_code ? sug.ror_country_code : ''} (${sug.ror_id})</option>`;
        });
        select.onchange = function() {
          document.getElementById("inputIDROREditInst").value = this.value;
        };
      } else {
        button.innerHTML = `<i class="bi bi-arrow-clockwise"></i>`;
        feedbackBox.classList.remove("d-none");
        feedbackBox.innerHTML = 'No se encontraron sugerencias en ROR. <a href="https://ror.org/" target="_blank" rel="noopener">Buscar manualmente aquí</a>';
      }
    })
    .catch((error) => {
      if (spinner) spinner.classList.add("d-none");
      button.innerHTML = `<i class="bi bi-arrow-clockwise"></i> Actualizar Sugerencias`;
      feedbackBox.classList.remove("d-none");
      feedbackBox.innerHTML = "Error al buscar sugerencias en ROR.";
      console.error("Error fetching ROR suggestions", error);
    });
}

function handleRORNavClick() {
  var input = document.getElementById('inputIDROREditInst');
  var link = document.getElementById('ror-nav-icon');
  var id = input.value.trim();
  if (id) {
    link.href = 'https://ror.org/' + id;
    return true; // allow navigation
  } else {
    link.href = '#';
    return false; // prevent navigation
  }
}

// Actualiza el link de ROR en vivo
var inputROR = document.getElementById('inputIDROREditInst');
if (inputROR) {
  inputROR.addEventListener('input', function() {
    var link = document.getElementById('ror-nav-icon');
    var id = this.value.trim();
    link.href = id ? 'https://ror.org/' + id : '#';
    link.setAttribute('aria-disabled', id ? 'false' : 'true');
  });
}


// Academicos DataTables
$(document).ready(() => {
  chooseInitTab();
  UNIDADES.forEach((unidad_id) => {
    $(`#table-${unidad_id}`).DataTable({
      language: {
        lengthMenu: "Mostrar _MENU_ registros por página",
        zeroRecords: "No hay datos",
        info: "",
        infoEmpty: "",
        infoFiltered: "(filtrado de _MAX_ registros totales)",
        search: "Buscar:",
        paginate: {
          previous: "Anterior",
          next: "Siguiente",
        },
      },
       dom: "<'row'<'col-12't>>" + // Table
       "<'row'<'col-12 d-flex justify-content-center'p>>"  // Center pagination
    });

     // DataTable para la tabla de grados de cada unidad
    $(`#grados-table-${unidad_id}`).DataTable({
      language: {
        lengthMenu: "Mostrar _MENU_ registros por página",
        zeroRecords: "No hay datos",
        info: "",
        infoEmpty: "",
        infoFiltered: "(filtrado de _MAX_ registros totales)",
        search: "Buscar:",
        paginate: {
          previous: "Anterior",
          next: "Siguiente",
        },
      },
      dom: "<'row'<'col-12't>>" + "<'row'<'col-12 d-flex justify-content-center'p>>"
    });

  });
});
document.addEventListener('DOMContentLoaded', function () {
  // mark current  unidad  as selected
  const nuevoAcademicoModal = document.getElementById('nuevoAcademicoModal');
  nuevoAcademicoModal.addEventListener('shown.bs.modal', function () {
      // Get the currently selected unidad button
      const selectedUnidadButton = document.querySelector('.query-type-selector.selected');
      if (selectedUnidadButton) {
        const unidadId = selectedUnidadButton.id.split('-')[1]; // Extract the unidad ID from the button ID
        const unidadSelect = document.getElementById('inputUnidadAcademicoNuevo');
        if (unidadSelect) {
          // Set the corresponding option as selected
          Array.from(unidadSelect.options).forEach(option => {
            option.selected = option.value === unidadId;
          });
        }
      }
    });
  }
);