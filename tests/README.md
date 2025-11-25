# Playwright Tests

Comprehensive test suite for the Ganorabricks website using Playwright.

## Setup

```bash
npm install
npx playwright install chromium
```

## Running Tests

```bash
# Run all tests
npm test

# Run tests in headed mode (watch browser)
npm run test:headed

# Run tests with UI mode (interactive)
npm run test:ui

# Run only mobile tests
npm run test:mobile

# View test report
npm run test:report
```

## Test Coverage

### Home Page (`tests/home.spec.js`)
- Page loads successfully
- Navigation bar with logo
- All navigation links present
- Hero section content
- "What I Offer" section
- Footer visibility
- Google Analytics tracking

### Navigation (`tests/navigation.spec.js`)
- Navigate between all pages
- Logo click returns to home
- Store links (BrickLink, BrickOwl)
- Tab switching functionality
- Product card display

### Mobile Responsive (`tests/mobile.spec.js`)
- Hamburger menu visibility
- Menu toggle functionality
- Menu closes after navigation
- Responsive layout
- Full-width buttons in mobile menu
- Readable text on mobile
- Single column card layout
- Appropriate spacing

### Accessibility (`tests/accessibility.spec.js`)
- Proper document structure
- Alt text for images
- Proper link text
- Clickable areas of adequate size
- Color contrast
- Proper meta tags
- Descriptive page titles
- Working links

### Performance (`tests/performance.spec.js`)
- Fast page load times
- No console errors
- No broken images
- All CSS and JS files load

## Test Configuration

Tests run on:
- **Desktop**: Chrome (1280x720)
- **Mobile**: Pixel 5 viewport (393x851)

The test server automatically starts on port 8080 before tests run.
