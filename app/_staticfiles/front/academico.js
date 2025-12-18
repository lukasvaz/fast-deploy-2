const generar_link = () => {
  // Toast Error
  const toast_error = document.getElementById("toast_error");
  const toastBootstrap_error = bootstrap.Toast.getOrCreateInstance(toast_error);

  const generar_button = document.getElementById("select_generar");
  generar_button.disabled = true;
  generar_button.classList.add("d-none");
  const academico_link_1 = document.getElementById("select_link_1");
  const academico_link_2 = document.getElementById("select_link_2");
  const academico_valid = document.getElementById("select_valid");

  // Create request
  // Make query
  fetch(ajax_url, {
    method: "POST",
    body: JSON.stringify(academico_id),
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
    })
    .then((data) => {
      const new_url = host_ajax + data.url;
      academico_link_1.value = new_url;
      academico_link_2.value = new_url;
      if (navigator.clipboard) {
        academico_valid.classList.remove("d-none");
      } else {
        academico_link_2.classList.remove("d-none");
      }
    })
    .catch((error) => {
      console.error("There was an error", error);
    });
};

const copy_link = () => {
  const copy_text = document.getElementById("select_link_1").value;
  navigator.clipboard
    .writeText(copy_text)
    .then(() => {
      console.log("successfully copied");
    })
    .catch(() => {
      console.error("something went wrong");
    });
};

let template = null;
$(".modal").on("show.bs.modal", function (event) {
  template = $(this).html();
});

$(".modal").on("hidden.bs.modal", function (e) {
  $(this).html(template);
});

  

// assignign  colors 
document.addEventListener("DOMContentLoaded", function () {
  const AREA_COLORS = {
    "Aplicaciones de Informática": "bg-success",
    "Hardware y Arquitectura": "bg-danger",
    "Interacción Humano-Computadora": "bg-warning",
    "Procesamiento de señales": "bg-info",
    "Inteligencia artificial": "bg-primary",
    "Redes de Computadoras y Comunicaciones": "bg-success",
    "Computación Grafica y Diseño Asistido por Computadora": "bg-danger",
    "Visión por Computador y Reconocimiento de Patrones": "bg-warning",
    "Software": "bg-info",
    "Teoría Computacional y Matemáticas": "bg-primary",
    "Sistemas de Información": "bg-success",
  };
  const DEFAULT_COLOR = "bg-secondary"; // Bootstrap secondary color
  document.querySelectorAll(".area-badge, .subarea-badge").forEach(el => {
    const areaName = el.dataset.area?.trim() || "";
    const color =   DEFAULT_COLOR;
    el.classList.add(color);
    
  });
})
