const validate_form_edit_subarea = (subarea_id) => {
  // Inputs
  var inputSubareaNombreEs = document.getElementById(
    "subareaNombreEs" + subarea_id
  );
  var inputSubareaNombreEn = document.getElementById(
    "subareaNombreEn" + subarea_id
  );

  var inputAction = document.getElementById("action" + subarea_id);
  inputAction.value = "edit";

  // Validate
  var is_valid = true;
  if (!inputSubareaNombreEs.value || !inputSubareaNombreEn.value) {
    if (!inputSubareaNombreEs.value) {
      inputSubareaNombreEs.classList.add("is-invalid");
    }
    if (!inputSubareaNombreEn.value) {
      inputSubareaNombreEn.classList.add("is-invalid");
    }
    is_valid = false;
  } else {
    if (inputSubareaNombreEs.value.length > 200 || inputSubareaNombreEn.value.length > 200) {
      if (inputSubareaNombreEs.value.length > 200) {
        inputSubareaNombreEs.classList.add("is-invalid");
      }
      if (inputSubareaNombreEn.value.length > 200) {
        inputSubareaNombreEn.classList.add("is-invalid");
      }
      is_valid = false;
    }
    if (inputSubareaNombreEs.value.length < 3 || inputSubareaNombreEn.value.length < 3) {
      if (inputSubareaNombreEs.value.length < 3) {
        inputSubareaNombreEs.classList.add("is-invalid");
      }
      if (inputSubareaNombreEn.value.length < 3) {
        inputSubareaNombreEn.classList.add("is-invalid");
      }
      is_valid = false;
    }
  }

  if (!is_valid) return;

  // Submit (validate with html attributes)
  const form = document.getElementById("subareaAction" + subarea_id);
  if (form.checkValidity()) {
    form.submit();
  }
};
const validate_form_remove_subarea = (subarea_id) => {
  // Inputs
  var inputAction = document.getElementById("action" + subarea_id);
  inputAction.value = "remove";

  // Submit
  const form = document.getElementById("subareaAction" + subarea_id);
  form.submit();
};

const validate_form_new_subarea = (area_id) => {
  // Inputs
  var inputSubareaNombreEs = document.getElementById(
    "subareaNombreEsNew" + area_id
  );
  var inputSubareaNombreEn = document.getElementById(
    "subareaNombreEnNew" + area_id
  );

  // Validate
  var is_valid = true;
  if (!inputSubareaNombreEs.value || !inputSubareaNombreEn.value) {
    if (!inputSubareaNombreEs.value) {
      inputSubareaNombreEs.classList.add("is-invalid");
    }
    if (!inputSubareaNombreEn.value) {
      inputSubareaNombreEn.classList.add("is-invalid");
    }
    is_valid = false;
  } else {
    if (inputSubareaNombreEs.value.length > 200 || inputSubareaNombreEn.value.length > 200) {
      if (inputSubareaNombreEs.value.length > 200) {
        inputSubareaNombreEs.classList.add("is-invalid");
      }
      if (inputSubareaNombreEn.value.length > 200) {
        inputSubareaNombreEn.classList.add("is-invalid");
      }
      is_valid = false;
    }
    if (inputSubareaNombreEs.value.length < 3 || inputSubareaNombreEn.value.length < 3) {
      if (inputSubareaNombreEs.value.length < 3) {
        inputSubareaNombreEs.classList.add("is-invalid");
      }
      if (inputSubareaNombreEn.value.length < 3) {
        inputSubareaNombreEn.classList.add("is-invalid");
      }
      is_valid = false;
    }
  }

  if (!is_valid) return;

  // Submit (validate with html attributes)
  const form = document.getElementById("subareaNew" + area_id);
  if (form.checkValidity()) {
    form.submit();
  }
};