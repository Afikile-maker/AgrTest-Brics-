function updateWeather() {
    const locationSelect = document.getElementById('location');
    
    if (locationSelect.value === 'current') {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(function(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                fetchWeatherData(lat, lon);
            }, function(error) {
                console.error("Error getting location:", error);
                alert("Unable to get your location. Please check your browser settings.");
            });
        } else {
            alert("Geolocation is not supported by your browser");
        }
    } else if (locationSelect.value === 'custom') {
        // You can implement a modal or form for custom location input
        const lat = prompt("Enter latitude:");
        const lon = prompt("Enter longitude:");
        if (lat && lon) {
            fetchWeatherData(lat, lon);
        }
    }
}

function fetchWeatherData(lat, lon) {
    fetch('/update_weather', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ lat, lon })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error fetching weather data: ' + data.error);
            return;
        }
        // Reload the page with new coordinates
        window.location.href = `/weather?lat=${lat}&lon=${lon}`;
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating weather data');
    });
} 