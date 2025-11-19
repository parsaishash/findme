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
    const collapseThreshold = 150; // pixels

    if (!sidebar || !resizeHandle || !toggleButton) return;

    const savedWidthRaw = localStorage.getItem('sidebar-width');
    let lastValidWidth = savedWidthRaw ? parseInt(savedWidthRaw, 10) : 256;
    if (!Number.isFinite(lastValidWidth)) {
      lastValidWidth = 256;
    }

    let collapsed = localStorage.getItem('sidebar-collapsed') === 'true';

    const icon = toggleButton.querySelector('i');

    const clampWidth = (value) => {
      const min = 160;
      const max = 320;
      return Math.min(Math.max(value, min), max);
    };

    const applySidebarState = () => {
      if (collapsed) {
        sidebar.classList.add('collapsed');
        sidebar.style.width = '4.5rem';
        if (icon) icon.className = 'bi bi-chevron-right';
        localStorage.setItem('sidebar-collapsed', 'true');
      } else {
        lastValidWidth = clampWidth(lastValidWidth);
        sidebar.classList.remove('collapsed');
        sidebar.style.width = `${lastValidWidth}px`;
        if (icon) icon.className = 'bi bi-chevron-left';
        localStorage.setItem('sidebar-collapsed', 'false');
        localStorage.setItem('sidebar-width', lastValidWidth);
      }
    };

    applySidebarState();

    let isResizing = false;

    resizeHandle.addEventListener('mousedown', function () {
      if (collapsed) return;
      isResizing = true;
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', function (e) {
      if (!isResizing) return;

      const rect = sidebar.getBoundingClientRect();
      const newWidth = e.clientX - rect.left;

      if (newWidth < collapseThreshold) {
        collapsed = true;
        applySidebarState();
        return;
      }

      if (newWidth <= 400) {
        lastValidWidth = clampWidth(newWidth);
        if (collapsed) {
          collapsed = false;
        }
        applySidebarState();
      }
    });

    document.addEventListener('mouseup', function () {
      if (isResizing) {
        isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    });

    toggleButton.addEventListener('click', function () {
      if (!collapsed) {
        const currentWidth = parseInt(sidebar.style.width, 10);
        if (!Number.isNaN(currentWidth)) {
          lastValidWidth = currentWidth;
        }
      }
      collapsed = !collapsed;
      applySidebarState();
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

    // Persist preferred download format and rewrite links on click
    const preferredKey = "download-format";
    function setPreferredFormat(fmt) {
      try { localStorage.setItem(preferredKey, fmt); } catch (e) {}
    }
    function getPreferredFormat() {
      try { return localStorage.getItem(preferredKey) || "raw"; } catch (e) { return "raw"; }
    }
    document.body.addEventListener("click", function (ev) {
      const link = ev.target.closest("a[data-download]");
      if (!link) return;
      let fmt = link.getAttribute("data-format") || "raw";
      if (fmt === "preferred") {
        fmt = getPreferredFormat();
      }
      setPreferredFormat(fmt);
      // If user prefers raw, ensure no format parameter; otherwise append ?format=...
      try {
        const url = new URL(link.href, window.location.origin);
        if (fmt === "raw") {
          url.searchParams.delete("format");
        } else {
          url.searchParams.set("format", fmt);
        }
        link.href = url.toString();
      } catch (e) {}
    }, true);

    // Optional: mark default download option in dropdowns
    const preferred = getPreferredFormat();
    document.querySelectorAll("a[data-download]").forEach((a) => {
      let afmt = a.getAttribute("data-format") || "raw";
      if (afmt === "preferred") afmt = preferred;
      if (afmt === preferred) {
        a.classList.add("active");
      }
    });

    // Download Job modal wiring
    const jobModal = document.getElementById("jobModal");
    if (jobModal) {
      jobModal.addEventListener("show.bs.modal", function (event) {
        const trigger = event.relatedTarget;
        const pathField = jobModal.querySelector('input[name="target_path"]');
        const label = jobModal.querySelector('[data-job-path]');
        const path = trigger ? (trigger.getAttribute("data-path") || "") : "";
        if (pathField) pathField.value = path;
        if (label) label.textContent = path || "/";
      });
      const jobForm = jobModal.querySelector('form[data-async-job]');
      handleAsyncForm(jobForm, function (data) {
        if (data && data.success) {
          showToast("Job created: #" + data.job_id);
          jobModal.querySelector('input[name="source"]').value = "";
        } else {
          showToast("Unable to create job");
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

    document.querySelectorAll(".theme-toggle-form").forEach(function (themeForm) {
      themeForm.addEventListener("submit", function (event) {
        event.preventDefault();
        var tokenInput = themeForm.querySelector('input[name="csrfmiddlewaretoken"]');
        var csrfToken = tokenInput ? tokenInput.value : getCsrfToken();
        var headers = {
          "X-Requested-With": "XMLHttpRequest",
        };
        if (csrfToken) {
          headers["X-CSRFToken"] = csrfToken;
        }
        fetch(themeForm.action, {
          method: "POST",
          headers: headers,
          credentials: "same-origin",
        })
          .then((response) => response.json())
          .then((data) => {
            if (!data.theme) {
              return;
            }

            document.documentElement.setAttribute('data-bs-theme', data.theme);

            document.querySelectorAll('.theme-toggle-form button').forEach(function (btn) {
              var icon = btn.querySelector('i');
              if (!icon) {
                return;
              }
              if (data.theme === 'dark') {
                icon.classList.remove('bi-moon');
                icon.classList.add('bi-brightness-high');
                btn.title = 'Switch to light mode';
              } else {
                icon.classList.remove('bi-brightness-high');
                icon.classList.add('bi-moon');
                btn.title = 'Switch to dark mode';
              }
            });
          })
          .catch(() => {
            showToast("Unable to toggle theme");
          });
      });
    });

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
