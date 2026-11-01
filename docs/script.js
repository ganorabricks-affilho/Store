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
    return path.includes("/highlights/") ? "../" : "";
}

function loadSiteChrome() {
    const jobs = [];
    const navEl = document.getElementById("navbar");
    const footerEl = document.getElementById("footer");
    const prefix = sitePrefix();

    if (navEl) {
        jobs.push(
            fetch(prefix + "navbar.html")
                .then(res => res.text())
                .then(html => {
                    navEl.innerHTML = html;
                    initHamburgerMenu();
                })
        );
    }

    if (footerEl) {
        jobs.push(
            fetch(prefix + "footer.html")
                .then(res => res.text())
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

    const grid = document.createElement("div");
    grid.className = "gallery-grid";

    items.forEach(item => {
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
            ${item.price ? `<p class="highlight-price">${escapeHtml(item.price)}</p>` : ""}
            <div class="card-actions">${links}</div>
        `;
        grid.appendChild(card);
    });

    container.appendChild(grid);
}
