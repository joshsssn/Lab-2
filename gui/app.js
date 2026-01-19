// API Configuration
const API_BASE = '';

// State
let currentUser = null;
let authToken = null;
let selectedItem = null;
let lastTransactionId = null;
let selectedRating = 0;

// DOM Elements
const authSection = document.getElementById('authSection');
const mainContent = document.getElementById('mainContent');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const itemsGrid = document.getElementById('itemsGrid');
const itemModal = document.getElementById('itemModal');
const welcomeText = document.getElementById('welcomeText');
const logoutBtn = document.getElementById('logoutBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkStoredAuth();
});

function setupEventListeners() {
    // Auth tabs
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => switchAuthTab(tab.dataset.tab));
    });

    // Main tabs (Items/Users)
    document.querySelectorAll('.main-tab').forEach(tab => {
        tab.addEventListener('click', () => switchMainView(tab.dataset.view));
    });

    // Forms
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    document.getElementById('createItemForm').addEventListener('submit', handleCreateItem);

    // Logout
    logoutBtn.addEventListener('click', handleLogout);

    // Filters
    document.getElementById('applyFilters').addEventListener('click', loadItems);
    document.getElementById('clearFilters').addEventListener('click', () => {
        document.getElementById('filterKeyword').value = '';
        document.getElementById('filterMinPrice').value = '';
        document.getElementById('filterMaxPrice').value = '';
        loadItems();
    });

    // Modal
    document.querySelector('.close-btn').addEventListener('click', closeModal);
    document.getElementById('buyBtn').addEventListener('click', handlePurchase);
    document.getElementById('submitRating').addEventListener('click', handleRating);

    // User Modal
    document.getElementById('closeUserModal').addEventListener('click', closeUserModal);
    document.getElementById('userModal').addEventListener('click', (e) => {
        if (e.target.id === 'userModal') closeUserModal();
    });

    // Rating stars
    document.querySelectorAll('.star').forEach(star => {
        star.addEventListener('click', () => {
            selectedRating = parseInt(star.dataset.value);
            updateStars();
        });
        star.addEventListener('mouseenter', () => {
            highlightStars(parseInt(star.dataset.value));
        });
    });
    document.querySelector('.rating-stars').addEventListener('mouseleave', updateStars);

    // Close modal on outside click
    itemModal.addEventListener('click', (e) => {
        if (e.target === itemModal) closeModal();
    });
}

