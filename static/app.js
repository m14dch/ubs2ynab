const fileInput = document.querySelector("#files");
const dropzone = document.querySelector("[data-dropzone]");
const fileList = document.querySelector("[data-file-list]");
const emptyState = document.querySelector("[data-empty-state]");
const clearButton = document.querySelector("[data-clear-files]");
const chooseButton = document.querySelector("[data-choose-files]");

if (fileInput && dropzone && fileList && emptyState && clearButton && chooseButton) {
  const selectedFiles = new Map();

  const fileKey = (file) => [file.name, file.size, file.lastModified].join(":");

  const syncInputFiles = () => {
    const dataTransfer = new DataTransfer();

    for (const file of selectedFiles.values()) {
      dataTransfer.items.add(file);
    }

    fileInput.files = dataTransfer.files;
  };

  const renderFiles = () => {
    fileList.innerHTML = "";

    if (selectedFiles.size === 0) {
      emptyState.hidden = false;
      clearButton.disabled = true;
      return;
    }

    emptyState.hidden = true;
    clearButton.disabled = false;

    for (const [key, file] of selectedFiles.entries()) {
      const item = document.createElement("li");
      item.className = "file-item";

      const name = document.createElement("span");
      name.textContent = file.name;
      name.className = "file-name";

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "file-remove";
      remove.textContent = "Remove";
      remove.addEventListener("click", () => {
        selectedFiles.delete(key);
        syncInputFiles();
        renderFiles();
      });

      item.append(name, remove);
      fileList.append(item);
    }
  };

  const addFiles = (files) => {
    for (const file of files) {
      if (file.name.toLowerCase().endsWith(".csv")) {
        selectedFiles.set(fileKey(file), file);
      }
    }

    syncInputFiles();
    renderFiles();
  };

  fileInput.addEventListener("change", () => {
    addFiles(fileInput.files);
  });

  chooseButton.addEventListener("click", () => {
    fileInput.click();
  });

  clearButton.addEventListener("click", () => {
    selectedFiles.clear();
    syncInputFiles();
    renderFiles();
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      event.stopPropagation();
      dropzone.classList.add("is-dragover");
    });
  });

  ["dragleave", "dragend", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (eventName !== "drop") {
        dropzone.classList.remove("is-dragover");
      }
    });
  });

  dropzone.addEventListener("drop", (event) => {
    dropzone.classList.remove("is-dragover");
    addFiles(event.dataTransfer?.files ?? []);
  });

  renderFiles();
}
