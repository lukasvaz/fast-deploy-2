const eliminarAcademicoModal = document.getElementById(
  "eleminarAcademicoModal"
);
if (eliminarAcademicoModal) {
  eliminarAcademicoModal.addEventListener("show.bs.modal", (event) => {
    // Button that triggered the modal
    const button = event.relatedTarget;
    // Extract info from data-bs-* attributes
    const academico_id = button.getAttribute("data-bs-id");
    const academico_nombre = button.getAttribute("data-bs-nombre");
    const academico_unidad_id = button.getAttribute("data-bs-unidad");

    // Update the modal's content.
    const modalTitle = eliminarAcademicoModal.querySelector(".modal-title");
    const modalText = eliminarAcademicoModal.querySelector(".modal-body-text");

    modalTitle.textContent = `Eliminar academico ${academico_nombre}`;
    modalText.textContent = `¿Estás seguro de eliminar al academico ${academico_nombre}?`;
    var delete_button = document.getElementById("deleteAcademicoButton");
    delete_button.href += `?id=${academico_id}&unidad=${academico_unidad_id}`;
  });
}

const cambiarUnidadAcademicoModal = document.getElementById(
  "cambiarUnidadAcademicoModal"
);
if (cambiarUnidadAcademicoModal) {
  cambiarUnidadAcademicoModal.addEventListener("show.bs.modal", (event) => {
    // Button that triggered the modal
    const button = event.relatedTarget;
    // Extract info from data-bs-* attributes
    const academico_id = button.getAttribute("data-bs-id");
    const academico_nombre = button.getAttribute("data-bs-nombre");
    const academico_unidad_id = button.getAttribute("data-bs-unidad");

    // Update the modal's content.
    const modalTitle =
      cambiarUnidadAcademicoModal.querySelector(".modal-title");

    // Change form values
    var inputAcademicoID = document.getElementById(
      "inputAcademicoChangeUnidad"
    );
    inputAcademicoID.value = academico_id;
    var inputUnidadOld = document.getElementById(
      "inputUnidadOldAcademicoChangeUnidad"
    );
    inputUnidadOld.value = academico_unidad_id;

    modalTitle.textContent = `Cambiar Unidad académico ${academico_nombre}`;
  });
}

const validate_form_academico_cambiar_unidad = () => {
  // Inputs
  var inputUnidadOld = document.getElementById(
    "inputUnidadOldAcademicoChangeUnidad"
  );
  var inputUnidadNew = document.getElementById(
    "inputUnidadNewAcademicoChangeUnidad"
  );
  var inputUnidadNewFeedback = document.getElementById(
    "inputUnidadNewFeedback"
  );

  // Validate
  var is_valid = true;
  if (!inputUnidadNew.value || inputUnidadNew.value === "0") {
    inputUnidadNew.classList.add("is-invalid");
    inputUnidadNewFeedback.innerText = "Este campo es obligatorio.";
    is_valid = false;
  }

  if (inputUnidadOld.value == inputUnidadNew.value) {
    inputUnidadNew.classList.add("is-invalid");
    inputUnidadNewFeedback.innerText =
      "Selecciona un unidad diferente a la actual.";
    is_valid = false;
  }

  if (!is_valid) return;

  // Submit (validate with html attributes)
  const form = document.getElementById("academico-change-unidad-form");
  if (form.checkValidity()) {
    form.submit();
  }
};

let template = null;
$(".modal").on("show.bs.modal", function (event) {
  template = $(this).html();
});

$(".modal").on("hidden.bs.modal", function (e) {
  $(this).html(template);
});