// Main View Switching
function switchMainView(view) {
    document.querySelectorAll('.main-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-view="${view}"]`).classList.add('active');

    const itemsView = document.getElementById('itemsView');
    const usersView = document.getElementById('usersView');
    const adminView = document.getElementById('adminView');

    itemsView.style.display = 'none';
    usersView.style.display = 'none';
    adminView.style.display = 'none';

    if (view === 'items') {
        itemsView.style.display = 'block';
    } else if (view === 'users') {
        usersView.style.display = 'block';
        loadUsers();
    } else if (view === 'admin') {
        adminView.style.display = 'block';
    }
}

// Auth Functions
function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

    if (tab === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');
    errorEl.textContent = '';

    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Login failed');
        }

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('username', username);

        await fetchCurrentUser(username);
        showMainContent();
    } catch (error) {
        errorEl.textContent = error.message;
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const errorEl = document.getElementById('registerError');
    const successEl = document.getElementById('registerSuccess');
    errorEl.textContent = '';
    successEl.textContent = '';

    const userData = {
        full_name: document.getElementById('regFullName').value,
        username: document.getElementById('regUsername').value,
        email: document.getElementById('regEmail').value,
        password: document.getElementById('regPassword').value
    };

    try {
        const response = await fetch(`${API_BASE}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Registration failed');
        }

        successEl.textContent = 'Account created! You can now login.';
        registerForm.reset();
        setTimeout(() => switchAuthTab('login'), 1500);
    } catch (error) {
        errorEl.textContent = error.message;
    }
}

async function fetchCurrentUser(username) {
    // Use the /me endpoint to get current user info including ID
    try {
        const response = await fetch(`${API_BASE}/me`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (response.ok) {
            const userData = await response.json();
            currentUser = {
                id: userData.id,
                username: userData.username,
                full_name: userData.full_name,
                email: userData.email,
                rating: userData.rating
            };
            localStorage.setItem('userId', userData.id);
        } else {
            currentUser = { username };
        }
    } catch (e) {
        console.log('Could not fetch user details');
        currentUser = { username };
    }
}

async function checkStoredAuth() {
    const token = localStorage.getItem('authToken');
    const username = localStorage.getItem('username');

    if (token && username) {
        authToken = token;
        // Fetch full user data including ID
        await fetchCurrentUser(username);
        showMainContent();
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    localStorage.removeItem('userId');
    showAuthSection();
}

function showMainContent() {
    authSection.style.display = 'none';
    mainContent.style.display = 'block';
    welcomeText.textContent = `Welcome, ${currentUser.username}`;
    logoutBtn.style.display = 'block';

    // Show admin tab only for admin user
    const adminTab = document.getElementById('adminTab');
    if (currentUser.username === 'admin') {
        adminTab.style.display = 'block';
    } else {
        adminTab.style.display = 'none';
    }

    loadItems();
}

function showAuthSection() {
    authSection.style.display = 'flex';
    mainContent.style.display = 'none';
    welcomeText.textContent = 'Not logged in';
    logoutBtn.style.display = 'none';
    document.getElementById('adminTab').style.display = 'none';
}

// Items Functions
async function loadItems() {
    const keyword = document.getElementById('filterKeyword').value;
    const minPrice = document.getElementById('filterMinPrice').value;
    const maxPrice = document.getElementById('filterMaxPrice').value;

    let url = `${API_BASE}/items?`;
    if (keyword) url += `keyword=${encodeURIComponent(keyword)}&`;
    if (minPrice) url += `min_price=${minPrice}&`;
    if (maxPrice) url += `max_price=${maxPrice}&`;

    itemsGrid.innerHTML = '<p class="loading">Loading items...</p>';

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load items');

        const items = await response.json();
        renderItems(items);
    } catch (error) {
        itemsGrid.innerHTML = `<p class="error-msg">${error.message}</p>`;
    }
}

function renderItems(items) {
    if (items.length === 0) {
        itemsGrid.innerHTML = '<p class="loading">No items available</p>';
        return;
    }

    itemsGrid.innerHTML = items.map(item => `
        <div class="item-card" onclick="openItemModal(${item.id}, '${escapeHtml(item.name)}', '${escapeHtml(item.description || '')}', ${item.price}, ${item.owner_id}, '${item.status}')">
            <h3>${escapeHtml(item.name)}</h3>
            <p class="description">${escapeHtml(item.description || 'No description')}</p>
            <p class="price">$${parseFloat(item.price).toFixed(2)}</p>
            <span class="status ${item.status.toLowerCase()}">${item.status}</span>
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

async function openItemModal(id, name, description, price, ownerId, status) {
    selectedItem = { id, name, description, price, ownerId, status };

    document.getElementById('modalItemName').textContent = name;
    document.getElementById('modalItemDescription').textContent = description || 'No description';
    document.getElementById('modalItemPrice').textContent = parseFloat(price).toFixed(2);

    // Fetch seller info
    const sellerNameEl = document.getElementById('modalSellerName');
    sellerNameEl.textContent = 'Loading...';
    sellerNameEl.onclick = null;

    try {
        const response = await fetch(`${API_BASE}/users/${ownerId}`);
        if (response.ok) {
            const seller = await response.json();
            sellerNameEl.textContent = seller.full_name;
            sellerNameEl.onclick = () => {
                closeModal();
                openUserModal(seller.id, seller.full_name, seller.username, seller.email, seller.rating);
            };
        } else {
            sellerNameEl.textContent = `User #${ownerId}`;
        }
    } catch (e) {
        sellerNameEl.textContent = `User #${ownerId}`;
    }

    const buyBtn = document.getElementById('buyBtn');
    const ratingSection = document.getElementById('ratingSection');
    const modalError = document.getElementById('modalError');
    const modalSuccess = document.getElementById('modalSuccess');

    modalError.textContent = '';
    modalSuccess.textContent = '';
    ratingSection.style.display = 'none';

    // Reset buy button state
    buyBtn.textContent = 'Buy Now';
    buyBtn.disabled = false;

    if (status === 'Available') {
        buyBtn.style.display = 'block';
    } else {
        buyBtn.style.display = 'none';
    }

    itemModal.classList.add('active');
}

function closeModal() {
    itemModal.classList.remove('active');
    selectedItem = null;
    lastTransactionId = null;
    selectedRating = 0;
    updateStars();

    // Reset buy button
    const buyBtn = document.getElementById('buyBtn');
    buyBtn.textContent = 'Buy Now';
    buyBtn.disabled = false;
}

// Purchase
async function handlePurchase() {
    if (!selectedItem || !authToken) return;

    const modalError = document.getElementById('modalError');
    const modalSuccess = document.getElementById('modalSuccess');
    const buyBtn = document.getElementById('buyBtn');

    modalError.textContent = '';
    modalSuccess.textContent = '';
    buyBtn.disabled = true;
    buyBtn.textContent = 'Processing...';

    try {
        // Check if we have the user ID
        if (!currentUser || !currentUser.id) {
            // Try to fetch it again
            await fetchCurrentUser(currentUser?.username);
            if (!currentUser || !currentUser.id) {
                throw new Error('Please log out and log in again');
            }
        }

        const response = await fetch(`${API_BASE}/purchases`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                buyer_id: currentUser.id,
                item_id: selectedItem.id
            })
        });

        const data = await response.json();

        if (response.ok) {
            lastTransactionId = data.id;
            modalSuccess.textContent = 'Purchase successful! You can now rate the seller.';
            buyBtn.style.display = 'none';
            document.getElementById('ratingSection').style.display = 'block';
            loadItems(); // Refresh items
        } else {
            throw new Error(data.detail || 'Purchase failed');
        }
    } catch (error) {
        modalError.textContent = error.message;
        buyBtn.disabled = false;
        buyBtn.textContent = 'Buy Now';
    }
}

