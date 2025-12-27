document.addEventListener("DOMContentLoaded", function () {
  // adding listeners on hover
  const mapIcon = document.getElementById('map-icon');
  const mapDiv = document.getElementById('map');
  const mapContainer = document.getElementById('map-container');

  if (mapIcon && mapDiv) {
    // initializing map rendering
    var tooltipMap = L.map('map').setView([
                parseFloat(insitutionLatitud),
                parseFloat(insitutionLongitud)
              ], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
              }).addTo(tooltipMap);

    L.marker([
                parseFloat(insitutionLatitud),
                parseFloat(insitutionLongitud)
              ]).addTo(tooltipMap)
                .bindPopup('<b>' + institutuionNombre + '</b> <br />' + 'Lat: ' + insitutionLatitud + ',<br> Lon: ' + insitutionLongitud)
                .openPopup();   
    mapContainer.addEventListener('mouseenter', function () {
      mapDiv.classList.remove('d-none');
    });
    mapContainer.addEventListener('mouseleave', function () {
      mapDiv.classList.add('d-none');
    });
    mapDiv.classList.add('d-none'); // initially hide the map
  }

}); 
