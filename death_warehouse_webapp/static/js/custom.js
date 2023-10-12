// custom.js

// Rétablit l'interaction avec les champs de formulaire
document.querySelectorAll('input, textarea, select').forEach(function (element) {
    element.removeAttribute('disabled');
});

// Réinitialise le formulaire lorsque le bouton de réinitialisation est cliqué
document.querySelectorAll('input[type="reset"]').forEach(function (resetButton) {
    resetButton.addEventListener('click', function (event) {
        const form = resetButton.form;
        if (form) {
            form.reset();
        }
    });
});

