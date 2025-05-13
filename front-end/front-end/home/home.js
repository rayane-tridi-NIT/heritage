document.addEventListener("DOMContentLoaded", function () {
    const filterBtn = document.getElementById("filterBtn");
    const filterMenu = document.getElementById("filterMenu");
    const applyFilter = document.getElementById("applyFilter");

    // Afficher/Masquer le menu avec effet déroulant
    filterBtn.addEventListener("click", function () {
        filterMenu.classList.toggle("show");
    });

    // Appliquer le filtre
    applyFilter.addEventListener("click", function () {
        let selectedCategories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
                                      .map(checkbox => checkbox.value);

        document.querySelectorAll(".item").forEach(item => {
            item.style.display = selectedCategories.length === 0 || selectedCategories.includes(item.dataset.category)
                                 ? "block"
                                 : "none";
        });
    });
});
// Fetch locations from PHP backend
async function loadLocations(category = null) {
    let url = '/backend/api/locations.php';
    if (category) {
        url += `?category=${category}`;
    }
    
    try {
        const response = await fetch(url);
        const locations = await response.json();
        
        // Update your gallery dynamically
        const gallery = document.querySelector('.gallery');
        gallery.innerHTML = '';
        
        locations.forEach(location => {
            gallery.innerHTML += `
                <div class="gallery-item" data-category="${location.category}">
                    <img src="${location.image_path || 'placeholder.jpg'}" alt="${location.title}">
                    <h3>${location.title}</h3>
                    <p>${location.city}</p>
                </div>
            `;
        });
    } catch (error) {
        console.error('Error loading locations:', error);
    }
}

// Call this when page loads or filters change
document.addEventListener('DOMContentLoaded', () => {
    loadLocations();
});
// In home.js
document.getElementById('applyFilter').addEventListener('click', () => {
    const categories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
      .map(el => el.value);
    
    fetch(`/backend/api/locations.php?category=${categories.join(',')}`)
      .then(res => res.json())
      .then(updateGallery);
  });