// Rating
function highlightStars(rating) {
    document.querySelectorAll('.star').forEach((star, i) => {
        star.classList.toggle('active', i < rating);
    });
}

function updateStars() {
    highlightStars(selectedRating);
}

async function handleRating() {
    if (!lastTransactionId || selectedRating === 0) {
        document.getElementById('modalError').textContent = 'Please select a rating';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/ratings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                transaction_id: lastTransactionId,
                score: selectedRating
            })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Rating failed');
        }

        document.getElementById('modalSuccess').textContent = 'Rating submitted! Thank you.';
        document.getElementById('ratingSection').style.display = 'none';
        setTimeout(closeModal, 1500);
    } catch (error) {
        document.getElementById('modalError').textContent = error.message;
    }
}

// Create Item
async function handleCreateItem(e) {
    e.preventDefault();

    const errorEl = document.getElementById('createItemError');
    const successEl = document.getElementById('createItemSuccess');
    errorEl.textContent = '';
    successEl.textContent = '';

    const itemData = {
        name: document.getElementById('itemName').value,
        description: document.getElementById('itemDescription').value,
        price: parseFloat(document.getElementById('itemPrice').value),
        status: 'Available',
        owner_id: 1 // Will be overridden by backend
    };

    try {
        const response = await fetch(`${API_BASE}/items`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(itemData)
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to create item');
        }

        successEl.textContent = 'Item listed successfully!';
        document.getElementById('createItemForm').reset();
        loadItems();
    } catch (error) {
        errorEl.textContent = error.message;
    }
}

// Users Functions
async function loadUsers() {
    const usersGrid = document.getElementById('usersGrid');
    usersGrid.innerHTML = '<p class="loading">Loading users...</p>';

    try {
        // Fetch users by iterating (API doesn't have a list all endpoint)
        const users = [];
        for (let i = 1; i <= 52; i++) {
            try {
                const response = await fetch(`${API_BASE}/users/${i}`);
                if (response.ok) {
                    users.push(await response.json());
                }
            } catch (e) {
                // User doesn't exist, continue
            }
        }
        renderUsers(users);
    } catch (error) {
        usersGrid.innerHTML = `<p class="error-msg">${error.message}</p>`;
    }
}

