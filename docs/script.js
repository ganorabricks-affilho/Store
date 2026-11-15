// ------------------------------
// SITE CHROME (nav + footer)
// ------------------------------
function initHamburgerMenu() {
    const hamburger = document.querySelector(".hamburger");
    const nav = document.querySelector("nav");

    if (!hamburger || !nav) return;

    hamburger.addEventListener("click", () => {
        const open = nav.classList.toggle("active");
        hamburger.setAttribute("aria-expanded", open ? "true" : "false");
        hamburger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });

    document.querySelectorAll("nav ul a").forEach(link => {
        link.addEventListener("click", () => {
            nav.classList.remove("active");
            hamburger.setAttribute("aria-expanded", "false");
            hamburger.setAttribute("aria-label", "Open menu");
        });
    });

    const path = window.location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll("nav ul a").forEach(link => {
        const file = (link.getAttribute("href") || "").split("/").pop();
        if (file === path) link.setAttribute("aria-current", "page");
    });
}

function sitePrefix() {
    const path = window.location.pathname.replace(/\\/g, "/");
    return /\/(highlights|products)\//.test(path) ? "../" : "";
}

function loadSiteChrome() {
    const jobs = [];
    const navEl = document.getElementById("navbar");
    const footerEl = document.getElementById("footer");
    const prefix = sitePrefix();

    if (navEl) {
        jobs.push(
            fetch(prefix + "navbar.html")
                .then(res => {
                    if (!res.ok) throw new Error("navbar " + res.status);
                    return res.text();
                })
                .then(html => {
                    navEl.innerHTML = html;
                    initHamburgerMenu();
                })
        );
    }

    if (footerEl) {
        jobs.push(
            fetch(prefix + "footer.html")
                .then(res => {
                    if (!res.ok) throw new Error("footer " + res.status);
                    return res.text();
                })
                .then(html => {
                    footerEl.innerHTML = html;
                })
        );
    }

    return Promise.all(jobs);
}

// ------------------------------
// 3D PRINT CATALOG CARDS
// ------------------------------
function createProductCard(params) {
    const {
        image,
        title,
        description,
        link = "#",
        note = ""
    } = params;

    const card = document.createElement("article");
    card.className = "card product-card";

    const subject = encodeURIComponent("Question about " + title);
    const askHref = `mailto:ganorabricks@icloud.com?subject=${subject}`;
    const hasPage = link && link !== "#";
    const media = hasPage
        ? `<a class="product-card-media" href="${link}"><img src="${image}" alt="${title}" loading="lazy"></a>`
        : `<div class="product-card-media"><img src="${image}" alt="${title}" loading="lazy"></div>`;

    card.innerHTML = `
        ${media}
        <h3>${title}</h3>
        ${description ? `<p class="card-copy">${description}</p>` : ""}
        ${note ? `<p class="card-note">${note}</p>` : ""}
        <div class="card-actions">
            ${hasPage ? `<a class="btn-stud" href="${link}">See details</a>` : ""}
            <a class="text-link" href="${askHref}">Ask about this</a>
        </div>
    `;

    return card;
}

function renderProductCards(containerId, cardsData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    cardsData.forEach(cardData => {
        container.appendChild(createProductCard(cardData));
    });
}

// ------------------------------
// EXPENSIVE PART HIGHLIGHTS
// ------------------------------
function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[ch]));
}

