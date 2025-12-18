const placeHolderAcademico = `
<div class="col">
  <div class="card" aria-hidden="true">
    <div class="card-body">
      <h5 class="card-title placeholder-glow">
        <span class="placeholder col-6"></span>
      </h5>
      <hr>
      <p class="card-text placeholder-glow">
        <span class="placeholder col-12"></span>
      </p>
      <select class="placeholder form-select form-select-sm mb-1"></select>
      <p class="card-text placeholder-glow">
        <span class="placeholder col-6"></span>
      </p>
      <a class="btn btn-secondary disabled placeholder col-3"></a>
    </div>
  </div>
</div>
`;

const onChangeDblpLink = (id) => {
  const new_dblp = document.getElementById("selectAcademico-" + id).value;
  var dblplink = document.getElementById("dblplink-" + id);
  if (new_dblp) {
    dblplink.innerHTML = `dblp.org/pid/${new_dblp}`;
    dblplink.href = `https://dblp.org/pid/${new_dblp}`;
  } else {
    dblplink.innerHTML = ``;
    dblplink.href = ``;
  }
};

const AcademicoBoxGen = (nombre, inv_cand_id, candidatos) => {
  const AcademicoHtml_a = `
  <div class="col">
    <div class="card" id="candidato-${inv_cand_id}" style="height: 100%;">
      <div class=" card-body ">
        <h5 class="card-title"><span id="nombreCandidatoHeader-${inv_cand_id}" class="nombreAcademicoSelect">${nombre}<span> <span id="simbolCandidato-${inv_cand_id}">${
    candidatos.length > 0
      ?  `<i class="bi bi-check-circle-fill text-success"></i>`
      : `<i class="bi bi-question-circle-fill text-secondary-emphasis"></i>`
  }</span></h5>
        <hr />
        <label for="selectAcademico" class="form-label"
          >Resultados de búsqueda.</label
        >
        <select
          class="form-select form-select-sm mb-1 academicoSelect d-none"
          id="selectAcademico-${inv_cand_id}"
          aria-label=".form-select-sm example"
          onchange="onChangeDblpLink('${inv_cand_id}')"
          ${candidatos.length === 1 ? "disabled" : ""}
        >
        <option></option>
  `;
  var AcademicoHtml_options = "";
  if (candidatos.length === 1) {
    AcademicoHtml_options = `<option value="${candidatos[0].dblp_id}" selected>${candidatos[0].dblp_id}</option>`;
  } else {
    candidatos.forEach(
      (candidato, idx) =>
        (AcademicoHtml_options =
          AcademicoHtml_options +
          `<option value="${candidato.dblp_id}">${candidato.dblp_id}</option>`)
    );
  }

  const AcademicoHtml_b = `
        </select>
        <div class="mb-3">
        <div class="d-flex flex-column gap-1"> 
        ${
          candidatos
            .map(
              (candidato) =>
              
                `<a id="dblplink-${inv_cand_id}" href="https://dblp.org/pid/${candidato.dblp_id}" target="_blank">dblp.org/pid/${candidato.dblp_id}</a>`
            )
            .join("")
        }
        </div>
</div>
      </div>
      <div class="card-footer bg-transparent">
        <button id="omitirbutton-${inv_cand_id}" type="button" class="btn btn-secondary omitirButton" onclick="omitirAcademico(${inv_cand_id})" >Omitir</button>
      </div>
    </div>
  </div>
  `;

  return AcademicoHtml_a + AcademicoHtml_options + AcademicoHtml_b;
};

const spinner =
  '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>';

const limpiarBusqueda = () => {};

const omitirAcademico = (id) => {
  const id_buttton = `omitirbutton-${id}`;
  const id_nombre = `nombreCandidatoHeader-${id}`;
  const id_simbolo = `simbolCandidato-${id}`;
  const id_box = `candidato-${id}`;
  var button = document.getElementById(id_buttton);
  var nombre = document.getElementById(id_nombre);
  var simbolo = document.getElementById(id_simbolo);
  var box = document.getElementById(id_box);
  button.classList.toggle("btn-secondary");
  button.classList.toggle("btn-light");
  if (button.innerText === "Omitir") {
    button.innerText = "Agregar";
    nombre.style = "text-decoration-line: line-through;";
    simbolo.style = "display: none;";
    box.classList.add("text-bg-secondary");
  } else {
    button.innerText = "Omitir";
    nombre.style = "";
    simbolo.style = "";
    box.classList.remove("text-bg-secondary");
  }
};

