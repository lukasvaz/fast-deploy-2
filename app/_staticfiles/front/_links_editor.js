const MAX_LINKS = 10;

const isValidUrl = (urlString) => {
  var urlPattern = new RegExp(
    "^(https?:\\/\\/)?" + // validate protocol
      "((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|" + // validate domain name
      "((\\d{1,3}\\.){3}\\d{1,3}))" + // validate OR ip (v4) address
      "(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*" + // validate port and path
      "(\\?[;&a-z\\d%_.~+=-]*)?" + // validate query string
      "(\\#[-a-z\\d_]*)?$",
    "i"
  ); // validate fragment locator
  return !!urlPattern.test(urlString);
};

// The corners are evils
const fixCorners = () => {
  var links_groups = document.getElementsByClassName("list-group-links");
  [].forEach.call(links_groups, (links_group) => {
    [].forEach.call(links_group.children, (node, idx) => {
      if (links_group.children.length === 1) {
        node.firstElementChild.style = "border-radius: 6px 0 0 6px;";
        node.lastElementChild.style =
          "border-radius: 0 6px 6px 0; width: 120px;";
      } else if (links_group.children.length > 1) {
        if (idx === 0) {
          node.firstElementChild.style = "border-radius: 6px 0 0 0;";
          node.lastElementChild.style =
            "border-radius: 0 6px 0 0; width: 120px";
        } else if (idx === links_group.children.length - 1) {
          node.firstElementChild.style = "border-radius: 0 0 0 6px;";
          node.lastElementChild.style =
            "border-radius: 0 0 6px 0; width: 120px;";
        } else {
          node.firstElementChild.style = "border-radius: 0;";
          node.lastElementChild.style = "border-radius: 0; width: 120px;";
        }
      }
    });
  });
};

const fixIdPos = () => {
  var links_groups = document.getElementsByClassName("list-group-links");
  [].forEach.call(links_groups, (links_group) => {
    const universidad_id = links_group.id.replace("listgrouplinks-", "");
    const addLinkExist = !!document.getElementById("linknuevo");
    [].forEach.call(links_group.children, (node, idx) => {
      if (addLinkExist && idx != links_group.children.length - 1) {
        node.firstElementChild.id = `list-group-item-action-${universidad_id}-${idx}`;
        node.lastElementChild.onclick = () => {
          deletelink(universidad_id, idx);
        };
      } else if (!addLinkExist) {
        node.firstElementChild.id = `list-group-item-action-${universidad_id}-${idx}`;
        node.lastElementChild.onclick = () => {
          deletelink(universidad_id, idx);
        };
      }
    });
  });
};

const agregarlink = (id_universidad) => {
  const list_group_id = `listgrouplinks-${id_universidad}`;
  var list_group = document.getElementById(list_group_id);
  const child_count = list_group.childElementCount;

  // Check invalidity
  var invalid = false;
  const linkAgregarNuevo = document.getElementById("linknuevo");
  if (linkAgregarNuevo) {
    const posLinkAgregarNuevo =
      linkAgregarNuevo.parentElement.parentElement.id.replace(
        "listgrouplinks-",
        ""
      );
    if (id_universidad != posLinkAgregarNuevo) {
      // Adding new val to another universidad
      var agregarlinkold = document.getElementById(
        `listgrouplinks-${posLinkAgregarNuevo}`
      ).lastElementChild;
      agregarlinkold.remove();
    } else {
      invalid = true;
    }
  }

  // If action is valid
  if (child_count < MAX_LINKS && !invalid) {
    // Add input box + button
    list_group.innerHTML =
      list_group.innerHTML +
      `
      <div class="d-flex">
        <input
          type="url"
          class="form-control"
          id="linknuevo"
          aria-describedby="nuevoLink"
          placeholder="https://ejemplo.com/personas"
        >

        <button
          type="button"
          class="btn btn-danger"
          onclick="savelink(${id_universidad})"
          id="buttonguardarlink-${id_universidad}"
        >
          Guardar
        </button>
      </div>
      `;
    fixCorners();
    fixIdPos();
  }
};

const savelink = (id_universidad) => {
  const list_group_id = `listgrouplinks-${id_universidad}`;
  var list_group = document.getElementById(list_group_id);
  const child_count = list_group.childElementCount;

  var input = document.getElementById("linknuevo");
  const button_guardar_id = `buttonguardarlink-${id_universidad}`;
  var button_guardar = document.getElementById(button_guardar_id);
  const new_link = input.value;
  // Validation
  if (!new_link || !isValidUrl(new_link)) {
    input.classList = "form-control is-invalid";
    return;
  } else {
    input.classList = "form-control";
  }
  const data = {
    universidad: id_universidad,
    link: new_link,
  };
  // Button loading
  button_guardar.disabled = true;
  button_guardar.innerHTML =
    `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>` +
    button_guardar.innerHTML;

  // Button buscar
  const button_buscar_id = `buttonBuscarAcademico`;
  var button_buscar_obj = document.getElementById(button_buscar_id);
  button_buscar_obj.disabled = true;

  // Make query
  fetch(_links_editor_ajax_agregar, {
    method: "POST",
    body: JSON.stringify(data),
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      // add new data
      const new_child_html = `
      <div class="d-flex">
        <a
          href="${new_link}"
          class="list-group-item list-group-item-action"
          target="_blank"
          >
          ${new_link}
        </a>
        <button
          type="button"
          class="btn btn-secondary"
          onclick="deletelink('${id_universidad}', '${child_count}')"
        >
          Eliminar
        </button>
      </div>`;
      list_group.lastElementChild.remove();
      list_group.innerHTML = list_group.innerHTML + new_child_html;
      fixCorners();
      fixIdPos();
      button_buscar_obj.disabled = false;
      const warning_buscar_id = `warningBuscarAcademico`;
      var warning_buscar_obj = document.getElementById(warning_buscar_id);
      warning_buscar_obj.classList.add("d-none");
    });
};

const deletelink = (id_universidad, pos) => {
  const list_group_id = `listgrouplinks-${id_universidad}`;
  var list_group = document.getElementById(list_group_id);

  const linktodelete_id = `list-group-item-action-${id_universidad}-${pos}`;
  var linktodelete_obj = document.getElementById(linktodelete_id);
  const link = linktodelete_obj.innerText;
  const data = {
    universidad: id_universidad,
    link: link,
  };
  // Make query
  fetch(_links_editor_ajax_eliminar, {
    method: "POST",
    body: JSON.stringify(data),
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      list_group.children[pos].remove();
      fixCorners();
      fixIdPos();
      if (data["links_count"] === 0) {
        const warning_buscar_id = `warningBuscarAcademico`;
        var warning_buscar_obj = document.getElementById(warning_buscar_id);
        warning_buscar_obj.classList.remove("d-none");
        const button_buscar_id = `buttonBuscarAcademico`;
        var button_buscar_obj = document.getElementById(button_buscar_id);
        button_buscar_obj.disabled = true;
      }
    });
};

window.onload = () => {
  fixCorners();
  fixIdPos();
};
