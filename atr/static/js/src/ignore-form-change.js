document.addEventListener("DOMContentLoaded", () => {
	document
		.querySelectorAll("table.page-details input.form-control")
		.forEach((input) => {
			var row = input.closest("tr");
			var updateBtn = row.querySelector("button.btn-primary");
			function check() {
				if (input.value === input.dataset.value) {
					updateBtn.classList.add("disabled");
				} else {
					updateBtn.classList.remove("disabled");
				}
			}
			input.addEventListener("input", check);
			check();
		});
});