const matchacademicwebtodblp = (id_universidad) => {
  // Disable button and add spinner
  const id_buttton = `buttonBuscarAcademico`;
  var button = document.getElementById(id_buttton);
  button.disabled = true;
  const button_original = button.innerHTML;
  button.innerHTML = spinner + button_original;

  // Toast Error
  const toast_error = document.getElementById("toast_error");
  const toastBootstrap_error = bootstrap.Toast.getOrCreateInstance(toast_error);

  // Space work
  const id_space_box = `space-work`;
  var space_box = document.getElementById(id_space_box);

  // Space link
  const id_space_links = `space-links`;
  var space_links = document.getElementById(id_space_links);
  space_links.classList.add("pe-none");

  // Academicos Boxes
  const id_academicos_boxes = `academicos-boxes`;
  var academicos_boxes = document.getElementById(id_academicos_boxes);

  // Progess bar - circle
  const id_progress_bar = "progress-bar";
  var progress_bar = document.getElementById(id_progress_bar);
  progress_bar.style = "width: 50%";
  const id_progerss_circle_2 = "progress-circle-2";
  var progress_circle_2 = document.getElementById(id_progerss_circle_2);

  // Toast
  const toast_1 = document.getElementById("toast_1");
  const toastBootstrap_1 = bootstrap.Toast.getOrCreateInstance(toast_1);
  toastBootstrap_1.show();

  // Make query
  fetch(ajaxUrl1, {
    method: "POST",
    body: JSON.stringify(id_universidad),
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      console.error("Something went wrong");
      toastBootstrap_error.show();
      toastBootstrap_1.hide();
    })
    .then((data) => {
      toastBootstrap_1.hide();
      button.innerHTML = button_original;
      var result = "";

      data["result"].forEach(
        (element) =>
          (result =
            result +
            AcademicoBoxGen(
              element["nombre"],
              element["investigador_candidato_id"],
              element["investigadores_candidatos"]
            ))
      );
      const id_tittle = `tittle-step`;
      var tittle = document.getElementById(id_tittle);
      tittle.innerText = "2.- Seleccionar académicos encontrados.";
      space_box.innerHTML = "";
      academicos_boxes.innerHTML = result;
      progress_circle_2.classList.remove("btn-secondary");
      progress_circle_2.classList.add("btn-danger");
  
    // Progess bar - circle
    const id_progress_bar = "progress-bar";
    var progress_bar = document.getElementById(id_progress_bar);
    progress_bar.style = "width: 90%";

    // Save button
    const id_save_button = "save-button";
    var save_button = document.getElementById(id_save_button);
    save_button.classList.remove("d-none");
        // Stop yellow spinner
        var yellowSpinners = document.getElementsByClassName("stoperclass");
        [].forEach.call(yellowSpinners, (yspinner) => {
          yspinner.innerHTML = `<i class="bi bi-exclamation-triangle-fill text-warning"></i>`;
        });

        // Allow Omitir
        var omitirButtons = document.getElementsByClassName("omitirButton");
        [].forEach.call(omitirButtons, (omitirButton) => {
          omitirButton.disabled = false;
        });
        //Omit all emmpty candidatos
        var selectAcademicos = document.getElementsByClassName("academicoSelect");
        [].forEach.call(selectAcademicos, (selectAcademico) => {
          if (selectAcademico.options.length === 1) {
            const idbox = selectAcademico.id.slice("selectAcademico-".length);
            const id_button = `omitirbutton-${idbox}`;
            omitirAcademico(idbox);
          }
        });

        // Progress bar full
        progress_bar.style = "width: 100%";

        // Allow save
        save_button.disabled = false;
      })
      .catch((error) => {
        console.error("There was an error", error);
      });
};
// DEPRECATED: global crontab will handle deambiguation for each  external source
const matchbycoauthor = (data, id_universidad) => {
  const data_2 = { data: data, universidad: id_universidad };
  // Remake query for uncomplete authors

  // Toast loading
  const toast_2 = document.getElementById("toast_2");
  const toastBootstrap_2 = bootstrap.Toast.getOrCreateInstance(toast_2);
  toastBootstrap_2.show();
  // Toast Error
  const toast_error = document.getElementById("toast_error");
  const toastBootstrap_error = bootstrap.Toast.getOrCreateInstance(toast_error);

  // Progess bar - circle
  const id_progress_bar = "progress-bar";
  var progress_bar = document.getElementById(id_progress_bar);
  progress_bar.style = "width: 90%";

  // Save button
  const id_save_button = "save-button";
  var save_button = document.getElementById(id_save_button);
  save_button.classList.remove("d-none");

  fetch(ajaxUrl2, {
    method: "POST",
    body: JSON.stringify(data_2),
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      console.error("Something went wrong");
      toastBootstrap_error.show();
      toastBootstrap_2.hide();
    })
    .then((data_3) => {
      toastBootstrap_2.hide();
      const results = data_3["resolution"];

      results.forEach((result) => {
        if (result.length === 1) {
          const selectAcademicoId = "selectAcademico-" + result[0][0];
          var selectAcademico = document.getElementById(selectAcademicoId);
          selectAcademico.value = result[0][1];
          selectAcademico.disabled = true;

          const simbolCandidatoId = "simbolCandidato-" + result[0][0];
          var simbolCandidato = document.getElementById(simbolCandidatoId);
          simbolCandidato.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i>`;

          const urlCandidatoId = "dblplink-" + result[0][0];
          var urlCandidato = document.getElementById(urlCandidatoId);
          urlCandidato.innerHTML = `dblp.org/pid/${result[0][1]}`;
          urlCandidato.href = `https://dblp.org/pid/${result[0][1]}`;
        }
      });

      // Stop yellow spinner
      var yellowSpinners = document.getElementsByClassName("stoperclass");
      [].forEach.call(yellowSpinners, (yspinner) => {
        yspinner.innerHTML = `<i class="bi bi-exclamation-triangle-fill text-warning"></i>`;
      });

      // Allow Omitir
      var omitirButtons = document.getElementsByClassName("omitirButton");
      [].forEach.call(omitirButtons, (omitirButton) => {
        omitirButton.disabled = false;
      });

      // Progress bar full
      progress_bar.style = "width: 100%";

      // Allow save
      save_button.disabled = false;
    })
    .catch((error) => {
      console.error("There was an error", error);
    });
};

