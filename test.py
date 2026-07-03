from db import reviews_collection

reviews_collection.insert_one({
    "product": "iPhone 15",
    "review": "Excellent camera quality",
    "rating": 5,
    "sentiment": "Positive"
})

print("Data Inserted Successfully")