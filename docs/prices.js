/**
 * Price Management Utility
 * Centralized source for all product pricing
 */

let pricesData = null;

/**
 * Load prices from the centralized prices.json file
 */
async function loadPrices() {
    if (pricesData) {
        return pricesData;
    }
    
    try {
        // Determine the correct path based on whether we're in a subdirectory
        const basePath = window.location.pathname.includes('/products/') ? '../prices.json' : './prices.json';
        const response = await fetch(basePath);
        pricesData = await response.json();
        return pricesData;
    } catch (error) {
        console.error('Error loading prices:', error);
        return null;
    }
}

/**
 * Get price for a specific 3D print product
 * @param {string} productId - The product ID (e.g., 'stand', 'tray', 'akro-mills-divider')
 * @param {string} format - Price format: 'display' (detailed) or 'card' (short) - default is 'display'
 * @returns {Promise<string>} The price string
 */
async function getPrice(productId, format = 'display') {
    const prices = await loadPrices();
    if (!prices) return 'Contact for pricing';
    
    // Check if it's a 3D print product
    if (prices['3d-prints'][productId]) {
        const priceField = format === 'card' ? 'price' : 'displayPrice';
        return prices['3d-prints'][productId][priceField];
    }
    
    return 'Contact for pricing';
}

/**
 * Get full product info for a 3D print
 * @param {string} productId - The product ID
 * @returns {Promise<Object>} The full product object
 */
async function getProductInfo(productId) {
    const prices = await loadPrices();
    if (!prices) return null;
    
    return prices['3d-prints'][productId] || null;
}

/**
 * Update the price display element with the price for a product
 * @param {string} productId - The product ID
 * @param {string} elementId - The element ID to update (default: 'product-price')
 */
async function setPriceDisplay(productId, elementId = 'product-price') {
    const price = await getPrice(productId);
    const element = document.querySelector(`div.product-price`) || document.getElementById(elementId);
    
    if (element) {
        element.textContent = price;
    }
}

/**
 * Get all 3D print products
 * @returns {Promise<Array>} Array of all 3D print products
 */
async function getAllProducts() {
    const prices = await loadPrices();
    if (!prices) return [];
    
    return Object.values(prices['3d-prints']);
}

/**
 * Get price for a LEGO set
 * @param {string} setId - The set ID (e.g., '5009015', '40764')
 * @returns {Promise<string>} The price string
 */
async function getSetPrice(setId) {
    const prices = await loadPrices();
    if (!prices) return 'Contact for pricing';
    
    if (prices['lego-sets'] && prices['lego-sets'][setId]) {
        return prices['lego-sets'][setId].price;
    }
    
    return 'Contact for pricing';
}

/**
 * Get price for a LEGO part
 * @param {string} partId - The part ID
 * @returns {Promise<string>} The price string
 */
async function getPartPrice(partId) {
    const prices = await loadPrices();
    if (!prices) return 'Contact for pricing';
    
    if (prices['lego-parts'] && prices['lego-parts'][partId]) {
        return prices['lego-parts'][partId].price;
    }
    
    return 'Contact for pricing';
}
