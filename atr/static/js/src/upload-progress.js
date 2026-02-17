/*
 *  Licensed to the Apache Software Foundation (ASF) under one
 *  or more contributor license agreements.  See the NOTICE file
 *  distributed with this work for additional information
 *  regarding copyright ownership.  The ASF licenses this file
 *  to you under the Apache License, Version 2.0 (the
 *  "License"); you may not use this file except in compliance
 *  with the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing,
 *  software distributed under the License is distributed on an
 *  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 *  KIND, either express or implied.  See the License for the
 *  specific language governing permissions and limitations
 *  under the License.
 */

function handleXhrLoad(xhr, ctx) {
	ctx.activeUploads.delete(ctx.index);
	if (xhr.status >= 200 && xhr.status < 300) {
		UploadUI.markUploadDone(ctx.ui, true, "Staged");
		ctx.state.completedCount++;
	} else {
		let msg = "Upload failed";
		try {
			msg = JSON.parse(xhr.responseText).error || msg;
		} catch {
			/* ignore */
		}
		UploadUI.markUploadDone(ctx.ui, false, `Failed: ${msg}`);
		ctx.state.failedCount++;
		ctx.addRetryButton(ctx.ui, ctx.index);
	}
	ctx.checkAllComplete();
}

function handleXhrFailure(ctx, reason, isCancelled) {
	ctx.activeUploads.delete(ctx.index);
	if (isCancelled) {
		ctx.statusEl.textContent = "Cancelled";
		ctx.statusEl.className = "upload-status text-secondary";
		ctx.cancelBtn.classList.add("d-none");
	} else {
		UploadUI.markUploadDone(ctx.ui, false, `Failed: ${reason}`);
		ctx.addRetryButton(ctx.ui, ctx.index);
	}
	ctx.state.failedCount++;
	ctx.checkAllComplete();
}

function setupXhrHandlers(
	xhr,
	ui,
	index,
	state,
	addRetryButtonFn,
	checkAllCompleteFn,
) {
	const ctx = {
		ui,
		index,
		state,
		addRetryButton: addRetryButtonFn,
		checkAllComplete: checkAllCompleteFn,
		activeUploads: state.activeUploads,
		statusEl: ui.querySelector(".upload-status"),
		cancelBtn: ui.querySelector(".cancel-btn"),
	};
	const progressBar = ui.querySelector("progress");
	const percentEl = ui.querySelector(".upload-percent");

	xhr.upload.addEventListener("progress", (e) =>
		UploadUI.handleUploadProgress(
			e,
			progressBar,
			ctx.statusEl,
			percentEl,
			ctx.cancelBtn,
		),
	);
	xhr.addEventListener("load", () => handleXhrLoad(xhr, ctx));
	xhr.addEventListener("error", () =>
		handleXhrFailure(ctx, "Network error", false),
	);
	xhr.addEventListener("abort", () => handleXhrFailure(ctx, null, true));
}

function checkAllComplete(state, container, finaliseUrl, csrfToken) {
	if (state.activeUploads.size > 0) return;
	if (state.completedCount === 0) {
		UploadUI.showAllFailedSummary(container);
	} else if (state.failedCount > 0) {
		UploadUI.showPartialSuccessSummary(
			container,
			state.completedCount,
			state.totalFiles,
			() => UploadUI.doFinalise(container, finaliseUrl, csrfToken),
		);
	} else {
		UploadUI.doFinalise(container, finaliseUrl, csrfToken);
	}
}

function startUpload(
	file,
	index,
	state,
	stageUrl,
	csrfToken,
	addRetryButtonFn,
	checkComplete,
) {
	const ui = document.getElementById(`upload-file-${index}`);
	const xhr = new XMLHttpRequest();
	state.activeUploads.set(index, xhr);
	setupXhrHandlers(xhr, ui, index, state, addRetryButtonFn, checkComplete);
	const formData = new FormData();
	formData.append("csrf_token", csrfToken);
	formData.append("file", file, file.name);
	xhr.open("POST", stageUrl, true);
	xhr.send(formData);
	ui.querySelector(".upload-status").textContent = "Uploading...";
}

function addRetryButton(
	ui,
	index,
	state,
	fileInput,
	stageUrl,
	csrfToken,
	checkComplete,
) {
	const retryBtn = document.createElement("button");
	retryBtn.type = "button";
	retryBtn.className = "btn btn-sm btn-outline-primary retry-btn ms-2";
	retryBtn.textContent = "Retry";
	retryBtn.addEventListener("click", () => {
		UploadUI.resetUploadUI(ui);
		retryBtn.remove();
		state.failedCount--;
		const file = Array.from(fileInput.files || [])[index];
		startUpload(
			file,
			index,
			state,
			stageUrl,
			csrfToken,
			addRetryButton,
			checkComplete,
		);
	});
	ui.querySelector(".upload-status").parentNode.append(retryBtn);
}

function handleFormSubmit(
	e,
	form,
	fileInput,
	container,
	state,
	stageUrl,
	csrfToken,
	checkComplete,
) {
	e.preventDefault();
	const files = Array.from(fileInput.files || []);
	if (files.length === 0) {
		alert("Please select files to upload.");
		return;
	}
	state.totalFiles = files.length;
	state.completedCount = 0;
	state.failedCount = 0;
	form.classList.add("d-none");
	container.classList.remove("d-none");
	container.innerHTML = "";
	files.forEach((file, index) => {
		container.append(
			UploadUI.createFileProgressUI(file, index, state.activeUploads),
		);
		startUpload(
			file,
			index,
			state,
			stageUrl,
			csrfToken,
			(ui, idx) =>
				addRetryButton(
					ui,
					idx,
					state,
					fileInput,
					stageUrl,
					csrfToken,
					checkComplete,
				),
			checkComplete,
		);
	});
}

(() => {
	const config = document.getElementById("upload-config");
	if (!config) return;

	const stageUrl = config.dataset.stageUrl;
	const finaliseUrl = config.dataset.finaliseUrl;
	if (!stageUrl || !finaliseUrl) return;

	const form = document
		.querySelector('input[name="variant"][value="add_files"]')
		?.closest("form");
	if (!form) return;

	const fileInput = form.querySelector('input[type="file"]');
	const container = document.getElementById("upload-progress-container");
	const csrfToken = form.querySelector('input[name="csrf_token"]')?.value;
	const state = {
		activeUploads: new Map(),
		completedCount: 0,
		failedCount: 0,
		totalFiles: 0,
	};

	const checkComplete = () =>
		checkAllComplete(state, container, finaliseUrl, csrfToken);

	form.addEventListener("submit", (e) =>
		handleFormSubmit(
			e,
			form,
			fileInput,
			container,
			state,
			stageUrl,
			csrfToken,
			checkComplete,
		),
	);
})();
