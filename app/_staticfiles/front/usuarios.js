const generar_link = () => {
  // Toast Error
  const toast_error = document.getElementById("toast_error");
  const toastBootstrap_error = bootstrap.Toast.getOrCreateInstance(toast_error);

  const institucion_select = document.getElementById("institucion_select");
  const institucion_generar = document.getElementById("select_generar");
  const institucion_error = document.getElementById("select_error");
  const institucion_valid = document.getElementById("select_valid");
  const institucion_link_1 = document.getElementById("select_link_1");
  const institucion_link_2 = document.getElementById("select_link_2");
  const institucion_id = institucion_select.value;
  if (institucion_id) {
    institucion_error.classList.add("d-none");
    institucion_generar.disabled = true;
    institucion_generar.classList.add("d-none");
    // Create request
    // Make query
    fetch(ajax_url, {
      method: "POST",
      body: JSON.stringify(institucion_id),
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
        const new_url = host + data.url;
        institucion_link_1.value = new_url;
        institucion_link_2.value = new_url;
        if (navigator.clipboard) {
          institucion_valid.classList.remove("d-none");
        } else {
          institucion_link_2.classList.remove("d-none");
        }
      })
      .catch((error) => {
        console.error("There was an error", error);
      });
  } else {
    institucion_error.classList.remove("d-none");
  }
};
const copy_link = () => {
  const copy_text = document.getElementById("select_link_1").value;
  navigator.clipboard
    .writeText(copy_text)
    .then(() => {
    })
    .catch(() => {
      console.error("something went wrong");
    });
};

const eliminarModal = document.getElementById("modalEliminar");
if (eliminarModal) {
  eliminarModal.addEventListener("show.bs.modal", (event) => {
    // Button that triggered the modal
    const button = event.relatedTarget;
    // Extract info from data-bs-* attributes
    const user_email = button.getAttribute("data-bs-email");

    // Update the modal's content.
    const modalTitle = eliminarModal.querySelector(".modal-title");

    modalTitle.textContent = `Eliminar usuario ${user_email}`;
    var delete_button = document.getElementById("deleteUserButton");
    delete_button.href += `?user=${user_email}`;
  });
}

let template = null;
$(".modal").on("show.bs.modal", function (event) {
  template = $(this).html();
});

$(".modal").on("hidden.bs.modal", function (e) {
  $(this).html(template);
});

$(document).ready(() => {
  $(`#table-users`).DataTable({
    language: {
      lengthMenu: "Mostrar _MENU_ registros por página",
      zeroRecords: "No hay datos",
      info: "Mostrando página _PAGE_ de _PAGES_",
      infoEmpty: "No hay registros disponibles",
      infoFiltered: "(filtrado de _MAX_ registros totales)",
      search: "Buscar:",
      paginate: {
        previous: "Anterior",
        next: "Siguiente",
      },
    },
  });
});
