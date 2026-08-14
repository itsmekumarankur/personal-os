from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from ConsentRequests import ConsentRequests
from ConsentDetails import ConsentDetail, FilterData, Fidata, DataLifeSpan, PurposeforDetail, SessionData
from FinancialAnalytics import FinancialAnalytics

global connection
connection = ConsentRequests()

app = FastAPI(title="Account Aggregator Demo API", description="Interactive AA Loan Application & Underwriting Demo")

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
def serve_ui():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Welcome to Account Aggregator Demo API. Open /docs for Swagger UI."}

@app.get("/home", tags=["Welcome Page"])
def welcomePage():
    return {"message": "Welcome to AA Integration Project API!"}

@app.post("/postconsent", tags=["Post Consent"])
def postConsent(consent_detail: ConsentDetail, filter_data: FilterData, freq: Fidata, datalife: DataLifeSpan, purpose: PurposeforDetail):
    consent_details = {
        "Detail": {
            "consentStart": consent_detail.consentStart,
            "consentExpiry": consent_detail.consentExpiry,
            "Customer": consent_detail.Customer,
            "FIDataRange": consent_detail.FIDataRange,
            "consentMode": consent_detail.consentMode,
            "consentTypes": consent_detail.consentTypes,
            "fetchType": consent_detail.fetchType,
            "Frequency": {
                "value": freq.value,
                "unit": freq.unit
            },
            "DataFilter": [
                {
                    "type": filter_data.type,
                    "value": filter_data.value,
                    "operator": filter_data.operator
                }
            ],
            "DataLife": {
                "value": datalife.value,
                "unit": datalife.unit
            },
            "DataConsumer": consent_detail.DataConsumer,
            "Purpose": {
                "Category": purpose.Category,
                "code": purpose.code,
                "text": purpose.text,
                "refUri": purpose.refUri
            },
            "fiTypes": consent_detail.fiTypes
        },
        "redirectUrl": consent_detail.redirectUrl
    }

    response = connection.sendConsentPayload(consent_details)

    if response.get("status_code") in [200, 201]:
        return {
            "status_code": response["status_code"],
            "id": response["response"]["id"],
            "consent_status": response["response"].get("status", "PENDING"),
            "consent_details": response["response"],
            "request_payload": consent_details # Included for Inspector UI
        }
    else:
        return {"error": "Error in sending consent payload"}

@app.get("/getconsent/{consentId}", tags=["Get Consent"])
def getConsent(consentId: str):
    reply = connection.getConsents(consentId)

    if reply.get("response") == 200:
        return {"status_code": reply["response"], "consent_status": reply["data"]}
    else:
        return {"error": "Could not fetch consent details"}

@app.post("/createsession", tags=["Create Data Session"])
def postDataSession(session: SessionData):
    session_data = {
        "consentId": session.consentId,
        "DataRange": {
            "from": session.fromdate,
            "to": session.todate
        },
        "format": session.format
    }
    
    response = connection.sendSessionPayload(session_data)
    if response.get("status_code") in [200, 201]:
        return {
            "status_code": response["status_code"], 
            "session": response["response"],
            "request_payload": session_data # Included for Inspector UI
        }
    else:
        return {"error": "Could not create data session"}

@app.get("/getsession/{sessionId}", tags=["Get FI Data"])
def getDataSession(sessionId: str):
    reply = connection.getSession(sessionId)

    if reply.get("response") == 200:
        return {"status_code": reply["response"], "session": reply["data"]}
    else:
        return {"error": "Could not fetch session details"}

@app.get("/analyze/{sessionId}", tags=["Financial Underwriting Analytics"])
def analyzeSession(sessionId: str):
    reply = connection.getSession(sessionId)
    
    if reply.get("response") == 200:
        session_data = reply.get("data", {})
        fi_data = session_data.get("fiData", {})
        analysis = FinancialAnalytics.analyze_statement(fi_data)
        return {
            "status_code": 200,
            "sessionId": sessionId,
            "analysis": analysis,
            "rawStatement": fi_data
        }
    else:
        raise HTTPException(status_code=404, detail="Session data not found for analysis")

@app.get("/fips", tags=["FIPs List"])
def getFIP():
    reply = connection.getFIPs()

    if reply.get("response") == 200:
        return {"status_code": reply["response"], "fips": reply["data"]}
    else:
        return {"error": "Could not fetch fips data"}
