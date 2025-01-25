import uuid
import time
import hashlib
import json
import base64
import secrets

def generate_poToken(secret_key):
    """
    Generate a serviceIntegrityDimensions.poToken.
    
    Args:
        secret_key (str): A secret key used to sign the token.
    
    Returns:
        str: The generated poToken.
    """
    # Create a unique identifier
    unique_id = str(uuid.uuid4())
    
    # Get the current timestamp
    timestamp = int(time.time())
    
    # Create a payload with the unique ID and timestamp
    payload = {
        "uid": unique_id,
        "ts": timestamp
    }
    
    # Convert the payload to a JSON string
    payload_json = json.dumps(payload)
    
    # Sign the payload using the secret key
    signature = hashlib.sha256((payload_json + secret_key).encode()).hexdigest()
    
    # Combine the payload and signature to create the token
    token = base64.b64encode(f"{payload_json}.{signature}".encode()).decode()
    
    return token

def generate_visitorData():
    """
    Generate context.client.visitorData.
    
    Returns:
        str: The generated visitorData.
    """
    # Create a unique identifier for the visitor
    visitor_id = str(uuid.uuid4())
    
    # Get the current timestamp
    timestamp = int(time.time())
    
    # Create a visitor data object
    visitor_data = {
        "visitorId": visitor_id,
        "timestamp": timestamp
    }
    
    # Convert the visitor data to a JSON string
    visitor_data_json = json.dumps(visitor_data)
    
    # Encode the visitor data in base64
    visitor_data_encoded = base64.b64encode(visitor_data_json.encode()).decode()
    
    return visitor_data_encoded

# Example usage

# Generate a 32-byte (256-bit) cryptographically secure random key
secret_key = secrets.token_urlsafe(32)

#secret_key = "your_secret_key_here"
poToken = generate_poToken(secret_key)
visitorData = generate_visitorData()

print("serviceIntegrityDimensions.poToken:", poToken)
print("context.client.visitorData:", visitorData)