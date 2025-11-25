# Ganorabricks Store

Official website for Ganorabricks - Premium LEGO® Parts & Custom 3D Prints.

## 🌐 Live Site

Visit [ganorabricks.com](https://ganorabricks.com)

## 📋 About

Ganorabricks offers:
- **Thousands of authentic LEGO® Parts and sets** - Available on BrickLink & BrickOwl
- **3D-Printed stands & organizers** - For collectors and display builders
- **Custom 3D print requests** - Unique solutions for your needs
- **Pick a Brick Wall service** - For those without a nearby LEGO® store

## 🛠️ Tech Stack

- **Frontend**: Vanilla HTML, CSS, JavaScript
- **Testing**: Playwright
- **Analytics**: Google Analytics
- **Hosting**: GitHub Pages

## 📁 Project Structure

```
Store/
├── docs/                    # Website files (GitHub Pages)
│   ├── index.html          # Home page
│   ├── lego-parts.html     # LEGO parts catalog
│   ├── 3dprints.html       # 3D prints showcase
│   ├── pab-service.html    # Pick a Brick service
│   ├── navbar.html         # Reusable navigation
│   ├── footer.html         # Reusable footer
│   ├── style.css           # Global styles
│   ├── script.js           # JavaScript utilities
│   ├── assets/             # Images and media
│   └── products/           # Product detail pages
├── tests/                   # Playwright test suite
│   ├── home.spec.js
│   ├── navigation.spec.js
│   ├── mobile.spec.js
│   ├── accessibility.spec.js
│   └── performance.spec.js
├── playwright.config.js
└── package.json
```

## 🚀 Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm

### Installation

```bash
# Clone the repository
git clone https://github.com/ganorabricks-affilho/Store.git
cd Store

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install chromium
```

### Local Development

```bash
# Start local server
cd docs
python3 -m http.server 8080

# Visit http://localhost:8080
```

## 🧪 Testing

```bash
# Run all tests
npm test

# Run specific test file
npm test -- tests/home.spec.js

# Run mobile tests only
npm run test:mobile

# View test report
npm run test:report
```

### Test Coverage

- ✅ Home page functionality
- ✅ Navigation between pages
- ✅ Mobile responsive design (hamburger menu)
- ✅ Accessibility (WCAG guidelines)
- ✅ SEO meta tags
- ✅ Performance benchmarks

## 📱 Features

### Responsive Design
- Mobile-first approach
- Hamburger menu for mobile devices
- Adaptive layouts for all screen sizes

### Accessibility
- WCAG 2.1 compliant
- Semantic HTML structure
- Proper ARIA labels
- Keyboard navigation support

### Performance
- Fast page load times
- Optimized images
- Minimal JavaScript
- Efficient CSS

## 🔗 External Links

- [BrickLink Store](https://store.bricklink.com/Ganorabricks)
- [BrickOwl Store](https://ganorabricks.brickowl.com/)

## 📞 Contact

**Email**: [ganorabricks@icloud.com](mailto:ganorabricks@icloud.com?subject=General%20Inquiry)

## 📄 License

© 2025 Ganorabricks — All Rights Reserved

LEGO® is a trademark of the LEGO Group, which does not sponsor or endorse this site.

## 🤝 Contributing

This is a personal business website. For inquiries about products or services, please contact via email.