function renderUsers(users) {
    const usersGrid = document.getElementById('usersGrid');

    if (users.length === 0) {
        usersGrid.innerHTML = '<p class="loading">No users found</p>';
        return;
    }

    usersGrid.innerHTML = users.map(user => `
        <div class="user-card" onclick="openUserModal(${user.id}, '${escapeHtml(user.full_name)}', '${escapeHtml(user.username)}', '${escapeHtml(user.email)}', ${user.rating})">
            <div class="avatar">👤</div>
            <h3>${escapeHtml(user.full_name)}</h3>
            <p class="username">@${escapeHtml(user.username)}</p>
            <p class="rating">⭐ ${parseFloat(user.rating).toFixed(1)}</p>
        </div>
    `).join('');
}

async function openUserModal(userId, fullName, username, email, rating) {
    document.getElementById('userModalName').textContent = fullName;
    document.getElementById('userModalRating').textContent = parseFloat(rating).toFixed(1);
    document.getElementById('userModalEmail').textContent = email;

    const userItemsGrid = document.getElementById('userItemsGrid');
    userItemsGrid.innerHTML = '<p class="loading">Loading items...</p>';

    document.getElementById('userModal').classList.add('active');

    try {
        const response = await fetch(`${API_BASE}/items/seller/${userId}`);
        if (!response.ok) throw new Error('Failed to load items');

        const items = await response.json();

        if (items.length === 0) {
            userItemsGrid.innerHTML = '<p class="loading">No items listed</p>';
        } else {
            userItemsGrid.innerHTML = items.map(item => `
                <div class="item-card" onclick="closeUserModal(); openItemModal(${item.id}, '${escapeHtml(item.name)}', '${escapeHtml(item.description || '')}', ${item.price}, ${item.owner_id}, '${item.status}')">
                    <h3>${escapeHtml(item.name)}</h3>
                    <p class="description">${escapeHtml(item.description || 'No description')}</p>
                    <p class="price">$${parseFloat(item.price).toFixed(2)}</p>
                    <span class="status ${item.status.toLowerCase()}">${item.status}</span>
                </div>
            `).join('');
        }
    } catch (error) {
        userItemsGrid.innerHTML = `<p class="error-msg">${error.message}</p>`;
    }
}

function closeUserModal() {
    document.getElementById('userModal').classList.remove('active');
}

// ==================== ADMIN FUNCTIONS ====================

