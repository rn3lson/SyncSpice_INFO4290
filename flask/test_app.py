import pytest
from app import app, initialize_db, add_weight_reading, get_latest_reading

@pytest.fixture
def client(temp_path, monkeypatch):
   
    #Create a temporary database file path within a temporary directory
    db_path = temp_path / "test_spice.db"
    
    #Use monkeypatch to replace the global DATABASE variable in app.py for the duration of the test.
    monkeypatch.setattr('app.DATABASE', str(db_path))
    
    #Initialize the schema in our new temporary database
    initialize_db()
    
    #Configure the Flask app for testing mode
    app.config['TESTING'] = True
    
    #Yield the test client, which can be used to make requests to the app
    with app.test_client() as client:
        yield client

def test_add_last_reading(client):
  
    #Add data directly to the test database using made previously fuction
    add_weight_reading(100.00)
    response = client.get('/latest_weight')
    json_data = response.get_json()
    assert json_data['weight'] == 100.00
    
    add_weight_reading(50.00)
    response = client.get('/latest_weight')
    json_data = response.get_json()
    assert json_data['weight'] == 50.00

