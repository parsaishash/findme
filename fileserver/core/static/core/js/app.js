(function () {
  function handleAsyncForm(form, onSuccess) {
    if (!form) return;
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const submitter = event.submitter || form.querySelector("[type=submit]");
      if (submitter) {
        submitter.disabled = true;
      }
      form.dispatchEvent(new CustomEvent("async:start"));
      const formData = new FormData(form);
      fetch(form.action, {
        method: form.method || "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          Accept: "application/json",
        },
        credentials: "same-origin",
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Request failed");
          }
          return response.json();
        })
        .then((data) => {
          form.dispatchEvent(new CustomEvent("async:success", { detail: data }));
          if (typeof onSuccess === "function") {
            onSuccess(data);
          }
        })
        .catch((error) => {
          form.dispatchEvent(new CustomEvent("async:error", { detail: error }));
          console.error(error);
          showToast("Something went wrong. Please try again.");
        })
        .finally(() => {
          form.dispatchEvent(new CustomEvent("async:complete"));
          if (submitter) {
            submitter.disabled = false;
          }
        });
    });
  }

  function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast align-items-center text-bg-dark border-0";
    toast.role = "alert";
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
  }

  function buildUploadUrl(base, path) {
    if (!path) return base;
    const encoded = path
      .split("/")
      .filter(Boolean)
      .map(encodeURIComponent)
      .join("/");
    if (base.endsWith("/")) {
      return `${base}${encoded}/`;
    }
    return `${base}/${encoded}/`;
  }

  document.addEventListener("DOMContentLoaded", function () {
    const shareModal = document.getElementById("shareModal");
    if (shareModal) {
      shareModal.addEventListener("show.bs.modal", function (event) {
        const trigger = event.relatedTarget;
        const pathField = shareModal.querySelector("input[name=path]");
        const display = shareModal.querySelector("[data-share-path]");
        if (trigger && pathField) {
          const path = trigger.getAttribute("data-path") || "";
          pathField.value = path;
          if (display) {
            display.textContent = path || "/";
          }
        }
        const result = shareModal.querySelector("[data-share-result]");
        if (result) {
          result.classList.add("d-none");
        }
      });

      const shareForm = shareModal.querySelector("form");
      handleAsyncForm(shareForm, function (data) {
        if (!data.success) {
          showToast("Unable to create share link.");
          return;
        }
        const result = shareModal.querySelector("[data-share-result]");
        const linkEl = shareModal.querySelector("[data-share-url]");
        const expiryEl = shareModal.querySelector("[data-share-expiry]");
        if (result && linkEl && expiryEl) {
          linkEl.value = data.url;
          expiryEl.textContent = new Date(data.expires_at).toLocaleString();
          result.classList.remove("d-none");
          linkEl.focus();
          linkEl.select();
          document.execCommand("copy");
        }
      });
    }

    const uploadModal = document.getElementById("uploadModal");
    if (uploadModal) {
      const uploadForm = uploadModal.querySelector("form");
      const base = uploadForm ? uploadForm.dataset.uploadBase : "";
      const progress = uploadModal.querySelector("[data-upload-progress]");
      if (uploadForm) {
        uploadForm.addEventListener("async:start", function () {
          if (progress) {
            progress.classList.remove("d-none");
          }
        });
        uploadForm.addEventListener("async:complete", function () {
          if (progress) {
            progress.classList.add("d-none");
          }
        });
      }
      uploadModal.addEventListener("show.bs.modal", function (event) {
        const trigger = event.relatedTarget;
        const pathField = uploadModal.querySelector("input[name=target_path]");
        const label = uploadModal.querySelector("[data-upload-path]");
        if (trigger && pathField) {
          const path = trigger.getAttribute("data-path") || "";
          pathField.value = path;
          if (label) {
            label.textContent = path || "/";
          }
          if (uploadForm && base) {
            uploadForm.action = buildUploadUrl(base, path);
          }
        }
      });
      handleAsyncForm(uploadForm, function (data) {
        if (data.success) {
          showToast("Upload completed.");
          setTimeout(() => window.location.reload(), 500);
        } else {
          showToast("Upload failed.");
        }
      });
    }

    document.querySelectorAll("[data-copy]").forEach((el) => {
      el.addEventListener("click", function () {
        const value = el.getAttribute("data-copy") || el.textContent;
        navigator.clipboard
          .writeText(value)
          .then(() => showToast("Copied to clipboard"))
          .catch(() => showToast("Unable to copy"));
      });
    });

    document.querySelectorAll("[data-copy-target]").forEach((el) => {
      el.addEventListener("click", function () {
        const selector = el.getAttribute("data-copy-target");
        const target = selector ? document.querySelector(selector) : null;
        if (target && target.value) {
          navigator.clipboard
            .writeText(target.value)
            .then(() => showToast("Copied to clipboard"));
        }
      });
    });

    const themeForm = document.getElementById("theme-toggle-form");
    if (themeForm) {
      themeForm.addEventListener("submit", function (event) {
        event.preventDefault();
        fetch(themeForm.action, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": themeForm.querySelector("input[name=csrfmiddlewaretoken]").value,
          },
          credentials: "same-origin",
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.theme) {
              document.body.setAttribute("data-theme", data.theme);
            }
          })
          .catch(() => {
            showToast("Unable to toggle theme");
          });
      });
    }

    document.querySelectorAll("form[data-async-token]").forEach((form) => {
      handleAsyncForm(form, function (data) {
        if (!data.success) {
          showToast("Unable to generate token");
          return;
        }
        const container = form.closest("[data-token-result]");
        if (container) {
          container.querySelector("[data-token-value]").textContent = data.token;
          container.querySelector("[data-token-curl]").textContent = data.curl_example;
          container.querySelector("[data-token-wget]").textContent = data.wget_example;
          container.classList.remove("d-none");
        }
      });
    });
  });
})();
