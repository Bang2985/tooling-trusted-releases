document.addEventListener("DOMContentLoaded", () => {
    let debounceTimeout;
    const debounceDelay = 500;

    const bodyTextarea = document.getElementById("body");
    const voteDurationInput = document.getElementById("vote_duration");
    const textPreviewContent = document.getElementById("vote-body-preview-content");
    const voteForm = document.querySelector("form.atr-canary");
    const configElement = document.getElementById("vote-config");

    if (!bodyTextarea || !voteDurationInput || !textPreviewContent || !voteForm) {
        console.error("Required elements for vote preview not found. Exiting.");
        return;
    }

    const previewUrl = configElement ? configElement.dataset.previewUrl : null;
    const minHours = configElement ? configElement.dataset.minHours : "72";
    const csrfTokenInput = voteForm.querySelector('input[name="csrf_token"]');

    if (!previewUrl || !csrfTokenInput) {
        console.error("Required data attributes or CSRF token not found for vote preview.");
        return;
    }
    const csrfToken = csrfTokenInput.value;

    function fetchAndUpdateVotePreview() {
        const bodyContent = bodyTextarea.value;
        const voteDuration = voteDurationInput.value || minHours;

        fetch(previewUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": csrfToken
                },
                body: new URLSearchParams({
                    "body": bodyContent,
                    "duration": voteDuration,
                    "csrf_token": csrfToken
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`HTTP error ${response.status}: ${text}`)
                    });
                }
                return response.text();
            })
            .then(previewText => {
                textPreviewContent.textContent = previewText;
            })
            .catch(error => {
                console.error("Error fetching email preview:", error);
                textPreviewContent.textContent = `Error loading preview:\n${error.message}`;
            });
    }

    bodyTextarea.addEventListener("input", () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(fetchAndUpdateVotePreview, debounceDelay);
    });

    voteDurationInput.addEventListener("input", () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(fetchAndUpdateVotePreview, debounceDelay);
    });

    fetchAndUpdateVotePreview();
});
