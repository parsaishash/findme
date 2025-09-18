(function () {
  function getCsrfToken() {
    var cookieValue = null;
    var name = 'csrftoken';
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
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

  // Sidebar functionality
  function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const resizeHandle = document.getElementById('resize-handle');
    const toggleButton = document.getElementById('sidebar-toggle');
    const collapseThreshold = 120; // pixels
    
    if (!sidebar || !resizeHandle || !toggleButton) return;

    // Load saved state from localStorage
    const savedWidth = localStorage.getItem('sidebar-width');
    const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    
    if (isCollapsed) {
      sidebar.classList.add('collapsed');
      sidebar.style.width = '3rem';
      toggleButton.querySelector('i').className = 'bi bi-chevron-right';
    } else if (savedWidth) {
      sidebar.style.width = savedWidth + 'px';
    }

    // Resize functionality
    let isResizing = false;
    let lastValidWidth = savedWidth ? parseInt(savedWidth) : 256;
    
    resizeHandle.addEventListener('mousedown', function(e) {
      isResizing = true;
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', function(e) {
      if (!isResizing) return;
      
      const rect = sidebar.getBoundingClientRect();
      const newWidth = e.clientX - rect.left;
      
      if (newWidth >= 48 && newWidth <= 320) { // min 3rem, max 20rem
        sidebar.style.width = newWidth + 'px';
        lastValidWidth = newWidth;
        localStorage.setItem('sidebar-width', newWidth);
        
        // Auto-collapse when below threshold
        if (newWidth < collapseThreshold) {
          sidebar.classList.add('collapsed');
          toggleButton.querySelector('i').className = 'bi bi-chevron-right';
          localStorage.setItem('sidebar-collapsed', 'true');
        } else {
          sidebar.classList.remove('collapsed');
          toggleButton.querySelector('i').className = 'bi bi-chevron-left';
          localStorage.setItem('sidebar-collapsed', 'false');
        }
      }
    });

    document.addEventListener('mouseup', function() {
      if (isResizing) {
        isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    });

    // Toggle functionality
    toggleButton.addEventListener('click', function() {
      const icon = toggleButton.querySelector('i');
      
      if (sidebar.classList.contains('collapsed')) {
        // Expand: restore to last valid width
        sidebar.classList.remove('collapsed');
        icon.className = 'bi bi-chevron-left';
        sidebar.style.width = lastValidWidth + 'px';
        localStorage.setItem('sidebar-collapsed', 'false');
        localStorage.setItem('sidebar-width', lastValidWidth);
      } else {
        // Collapse: save current width and collapse
        const currentWidth = parseInt(sidebar.style.width) || 256;
        lastValidWidth = currentWidth;
        sidebar.classList.add('collapsed');
        icon.className = 'bi bi-chevron-right';
        sidebar.style.width = '3rem';
        localStorage.setItem('sidebar-collapsed', 'true');
        localStorage.setItem('sidebar-width', currentWidth);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Initialize sidebar
    initSidebar();
    
    // Configure HTMX CSRF and default swap
    if (window.htmx) {
      document.body.addEventListener('htmx:configRequest', function(evt) {
        evt.detail.headers['X-CSRFToken'] = getCsrfToken();
      });
      htmx.config.historyEnabled = true;
      htmx.config.refreshOnHistoryMiss = true;
      htmx.config.defaultSwapStyle = 'outerHTML';
    }
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
            "X-CSRFToken": getCsrfToken(),
          },
          credentials: "same-origin",
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.theme) {
              // Use Bootstrap color modes via data-bs-theme
              document.documentElement.setAttribute('data-bs-theme', data.theme);
              // Update toggle icon without reload
              try {
                var btn = themeForm.querySelector('button');
                var icon = btn ? btn.querySelector('i') : null;
                if (icon) {
                  if (data.theme === 'dark') {
                    icon.classList.remove('bi-moon');
                    icon.classList.add('bi-brightness-high');
                    btn.title = 'Switch to light mode';
                  } else {
                    icon.classList.remove('bi-brightness-high');
                    icon.classList.add('bi-moon');
                    btn.title = 'Switch to dark mode';
                  }
                }
              } catch (e) {
                // no-op
              }
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
