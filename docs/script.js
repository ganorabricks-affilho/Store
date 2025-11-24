// ------------------------------
// HAMBURGER MENU TOGGLE
// ------------------------------
const hamburger = document.querySelector(".hamburger");
const nav = document.querySelector("nav");

hamburger.addEventListener("click", () => {
    nav.classList.toggle("active");
});

// Close menu when clicking a link (mobile)
document.querySelectorAll("nav ul li a").forEach(link => {
    link.addEventListener("click", () => {
        nav.classList.remove("active");
    });
});

// ------------------------------
// CARD FLOATING ANIMATION ON HOVER
// ------------------------------
const cards = document.querySelectorAll(".card");

cards.forEach(card => {
    card.addEventListener("mouseenter", () => {
        card.style.transform = "translateY(-6px)";
        card.style.boxShadow = "0 12px 25px rgba(0,0,0,0.2)";
    });

    card.addEventListener("mouseleave", () => {
        card.style.transform = "translateY(0)";
        card.style.boxShadow = "0 4px 8px rgba(0,0,0,0.1)";
    });
});

// ------------------------------
// SMOOTH SECTION ANIMATION ON SCROLL
// ------------------------------
const sections = document.querySelectorAll("section");

const observerOptions = {
    threshold: 0.1
};

const sectionObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if(entry.isIntersecting){
            entry.target.classList.add("section-visible");
        }
    });
}, observerOptions);

sections.forEach(section => {
    sectionObserver.observe(section);
});

// ------------------------------
// REUSABLE PRODUCT CARD COMPONENT
// ------------------------------
// Generate BrickLink image URL from set number
function getBrickLinkImageUrl(setNumber) {
    // BrickLink uses format: https://img.bricklink.com/ItemImage/SN/0/SETNUMBER-1.png
    const formattedNumber = setNumber.toString().replace(/-/g, '');
    return `https://img.bricklink.com/ItemImage/SN/0/${formattedNumber}-1.png`;
}

// Generate Rebrickable image URL from set number (alternative)
function getRebrickableImageUrl(setNumber) {
    return `https://cdn.rebrickable.com/media/sets/${setNumber}-1.jpg`;
}

function createProductCard(params) {
    const {
        image,
        title,
        description,
        price,
        link = '#',
        imageWidth = '120px',
        setNumber = null,
        useSetImage = false // Set to true to auto-generate image from setNumber
    } = params;

    // Determine image source
    let imageSrc = image;
    if (useSetImage && setNumber) {
        imageSrc = getBrickLinkImageUrl(setNumber);
    }

    const card = document.createElement('div');
    card.className = 'card product-card';
    card.style.cssText = 'display: flex; flex-direction: column; align-items: center; padding: 18px; border-radius: 12px; background: #fff; box-shadow: 0 2px 8px #0002;';

    const linkEl = link !== '#' ? `<a href="${link}" style="width: 100%; text-align: center;">` : '<div style="width: 100%; text-align: center;">';
    const closeLinkEl = link !== '#' ? '</a>' : '</div>';

    card.innerHTML = `
        ${linkEl}
            <img src="${imageSrc}" alt="${title}" style="width: ${imageWidth}; height: ${imageWidth}; object-fit: contain; border-radius: 8px; margin-bottom: 10px;">
        ${closeLinkEl}
        <div style="flex: 1;">
            <p style="margin: 0 0 8px 0; font-weight: bold; text-align: center;">${title}</p>
            ${description ? `<p style="margin: 0 0 8px 0; font-size: 0.95em; color: #444; text-align: center;">${description}</p>` : ''}
        </div>
        <div style="margin-top: auto; font-size: 1.1em; font-weight: bold; color: #0288D1;">${price}</div>
    `;

    return card;
}

// Helper function to create multiple product cards
function renderProductCards(containerId, cardsData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    cardsData.forEach(cardData => {
        const card = createProductCard(cardData);
        container.appendChild(card);
    });
}
