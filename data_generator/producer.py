import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from faker import Faker
import json
import uuid
from time import sleep

# Function to establish a connection with retry mechanism
def connect_kafka():
    while True:
        try:
            producer = KafkaProducer(bootstrap_servers='kafka-container:49094')
            print("Connected to Kafka!")
            return producer
        except NoBrokersAvailable:
            print("Kafka broker not available. Retrying in 5 seconds...")
            time.sleep(5)

# Initialize Kafka producer with retry
producer = connect_kafka()
faker = Faker()

class DataGenerator:
    @staticmethod
    def get_data():
        return {
            "emp_id": str(uuid.uuid4()),
            "employee_name": faker.name(),
            "department": faker.random_element(elements=('IT', 'HR', 'Sales', 'Marketing')),
            "state": faker.random_element(elements=('CA', 'NY', 'TX', 'FL', 'IL', 'RJ')),
            "salary": faker.random_int(min=10000, max=150000),
            "age": faker.random_int(min=18, max=60),
            "bonus": faker.random_int(min=0, max=100000),
            "ts": faker.date_time().isoformat()
        }

if __name__ == "__main__":
    try:
        while True:
            record = DataGenerator.get_data()
            producer.send('FirstTopic', value=json.dumps(record).encode('utf-8'))
            print(f"Sent record: {record}")
            sleep(5)  # Adjust as needed for continuous data generation
    except KeyboardInterrupt:
        print("Data generation interrupted.")
    finally:
        producer.flush()
        producer.close()