async function adminGetUser() {
    const userId = document.getElementById('adminUserId').value;
    const resultEl = document.getElementById('adminUserResult');

    if (!userId) {
        resultEl.textContent = 'Please enter a User ID';
        resultEl.style.color = '#ff6b6b';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/users/${userId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();

        if (response.ok) {
            resultEl.textContent = JSON.stringify(data, null, 2);
            resultEl.style.color = '#51cf66';
            // Pre-fill update form
            document.getElementById('adminUserFullName').value = data.full_name || '';
            document.getElementById('adminUserUsername').value = data.username || '';
            document.getElementById('adminUserEmail').value = data.email || '';
        } else {
            resultEl.textContent = data.detail || 'User not found';
            resultEl.style.color = '#ff6b6b';
        }
    } catch (error) {
        resultEl.textContent = error.message;
        resultEl.style.color = '#ff6b6b';
    }
}

async function adminDeleteUser() {
    const userId = document.getElementById('adminUserId').value;
    const resultEl = document.getElementById('adminUserResult');

    if (!userId) {
        resultEl.textContent = 'Please enter a User ID';
        resultEl.style.color = '#ff6b6b';
        return;
    }

    if (!confirm(`Are you sure you want to delete user ${userId}?`)) return;

    try {
        const response = await fetch(`${API_BASE}/users/${userId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();

        if (response.ok) {
            resultEl.textContent = 'User deleted successfully';
            resultEl.style.color = '#51cf66';
        } else {
            resultEl.textContent = data.detail || 'Delete failed';
            resultEl.style.color = '#ff6b6b';
        }
    } catch (error) {
        resultEl.textContent = error.message;
        resultEl.style.color = '#ff6b6b';
    }
}

async function adminUpdateUser() {
    const userId = document.getElementById('adminUserId').value;
    const resultEl = document.getElementById('adminUserResult');

    if (!userId) {
        resultEl.textContent = 'Please enter a User ID first';
        resultEl.style.color = '#ff6b6b';
        return;
    }

    const updateData = {};
    const fullName = document.getElementById('adminUserFullName').value;
    const username = document.getElementById('adminUserUsername').value;
    const email = document.getElementById('adminUserEmail').value;
    const password = document.getElementById('adminUserPassword').value;

    if (fullName) updateData.full_name = fullName;
    if (username) updateData.username = username;
    if (email) updateData.email = email;
    if (password) updateData.password = password;

    if (Object.keys(updateData).length === 0) {
        resultEl.textContent = 'Please fill in at least one field to update';
        resultEl.style.color = '#ff6b6b';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(updateData)
        });
        const data = await response.json();

        if (response.ok) {
            resultEl.textContent = 'User updated:\n' + JSON.stringify(data, null, 2);
            resultEl.style.color = '#51cf66';
        } else {
            resultEl.textContent = data.detail || 'Update failed';
            resultEl.style.color = '#ff6b6b';
        }
    } catch (error) {
        resultEl.textContent = error.message;
        resultEl.style.color = '#ff6b6b';
    }
}

async function adminGetItemsBySeller() {
    const sellerId = document.getElementById('adminItemId').value;
    const resultEl = document.getElementById('adminItemResult');

    if (!sellerId) {
        resultEl.textContent = 'Please enter a Seller ID';
        resultEl.style.color = '#ff6b6b';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/items/seller/${sellerId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();

        if (response.ok) {
            resultEl.textContent = `Found ${data.length} items:\n` + JSON.stringify(data, null, 2);
            resultEl.style.color = '#51cf66';
        } else {
            resultEl.textContent = data.detail || 'Error fetching items';
            resultEl.style.color = '#ff6b6b';
        }
    } catch (error) {
        resultEl.textContent = error.message;
        resultEl.style.color = '#ff6b6b';
    }
}

async function adminUpdateItem() {
    const itemId = document.getElementById('adminItemId').value;
    const resultEl = document.getElementById('adminItemResult');

    if (!itemId) {
        resultEl.textContent = 'Please enter an Item ID';
        resultEl.style.color = '#ff6b6b';
        return;
    }

    const updateData = {};
    const name = document.getElementById('adminItemName').value;
    const price = document.getElementById('adminItemPrice').value;
    const desc = document.getElementById('adminItemDesc').value;
    const status = document.getElementById('adminItemStatus').value;

    if (name) updateData.name = name;
    if (price) updateData.price = parseFloat(price);
    if (desc) updateData.description = desc;
    if (status) updateData.status = status;

    if (Object.keys(updateData).length === 0) {
        resultEl.textContent = 'Please fill in at least one field to update';
        resultEl.style.color = '#ff6b6b';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/items/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(updateData)
        });
        const data = await response.json();

        if (response.ok) {
            resultEl.textContent = 'Item updated:\n' + JSON.stringify(data, null, 2);
            resultEl.style.color = '#51cf66';
            loadItems(); // Refresh main list
        } else {
            resultEl.textContent = data.detail || 'Update failed';
            resultEl.style.color = '#ff6b6b';
        }
    } catch (error) {
        resultEl.textContent = error.message;
        resultEl.style.color = '#ff6b6b';
    }
}

async function adminDirectApiCall() {
    const method = document.getElementById('apiMethod').value;
    const endpoint = document.getElementById('apiEndpoint').value;
    const bodyText = document.getElementById('apiBody').value;
    const resultEl = document.getElementById('apiResult');

    if (!endpoint) {
        resultEl.textContent = 'Please enter an endpoint (e.g., /users/1)';
        resultEl.style.color = '#ff6b6b';
        return;
    }

    const options = {
        method: method,
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    };

    if ((method === 'POST' || method === 'PUT') && bodyText) {
        options.headers['Content-Type'] = 'application/json';
        try {
            options.body = JSON.stringify(JSON.parse(bodyText));
        } catch (e) {
            resultEl.textContent = 'Invalid JSON body';
            resultEl.style.color = '#ff6b6b';
            return;
        }
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await response.json();

        resultEl.textContent = `Status: ${response.status}\n\n${JSON.stringify(data, null, 2)}`;
        resultEl.style.color = response.ok ? '#51cf66' : '#ff6b6b';
    } catch (error) {
        resultEl.textContent = error.message;
        resultEl.style.color = '#ff6b6b';
    }
}
