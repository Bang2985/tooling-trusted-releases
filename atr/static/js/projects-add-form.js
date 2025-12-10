document.addEventListener("DOMContentLoaded", function() {
    const configElement = document.getElementById("projects-add-config");
    if (!configElement) return;

    const committeeDisplayName = configElement.dataset.committeeDisplayName;
    const committeeName = configElement.dataset.committeeName;
    if (!committeeDisplayName || !committeeName) return;

    const formTexts = document.querySelectorAll(".form-text, .text-muted");
    formTexts.forEach(function(element) {
        element.textContent = element.textContent.replace(/Example/g, committeeDisplayName);
        element.textContent = element.textContent.replace(/example/g, committeeName.toLowerCase());
    });
});
