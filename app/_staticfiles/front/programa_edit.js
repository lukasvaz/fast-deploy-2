// Unidad Edit
function updateUnidadesDropdown() {
  const paisDropdown = document.getElementById("InputPais");
  const unidadDropdown = document.getElementById("InputUnidad");
  const unidadesData = JSON.parse(document.getElementById("unidades_context").textContent);//  {pais_code : {country_label: "", unidades: {id: "uni - unidad"}}}
  
  // Clear existing options in Unidades dropdown
  unidadDropdown.innerHTML = '<option value="">Seleccione una unidad académica</option>';

  // Get selected País
  const selectedPais = paisDropdown.value;

  // Populate Unidades dropdown based on selected País
  if (selectedPais) {
    const paisUnidades = unidadesData[selectedPais];
    if (paisUnidades) {
      const unidades = paisUnidades.unidades;
      for (const u of unidades) {
        const option = document.createElement("option");
        option.value = u.id;
        option.textContent = u.label;
        if (String(u.id) === String(initialUnidadId)) option.selected = true;
        unidadDropdown.appendChild(option);
    }
    }
}
}
// setting initial unidades options on page load
document.addEventListener("DOMContentLoaded", function() {
  updateUnidadesDropdown();
  //select 2 
  $('#InputUnidad').select2({
    width: '100%',
    placeholder: 'Seleccione una unidad académica',
    allowClear: true
  });  
  $('#InputPais').select2({
    width: '100%',
    placeholder: 'Seleccione un país',
    allowClear: true
  });
}); 