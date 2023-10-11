// custom.js

// Rétablit l'interaction avec les champs de formulaire
document.querySelectorAll('input, textarea, select').forEach(function (element) {
    element.removeAttribute('disabled');
});
