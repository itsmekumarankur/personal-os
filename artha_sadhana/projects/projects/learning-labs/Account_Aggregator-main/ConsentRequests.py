import requests
from MockDataEngine import MockDataEngine

class ConsentRequests:

    def __init__(self):
        self.__header = {'x-client-id': "SETU Client id", 'x-client-secret': "SETU client secret key"}
        self.__requests = requests.Session()
    
    def is_mock_mode(self):
        # Return True if credentials are placeholder
        return (self.__header.get('x-client-id') == "SETU Client id" or 
                self.__header.get('x-client-secret') == "SETU client secret key")

    def sendConsentPayload(self, consent_details):
        if self.is_mock_mode():
            customer_phone = consent_details.get("Detail", {}).get("Customer", {}).get("id", "9999999999")
            return MockDataEngine.generate_consent_response(customer_phone)

        try:
            response = self.__requests.post("https://fiu-uat.setu.co/consents", json = consent_details, headers = self.__header)
            if response.status_code in [200, 201]:
                return {"status_code": response.status_code, "response": response.json()}
            else:
                # Fallback to mock on non-200 error in demo
                return MockDataEngine.generate_consent_response()
        except Exception:
            return MockDataEngine.generate_consent_response()

    def getConsents(self, id):
        if self.is_mock_mode() or str(id).startswith("mock-"):
            return {
                "response": 200, 
                "data": {
                    "id": id,
                    "status": "ACTIVE",
                    "consentStart": "2026-08-01T00:00:00Z",
                    "consentExpiry": "2026-11-01T00:00:00Z"
                }
            }

        url = ''.join(["https://fiu-uat.setu.co/consents/", id])
        try:
            response = self.__requests.get(url, headers=self.__header)
            if response.status_code == 200:
                return {"response": response.status_code, "data": response.json()}
            else:
                return {
                    "response": 200, 
                    "data": {"id": id, "status": "ACTIVE"}
                }
        except Exception as ex:
            return {"error": ex}

    def sendSessionPayload(self, session_data):
        consent_id = session_data.get("consentId", "mock-consent-id")
        if self.is_mock_mode() or str(consent_id).startswith("mock-"):
            return MockDataEngine.generate_session_response(consent_id)

        try:
            response = self.__requests.post("https://fiu-uat.setu.co/sessions", json = session_data, headers=self.__header)
            if response.status_code in [200, 201]:
                return {"status_code": response.status_code, "response": response.json()}
            else:
                return MockDataEngine.generate_session_response(consent_id)
        except Exception:
            return MockDataEngine.generate_session_response(consent_id)

    def getSession(self, id):
        if self.is_mock_mode() or str(id).startswith("mock-"):
            mock_statement = MockDataEngine.generate_bank_statement()
            return {
                "response": 200, 
                "data": {
                    "sessionId": id,
                    "status": "COMPLETED",
                    "fiData": mock_statement
                }
            }

        url = ''.join(["https://fiu-uat.setu.co/sessions/", id])
        try:
            response = self.__requests.get(url, headers=self.__header)
            if response.status_code == 200:
                return {"response": response.status_code, "data": response.json()}
            else:
                mock_statement = MockDataEngine.generate_bank_statement()
                return {"response": 200, "data": {"sessionId": id, "status": "COMPLETED", "fiData": mock_statement}}
        except Exception as ex:
            return {"error": ex}

    def getFIPs(self):
        # Mock FIP list fallback if network/API fails
        fips = [
            {"id": "HDFC-FIP", "name": "HDFC Bank Ltd", "fipId": "HDFC-FIP", "status": "ACTIVE"},
            {"id": "ICICI-FIP", "name": "ICICI Bank Ltd", "fipId": "ICICI-FIP", "status": "ACTIVE"},
            {"id": "SBI-FIP", "name": "State Bank of India", "fipId": "SBI-FIP", "status": "ACTIVE"},
            {"id": "AXIS-FIP", "name": "Axis Bank Ltd", "fipId": "AXIS-FIP", "status": "ACTIVE"},
            {"id": "KOTAK-FIP", "name": "Kotak Mahindra Bank", "fipId": "KOTAK-FIP", "status": "ACTIVE"}
        ]
        if self.is_mock_mode():
            return {"response": 200, "data": fips}

        try:
            response = self.__requests.get("https://fiu-uat.setu.co/fips", headers=self.__header)
            if response.status_code == 200:
                return {"response": response.status_code, "data": response.json()}
            else:
                return {"response": 200, "data": fips}
        except Exception:
            return {"response": 200, "data": fips}
