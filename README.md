# Ganorabricks Store

Official website for Ganorabricks - Premium LEGO® Parts & Custom 3D Prints.

## 🌐 Live Site

Visit [ganorabricks.com](https://ganorabricks.com)

## 📋 About

Ganorabricks offers:
- **Thousands of authentic LEGO® parts and sets** on BrickLink and BrickOwl
- **Photos of parts $10 and up** on this site, for a closer look
- **3D-printed stands and organizers**, quoted by email
- **Custom 3D print requests**

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
│   ├── part-highlights.html # Photos of parts $10 and up
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

## Parts $10+ from LotLedger

The parts page is built from the BrickLink inventory already stored in LotLedger (`store_inventory`). A lot is included when it is for sale, still in stock, and the unit price is $10.000 or more.

Photos live in `docs/assets/parts/highlights`. Name them with the BrickLink inventory id:

```text
12345678_1.jpg
12345678_2.jpg
```

The number goes up for each extra photo. On the next build, an existing lot keeps its photos and gets a new price. A new lot is added. A lot that is no longer on the list is removed, along with its photos, only after you confirm.

```bash
python3 scripts/build_highlights.py --db ~/Projects/Lotledger/data/lotledger.db
```

To take the photos on a phone connected to the same Wi-Fi as this Mac, leave this running and open the address it prints:

```bash
python3 scripts/build_highlights.py photos
```

BrickLink links open that inventory lot. LotLedger does not store a BrickOwl lot id, so the BrickOwl link searches your store by item number.

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
