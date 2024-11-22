const db = firebase.firestore();

function updateSensorData(plantId) {
    const sensorRef = db.collection('sensor_data').doc(plantId);

    sensorRef.onSnapshot((doc) => {
        if (doc.exists) {
            const data = doc.data();
            document.querySelector(`#moisture-${plantId}`).textContent = `${data.moisture}%`;
            document.querySelector(`#temperature-${plantId}`).textContent = `${data.temperature}°C`;
            document.querySelector(`#humidity-${plantId}`).textContent = `${data.humidity}%`;
            document.querySelector(`#light-${plantId}`).textContent = `${data.light} lux`;

            // Add updating animation
            const values = document.querySelectorAll('.sensor-value');
            values.forEach(value => {
                value.classList.add('updating');
                setTimeout(() => value.classList.remove('updating'), 1000);
            });
        }
    });
}

// Initialize real-time updates for each plant
document.addEventListener('DOMContentLoaded', () => {
    const plants = document.querySelectorAll('.plant-card');
    plants.forEach(plant => {
        const plantId = plant.dataset.plantId;
        updateSensorData(plantId);
    });
});