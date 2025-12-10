document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".copy-var-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const variable = btn.dataset.variable;
            navigator.clipboard.writeText(variable).then(() => {
                const originalText = btn.textContent;
                btn.textContent = "Copied!";
                btn.classList.remove("btn-outline-secondary");
                btn.classList.add("btn-success");
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove("btn-success");
                    btn.classList.add("btn-outline-secondary");
                }, 1500);
            });
        });
    });
});
