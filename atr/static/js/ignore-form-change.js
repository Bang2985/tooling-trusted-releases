document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("table.page-details input.form-control").forEach(function (input) {
        var row = input.closest("tr");
        var updateBtn = row.querySelector("button.btn-primary");
        function check() {
            if (input.value !== input.dataset.value) {
                updateBtn.classList.remove("disabled");
            } else {
                updateBtn.classList.add("disabled");
            }
        }
        input.addEventListener("input", check);
        check();
    });
});
