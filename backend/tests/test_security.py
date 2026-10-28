from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hash_verification():
    hashed = hash_password("CorrectHorseBatteryStaple!")
    assert hashed != "CorrectHorseBatteryStaple!"
    assert verify_password("CorrectHorseBatteryStaple!", hashed)
    assert not verify_password("wrong", hashed)

def test_jwt_round_trip():
    token = create_access_token("demo_user", "ADMIN", 5)
    payload = decode_access_token(token)
    assert payload["sub"] == "demo_user"
    assert payload["role"] == "ADMIN"
