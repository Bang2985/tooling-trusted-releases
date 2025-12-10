document.addEventListener("DOMContentLoaded", function() {
    const checkboxes = document.querySelectorAll("input[name='selected_committees']");
    if (checkboxes.length === 0) return;

    const firstCheckbox = checkboxes[0];
    const container = firstCheckbox.closest(".col-sm-8");
    if (!container) return;

    const button = document.createElement("button");
    button.id = "toggleCommitteesBtn";
    button.type = "button";
    button.className = "btn btn-outline-secondary btn-sm mt-2";
    button.textContent = "Select all committees";

    button.addEventListener("click", function() {
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        checkboxes.forEach(cb => cb.checked = !allChecked);
        button.textContent = allChecked ? "Select all committees" : "Deselect all committees";
    });

    container.appendChild(button);
});
