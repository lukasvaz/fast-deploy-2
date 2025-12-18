const box_nodata_id = "result-nodata-box";
const box_academicos_id = "result-academicos-box";
const box_universidades_id = "result-universidades-box";
const box_grados_id = "result-grados-box";
const button_academicos_id = "academicos_button";
const button_grados_id = "grados_button";
const button_universidades_id = "universidades_button"

const selectSubareaInit = () => {
  var fs_select = document.getElementById("fs");
  const area_value = document.getElementById("fa").value;
  if (area_value != 0) {
    fs_select.disabled = false;
    const subareas = areas_subareas["areas"].find(
      (area) => area["id"] == area_value
    )["subareas"];
    // Add options
    subareas.forEach((subarea) => {
      let newOption = new Option(subarea["nombre"], subarea["id"]);
      fs_select.add(newOption);
    });
    if (subarea_init != 0) {
      fs_select.value = subarea_init;
    }
  }
};

const areachange = () => {
  var fa_select = document.getElementById("fa");
  var fs_select = document.getElementById("fs");
  // Clean options
  while (fs_select.options.length > 0) {
    fs_select.remove(0);
  }
  let voidOption = new Option("Subárea: Todos", "0");
  fs_select.add(voidOption);
  if (!fa_select.value || fa_select.value === "0") {
    fs_select.disabled = true;
    fs_select.value = "0";
  } else {
    fs_select.disabled = false;
    const subareas = areas_subareas["areas"].find(
      (area) => area["id"] == fa_select.value
    )["subareas"];
    // Clean options
    while (fs_select.options.length > 0) {
      fs_select.remove(0);
    }
    // Add options
    fs_select.add(voidOption);
    subareas.forEach((subarea) => {
      let newOption = new Option(subarea["nombre"], subarea["id"]);
      fs_select.add(newOption);
    });
  }
};
const chooseInitTab = () => {
  const box_nodata = document.getElementById(box_nodata_id);
  const box_academicos = document.getElementById(box_academicos_id);
  const box_universidades = document.getElementById(box_universidades_id);
  const box_grados = document.getElementById(box_grados_id);
  const button_academicos = document.getElementById(button_academicos_id);
  const button_universidades = document.getElementById(button_universidades_id);
  const button_grados = document.getElementById(button_grados_id);
  
  // ensure safe defaults
  if (button_academicos) button_academicos.disabled = true;
  if (button_universidades) button_universidades.disabled = true;
  if (button_grados) button_grados.disabled = true;
  
  // for each section 
  [button_academicos, button_universidades, button_grados].forEach((button, index) => {
    button.disabled = false;
  })

  // initial section
  if (current_section ) {
    toggletab(current_section);
  }
}
const toggletab = (tab) => {
  const enableFilters = (section) => {
  // common filters
  const pais = document.getElementById("filter-pais");
  let commonFilters = [pais]
  // academico filters
  const fa = document.getElementById("fa");
  const fs = document.getElementById("fs");
  let academicoFilters = [fa ,fs]
  // programa filters
  const grado = document.getElementById("filter-grado");
  let gradosFilters = [grado]
  if (section === "academicos") {
      academicoFilters.forEach ((filter) => {
        filter.disabled = false,
        filter.classList.remove("d-none")
      }
    )
      commonFilters.forEach ((filter) => {
        filter.classList.remove("d-none"),
        filter.disabled = false
      }
      )
      gradosFilters.forEach ((filter) => {
        filter.classList.add("d-none"),
        filter.disabled = true
      }
  )

  } else if (section === "universidades") {
      commonFilters.forEach ((filter) => 
      {
        filter.classList.remove("d-none"),
        filter.disabled = false
      }
      )
      academicoFilters.forEach ((filter) => {
        filter.classList.add("d-none"),
        filter.disabled = true
      }
    )
      gradosFilters.forEach ((filter) => {
        filter.classList.add("d-none"),
        filter.disabled = true
      }
  )

    
  } else if (section === "grados") {
      gradosFilters.forEach ((filter) => {
        filter.classList.remove("d-none"),
        filter.disabled = false
      }
    )
      commonFilters.forEach ((filter) => {  
        filter.classList.remove("d-none"),
        filter.disabled = false
      }
      )
      academicoFilters.forEach ((filter) => {
        filter.classList.add("d-none"),
        filter.disabled = true
      }
  ) 
  } 

  
};
  const box_academicos = document.getElementById(box_academicos_id);
  const button_academicos = document.getElementById(button_academicos_id);
  
  const box_universidades = document.getElementById(box_universidades_id);
  const button_universidades = document.getElementById(button_universidades_id);
  
  const box_grados = document.getElementById("result-grados-box");
  const button_grados = document.getElementById("grados_button");

  const nodata_box = document.getElementById(box_nodata_id);
  
  // detect presence by checking for result cards 
  const hasAcademicos = !!(box_academicos && box_academicos.querySelector(".card"));
  const hasUniversidades = !!(box_universidades && box_universidades.querySelector(".card"));
  const hasGrados = !!(box_grados && box_grados.querySelector(".card"));
  const sections=['academicos', 'universidades', 'grados']
  const hasObjects=[hasAcademicos, hasUniversidades, hasGrados]
  
  if (tab === "academicos") {
      box_academicos.classList.remove("d-none");
      box_universidades.classList.add("d-none");
      box_grados.classList.add("d-none");
      button_academicos.classList.add("selected");
      button_universidades.classList.remove("selected");
      button_grados.classList.remove("selected");
      enableFilters("academicos");
      if (!hasAcademicos) {
        box_academicos.classList.add("d-none");
        nodata_box.classList.remove("d-none");
      }else{
        nodata_box.classList.add("d-none");
      }
  } else if (tab === "universidades") {
      box_academicos.classList.add("d-none");
      box_universidades.classList.remove("d-none");
      box_grados.classList.add("d-none");
      button_academicos.classList.remove("selected");
      button_universidades.classList.add("selected");
      button_grados.classList.remove("selected");
      enableFilters("universidades");
      if (!hasUniversidades) {
          box_universidades.classList.add("d-none");
          nodata_box.classList.remove("d-none");
        }else{
          nodata_box.classList.add("d-none");
        }
  } else if (tab === "grados") {
      box_academicos.classList.add("d-none");
      box_universidades.classList.add("d-none");
      box_grados.classList.remove("d-none");
      button_academicos.classList.remove("selected");
      button_universidades.classList.remove("selected");
      button_grados.classList.add("selected");
      enableFilters("grados");
      if (!hasGrados) {
        box_grados.classList.add("d-none");
        nodata_box.classList.remove("d-none");
      }else{
        nodata_box.classList.add("d-none");
      }
  }
  const formSection = document.getElementById("form-section");
  if (formSection) {
    formSection.value = tab;
  }
};
window.onload = () => {
  chooseInitTab();
  selectSubareaInit();
};
