from datetime import datetime
from firebase_admin import firestore

db = firestore.client()

class Plant:
    def __init__(self, name, type, user_id):
        self.name = name
        self.type = type
        self.user_id = user_id
        self.moisture_level = 0
        self.temperature = 0
        self.created_at = datetime.now()
        self.last_watered = datetime.now()

    def save(self):
        return db.collection('plants').add({
            'name': self.name,
            'type': self.type,
            'user_id': self.user_id,
            'moisture_level': self.moisture_level,
            'temperature': self.temperature,
            'created_at': self.created_at,
            'last_watered': self.last_watered
        })

    @staticmethod
    def get_user_plants(user_id):
        plants = []
        plants_ref = db.collection('plants').where('user_id', '==', user_id).stream()
        for plant in plants_ref:
            plant_data = plant.to_dict()
            plant_data['id'] = plant.id
            plants.append(plant_data)
        return plants 