const saveacademicosbatch = (id_universidad) => {
  // Toast
  const toast_error = document.getElementById("toast_error");
  const toastBootstrap_error = bootstrap.Toast.getOrCreateInstance(toast_error);
  const toast_4 = document.getElementById("toast_4");
  const toast_4_msg = document.getElementById("toast_4_msg");
  const toastBootstrap_4 = bootstrap.Toast.getOrCreateInstance(toast_4);
  toastBootstrap_4.show();

  const toast_5 = document.getElementById("toast_5");
  const toastBootstrap_5 = bootstrap.Toast.getOrCreateInstance(toast_5);

  // Save button
  const id_save_button = "save-button";
  var save_button = document.getElementById(id_save_button);
  save_button.disabled = true;

  // Progess bar - circle
  const id_progerss_circle_3 = "progress-circle-3";
  var progress_circle_3 = document.getElementById(id_progerss_circle_3);
  progress_circle_3.classList.remove("btn-secondary");
  progress_circle_3.classList.add("btn-danger");

  // Take select data confirmed
  var result = { universidad: id_universidad, academicos: [] };
  const academicos_nombres_class = `nombreAcademicoSelect`;
  const academicos_select_class = `academicoSelect`;
  const academicos_nombres = document.getElementsByClassName(
    academicos_nombres_class
  );
  const academicos_select = document.getElementsByClassName(
    academicos_select_class
  );
  // TODO:
  // if (academicos_nombres.length !== academicos_select) {
  //   error()
  // }
  [].forEach.call(academicos_select, (select, idx) => {
    // To check if "omitido", read text in button
    const idbox = select.id.slice("selectAcademico-".length);
    const id_button = `omitirbutton-${idbox}`;
    var button = document.getElementById(id_button);
    if (button.innerText === "Omitir") {
      result.academicos.push({
        nombre: academicos_nombres[idx].innerText,
        dblp_id: select.value,
      });
    }
  });
  var listos = 0;

  result.academicos.forEach((academico, idx) => {
    var academico_data = {
      nombre: academico.nombre,
      institucion_id: result.universidad,
      unidad_id: "0",
      dblp_id: academico.dblp_id,
    };

    fetch(ajaxUrl3, {
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
        console.error("Something went wrong");
        toastBootstrap_4.hide();
        toastBootstrap_error.show();
      })
      .then((_) => {
        listos += 1;
        toast_4_msg.innerText = `Guardando (${listos}/${result.academicos.length}) académicos en la base de datos.`;
        const acamdemicos_box_id = `academicos-boxes`;
        var acamdemicos_box = document.getElementById(acamdemicos_box_id);
        acamdemicos_box = ``;
        if (listos === result.academicos.length) {
          setTimeout(function () {
            window.location.href = urlUni;
          }, 5000);
        }
      })
      .catch((error) => {
        console.error("There was an error", error);
      });
  });
};



