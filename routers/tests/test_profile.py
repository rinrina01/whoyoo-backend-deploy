from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)


class TestModifyUser:

    #Test if successful when all the information come
    def test_modify_user(self ,client ,seed_user):
        response = client.put(
            f"/users/modify/{seed_user}",
            json={"first_name": "Alice Updated", "email": "alice_new@example.com", "last_name": "Dupolirier","description": "J'aime le curry"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["first_name"] == "Alice Updated"
        assert data[0]["email"] == "alice_new@example.com"
        assert data[0]["last_name"] == "Dupolirier"
        assert data[0]["description"] == "J'aime le curry"

    #Test if successful when not all the datas come
    #To pass it I had to exclude none field
    def test_modify_user_partial_update(self, client, seed_user):
        response = client.put(
            f"/users/modify/{seed_user}",
            json={"first_name": "Bob", "email": "alice@example.com"}
        )
        assert response.status_code == 200
        assert response.json()[0]["first_name"] == "Bob"

    #Test that try what happen if connexion is lost
    #Had to add try except to make this test work
    def test_modify_user_db_connection_lost(self, client, seed_user, db_engine):
        from unittest.mock import patch
        from sqlalchemy.exc import OperationalError

        with patch.object(
                db_engine,
                "begin",
                side_effect=OperationalError("connection lost", None, None)
        ):
            response = client.put(
                f"/users/modify/{seed_user}",
                json={"first_name": "Alice Updated", "email": "alice_new@example.com", "last_name": "Dupolirier",
                      "description": "J'aime le curry"}
            )

        assert response.status_code == 500

    #Test what happened if all the fields are none
    #Had to add a raise to the HTTP exception
    def test_modify_user_all_fields_empty(self, client, seed_user):
        response = client.put(
            f"/users/modify/{seed_user}",
            json={}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "No fields to update"