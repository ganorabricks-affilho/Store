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
