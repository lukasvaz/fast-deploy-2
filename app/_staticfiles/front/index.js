let phrase_idx = 0;
let char_idx = 0;
let is_deleting = false;
let placeholder = "";
const txts = ["Universidad de Chile","UCH;UC","Machine Learning", "Pedro;Juan", "Magister Ciencia de Datos; Master Software"];
const speed = 200;

const placeholderchanger = () => {
  if (!is_deleting) {
    placeholder += txts[phrase_idx].charAt(char_idx);
  } else {
    placeholder = placeholder.slice(0, -1);
  }
  document
    .getElementById("searchtextid")
    .setAttribute("placeholder", placeholder);
  if (!is_deleting) {
    char_idx++;
    if (char_idx === txts[phrase_idx].length) {
      is_deleting = !is_deleting;
    }
  } else {
    char_idx--;
    if (char_idx === 0) {
      is_deleting = !is_deleting;
      phrase_idx++;
      if (phrase_idx === txts.length) {
        phrase_idx = 0;
      }
    }
  }
  setTimeout(placeholderchanger, speed);
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
    fs_select.add(voidOption);
    // Add options
    subareas.forEach((subarea) => {
      let newOption = new Option(subarea["nombre"], subarea["id"]);
      fs_select.add(newOption);
    });
  }
};

window.onload = () => {
  placeholderchanger();
};
