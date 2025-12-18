const validate_form = () => {
  // Validate by hand (add warnings in case of errors)

  // Inputs
  var inputNombre = document.getElementById("inputNombre");
  var inputNombreFeedback = document.getElementById("input-nombre-feedback");
  var inputSigla = document.getElementById("inputSigla");
  var inputSiglaFeedback = document.getElementById("input-sigla-feedback");
  var inputWebpage = document.getElementById("inputWebpage");
  var inputWebpageFeedback = document.getElementById("input-webpage-feedback");
  var inputPais = document.getElementById("inputPais");
  var inputPaisFeedback = document.getElementById("input-pais-feedback");
  var inputFileEscudo = document.getElementById("inputFileEscudo");
  var inputFileEscudoFeedback = document.getElementById(
    "input-escudo-feedback"
  );
  var inputIDRinggold = document.getElementById("inputIDRinggold");
  var inputIDRinggoldFeedback = document.getElementById(
    "input-ringgold-feedback"
  );
  var inputIDROR = document.getElementById("inputIDROR");
  var inputIDRORFeedback = document.getElementById("input-ror-feedback");
  var inputIDCrossref = document.getElementById("inputIDCrossref");
  var inputIDCrossrefFeedback = document.getElementById(
    "input-crossref-feedback"
  );
  var inputIDWikidata = document.getElementById("inputIDWikidata");
  var inputIDWikidataFeedback = document.getElementById(
    "input-wikidata-feedback"
  );
  var inputIDISNI = document.getElementById("inputIDISNI");
  var inputIDISNIFeedback = document.getElementById("input-isni-feedback");

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
    // inputSigla.classList.add("is-invalid");
    // inputSiglaFeedback.innerText = "Este campo es obligatorio.";
    // is_valid = false;
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
  if (!inputWebpage.value) {
    // inputWebpage.classList.add("is-invalid");
    // inputWebpageFeedback.innerText = "Este campo es obligatorio.";
    // is_valid = false;
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

  if (!is_valid) return;

  // Submit (validate with html attributes)
  const form = document.getElementById("institucion-nueva-form");
  if (form.checkValidity()) {
    form.submit();
  }
};

const remove_feedback = (inputID) => {
  var input = document.getElementById(inputID);
  input.classList.remove("is-invalid");
};

const determinarOpenAlexID = ( ) => {
  const spinner = document.getElementById("spinnerSearchOpenAlex");
  const feedBackBox = document.getElementById("input-openalex-feedback");
  const buttonContent= document.getElementById("openalex-button-text");
  institutionName = document.getElementById("inputNombre").value;
  institutionCountry = document.getElementById("inputPais").value;
  if (!institutionName || institutionName.length < 3) {
    if (spinner) spinner.classList.add("d-none");
    feedBackBox.classList.remove("d-none");
    feedBackBox.style.display = "block";
    feedBackBox.innerText =
      "El nombre de la institución es obligatorio para buscar sugerencias.";
    return;
  }
  spinner.classList.remove("d-none");
  buttonContent.innerHTML = ''
  const url = `${openalexSuggestionsUrl}?Institution_name=${encodeURIComponent(institutionName)}&Insitution_country_code=${encodeURIComponent(institutionCountry)}`;
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
      const select = document.getElementById("openalex-suggestions-select");
      feedBackBox.innerHTML = ""; 
      select.innerHTML = "";
      if (data && data.status === "success" && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
        // Create the select element
        feedBackBox.classList.add("d-none");
        buttonContent.innerHTML = `<i class="bi bi-arrow-clockwise"></i>`;
        select.classList.remove("d-none");
        select.innerHTML = `<option value="0" selected>Seleccione una opción</option>`;
        data.suggestions.forEach(sug => {
          select.innerHTML += `<option value="${sug.openalex_id}">${sug.openalex_display_name} - ${sug.openalex_country_code?sug.openalex_country_code:''} (${sug.openalex_id})</option>`;
        });
        select.onchange = function() {
          document.getElementById("inputOpenAlex").value = this.value;
        };
      } else {   
          buttonContent.innerHTML = `<i class="bi bi-arrow-clockwise"></i>`;
          feedBackBox.innerHTML = 'No se encontraron sugerencias en OpenAlex. <a href="https://openalex.org/institutions" target="_blank" rel="noopener">Buscar manualmente aquí</a>';
          feedBackBox.classList.remove("d-none");
            }
          })
      .catch((error) => {
        if (spinner) spinner.classList.add("d-none");
        console.error("Error fetching OpenAlex suggestions", error);
      });
      };

