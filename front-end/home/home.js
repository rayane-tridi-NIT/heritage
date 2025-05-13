document.addEventListener('DOMContentLoaded', () => {
    // Check authentication status
    const token = localStorage.getItem('token');
    const loginLink = document.getElementById('loginLink');
    const logoutBtn = document.getElementById('logoutBtn');

    if (token) {
        loginLink.style.display = 'none';
        logoutBtn.style.display = 'block';
    }

    // Logout functionality
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('token');
        localStorage.removeItem('userEmail');
        window.location.reload();
    });

    // Initialize filter button
    const filterBtn = document.getElementById('filterBtn');
    const filterMenu = document.getElementById('filterMenu');
    
    filterBtn.addEventListener('click', () => {
        filterMenu.classList.toggle('hidden');
    });

    // Load initial locations
    loadLocations();

    // Handle filter application
    document.getElementById('applyFilter').addEventListener('click', () => {
        const selectedCategories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
            .map(checkbox => checkbox.value);
        loadLocations(selectedCategories);
        filterMenu.classList.add('hidden'); // Hide menu after applying filter
    });

    // Add navigation handling
    document.querySelectorAll('.footer-button').forEach(button => {
        button.addEventListener('click', async (e) => {
            const link = button.querySelector('a');
            if (link && link.href.includes('profile.html')) {
                e.preventDefault();
                const token = localStorage.getItem('token');
                
                if (!token) {
                    window.location.href = 'connexion.html';
                    return;
                }

                try {
                    const response = await fetch('http://localhost:8000/api/profile', {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    
                    if (response.ok) {
                        window.location.href = link.href;
                    } else {
                        localStorage.removeItem('token');
                        window.location.href = 'connexion.html';
                    }
                } catch (error) {
                    console.error('Error:', error);
                    localStorage.removeItem('token');
                    window.location.href = 'connexion.html';
                }
            }
        });
    });
});

async function loadLocations(categories = []) {
    try {
        const token = localStorage.getItem('token');
        const headers = {
            'Accept': 'application/json',
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const url = categories.length > 0
            ? `http://localhost:8000/api/locations/?category=${categories.join(',')}`
            : 'http://localhost:8000/api/locations/';
        
        console.log('Attempting to fetch from:', url);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: headers,
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const locations = await response.json();
        console.log('Raw response:', locations);
        
        if (!Array.isArray(locations)) {
            throw new Error('Expected array of locations but got: ' + typeof locations);
        }
        
        const gallery = document.getElementById('locationGallery');
        if (locations.length === 0) {
            gallery.innerHTML = '<div class="no-results">No locations found</div>';
            return;
        }

        gallery.innerHTML = locations.map(location => `
            <div class="gallery-item">
                <img src="${location.image_path}" alt="${location.title}" />
                <div class="caption">${location.title} - ${location.city}</div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading locations:', error);
        document.getElementById('locationGallery').innerHTML = 
            `<div class="error">Error loading locations: ${error.message}</div>`;
    }
}