function renderHighlights(containerId, items) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.replaceChildren();

    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="empty-gallery">
                <p class="empty-title">Photos coming soon</p>
                <p>When a part is worth a closer look, its photo will show up here. The full inventory stays on BrickLink and BrickOwl.</p>
            </div>
        `;
        return;
    }

    const visible = items.filter(item => item.photos && item.photos.length);
    if (!visible.length) {
        container.innerHTML = `
            <div class="empty-gallery">
                <p class="empty-title">Photos coming soon</p>
                <p>When a part is worth a closer look, its photo will show up here. The full inventory stays on BrickLink and BrickOwl.</p>
            </div>
        `;
        return;
    }

    const grid = document.createElement("div");
    grid.className = "gallery-grid";

    visible.forEach(item => {
        const card = document.createElement("article");
        card.className = "card highlight-card";
        const title = escapeHtml(item.title);
        const photo = (item.photos && item.photos[0]) || item.image;
        const photoHref = item.photo_page || "#";
        const media = photo
            ? `<a class="product-card-media" href="${escapeHtml(photoHref)}"><img src="${escapeHtml(photo)}" alt="${title}" loading="lazy"></a>`
            : `<a class="photo-placeholder" href="${escapeHtml(photoHref)}">No photo yet</a>`;
        const meta = [item.item_no, item.condition, item.qty ? `qty ${item.qty}` : ""].filter(Boolean).join(" · ");
        const links = item.bricklink_url
            ? `<a class="btn-stud" href="${escapeHtml(item.bricklink_url)}" target="_blank" rel="noopener noreferrer">BrickLink</a>
               <a class="btn-stud btn-orange" href="${escapeHtml(item.brickowl_url)}" target="_blank" rel="noopener noreferrer">BrickOwl</a>
               <a class="text-link" href="${escapeHtml(photoHref)}">See photos</a>`
            : "";
        card.innerHTML = `
            ${media}
            <h3>${title}</h3>
            ${meta ? `<p class="card-copy">${escapeHtml(meta)}</p>` : ""}
            ${item.note ? `<p class="card-copy">${escapeHtml(item.note)}</p>` : ""}
            <div class="card-actions">${links}</div>
        `;
        grid.appendChild(card);
    });

    container.appendChild(grid);
}

// ------------------------------
// HIGHLIGHT PHOTO VIEWER
// ------------------------------
function initPhotoLightbox() {
    const lightbox = document.getElementById("photoLightbox");
    const photo = document.getElementById("photoFull");
    const zoomIn = document.getElementById("zoomIn");
    const zoomOut = document.getElementById("zoomOut");
    if (!lightbox || !photo || !zoomIn || !zoomOut) return;

    const minZoom = 1;
    const maxZoom = 4;
    let zoom = 1;
    let opener = null;

    function fittedScale() {
        const naturalWidth = photo.naturalWidth || 1;
        const naturalHeight = photo.naturalHeight || 1;
        const maxWidth = Math.max(window.innerWidth - 32, 1);
        const maxHeight = Math.max(window.innerHeight - 96, 1);
        return Math.min(maxWidth / naturalWidth, maxHeight / naturalHeight, 1);
    }

    function applyZoom() {
        const stage = lightbox.querySelector(".photo-lightbox-stage");
        const scale = fittedScale() * zoom;
        photo.style.width = Math.round(photo.naturalWidth * scale) + "px";
        photo.style.height = Math.round(photo.naturalHeight * scale) + "px";
        zoomOut.disabled = zoom <= minZoom;
        zoomIn.disabled = zoom >= maxZoom;
        requestAnimationFrame(() => {
            stage.scrollLeft = Math.max(0, (stage.scrollWidth - stage.clientWidth) / 2);
            stage.scrollTop = Math.max(0, (stage.scrollHeight - stage.clientHeight) / 2);
        });
    }

    function openPhoto(src, alt, button) {
        opener = button;
        zoom = 1;
        photo.alt = alt;
        photo.src = src;
        lightbox.hidden = false;
        document.body.style.overflow = "hidden";
        if (photo.complete && photo.naturalWidth) applyZoom();
        else photo.addEventListener("load", applyZoom, { once: true });
        zoomIn.focus();
    }

    function closePhoto() {
        if (lightbox.hidden) return;
        lightbox.hidden = true;
        document.body.style.overflow = "";
        photo.removeAttribute("src");
        if (opener) opener.focus();
    }

    document.querySelectorAll(".photo-thumbs button").forEach(button => {
        button.addEventListener("click", () => {
            openPhoto(button.dataset.full, button.getAttribute("aria-label") || "", button);
        });
    });

    zoomIn.addEventListener("click", () => {
        zoom = Math.min(maxZoom, Math.round((zoom + 0.5) * 10) / 10);
        applyZoom();
    });

    zoomOut.addEventListener("click", () => {
        zoom = Math.max(minZoom, Math.round((zoom - 0.5) * 10) / 10);
        applyZoom();
    });

    lightbox.addEventListener("click", event => {
        if (event.target === photo || event.target.closest("button")) return;
        closePhoto();
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") closePhoto();
    });

    window.addEventListener("resize", () => {
        if (!lightbox.hidden) applyZoom();
    });
}

initPhotoLightbox();