const  handleOpenAlexNavClick= ()=> {
  var input = document.getElementById('inputOpenAlex');
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

const determinarRORID = () => {
  const spinner = document.getElementById("spinnerSearchROR");
  const feedBackBox = document.getElementById("input-ror-feedback");
  const buttonContent = document.getElementById("ror-button-text");
  const select = document.getElementById("ror-suggestions-select");
  const inputNombre = document.getElementById("inputNombre");
  const inputPais = document.getElementById("inputPais");
  const inputIDROR = document.getElementById("inputIDROR");

  let institutionName = inputNombre.value;
  let institutionCountry = inputPais.value;

  if (!institutionName || institutionName.length < 3) {
    if (spinner) spinner.classList.add("d-none");
    feedBackBox.classList.remove("d-none");
    feedBackBox.style.display = "block";
    feedBackBox.innerText =
      "El nombre de la institución es obligatorio para buscar sugerencias.";
    return;
  }
  if (spinner) spinner.classList.remove("d-none");
  buttonContent.innerHTML = '';
  feedBackBox.classList.add("d-none");
  select.classList.add("d-none");
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
      feedBackBox.innerHTML = "";
      select.innerHTML = "";
      if (data && data.status === "success" && Array.isArray(data.suggestions) && data.suggestions.length > 0) {
        buttonContent.innerHTML = `<i class="bi bi-arrow-clockwise"></i>`;
        select.classList.remove("d-none");
        select.innerHTML = `<option value="0" selected>Seleccione una opción</option>`;
        data.suggestions.forEach(sug => {
          select.innerHTML += `<option value="${sug.ror_id}">${sug.ror_name ? sug.ror_name : ''} - ${sug.ror_country_code ? sug.ror_country_code : ''} (${sug.ror_id})</option>`;
        });
        select.onchange = function() {
          inputIDROR.value = this.value;
        };
      } else {
        buttonContent.innerHTML = `<i class="bi bi-arrow-clockwise"></i>`;
        feedBackBox.innerHTML = 'No se encontraron sugerencias en ROR. <a href="https://ror.org/" target="_blank" rel="noopener">Buscar manualmente aquí</a>';
        feedBackBox.classList.remove("d-none");
      }
    })
    .catch((error) => {
      if (spinner) spinner.classList.add("d-none");
      console.error("Error fetching ROR suggestions", error);
    });
};


// Optional: handle nav click if you want to prevent navigation when empty
function handleRORNavClick() {
  var input = document.getElementById('inputIDROR');
  var link = document.getElementById('ror-nav-icon');
  var id = input.value.trim();
  if (id) {
    link.href = 'https://ror.org/' + id;
    return true;
  } else {
    link.href = '#';
    return false;
  }
}
document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('nueva-modal').addEventListener('shown.bs.modal', function () {
    const inputIDROR = document.getElementById('inputIDROR');
    const link = document.getElementById('ror-nav-icon');
    // Add the input event listener
    inputIDROR.addEventListener('input', function () {
      const id = this.value.trim();
      link.href = id ? 'https://ror.org/' + id : '#';
      link.setAttribute('aria-disabled', id ? 'false' : 'true');
    });
  
    // Update href live as user types
  document.getElementById('inputOpenAlex').addEventListener('input', function() {
    var link = document.getElementById('openalex-nav-icon');
    var id = this.value.trim();
    link.href = id ? 'https://openalex.org/institutions/' + id : '#';
    link.setAttribute('aria-disabled', id ? 'false' : 'true');
  });
  
  });
})