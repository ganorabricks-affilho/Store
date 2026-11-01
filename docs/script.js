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

function loadSiteChrome() {
    const jobs = [];
    const navEl = document.getElementById("navbar");
    const footerEl = document.getElementById("footer");

    if (navEl) {
        jobs.push(
            fetch("/navbar.html")
                .then(res => res.text())
                .then(html => {
                    navEl.innerHTML = html;
                    initHamburgerMenu();
                })
        );
    }

    if (footerEl) {
        jobs.push(
            fetch("/footer.html")
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
function renderHighlights(containerId, items) {
    const container = document.getElementById(containerId);
    if (!container) return;

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
        const subject = encodeURIComponent("Question about " + item.title);
        card.innerHTML = `
            <img src="${item.image}" alt="${item.title}" loading="lazy">
            <h3>${item.title}</h3>
            ${item.note ? `<p class="card-copy">${item.note}</p>` : ""}
            <a class="btn-stud" href="mailto:ganorabricks@icloud.com?subject=${subject}">Ask about this part</a>
        `;
        grid.appendChild(card);
    });

    container.appendChild(grid);
}
