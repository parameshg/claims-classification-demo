BASE = "/api/v1/claims"
NEW = {
    "customer_id": 1,
    "policy_id": 1,
    "filing_date": "2026-11-20",
    "fnol_text": "Someone smashed my passenger window overnight.",
    "police_report_number": None,
}


def test_submit_creates_claim(client):
    res = client.post(BASE, json=NEW)
    assert res.status_code == 201
    body = res.json()
    assert body["claim_id"] > 0
    assert body["fnol_text"] == NEW["fnol_text"]
    assert body["police_report_number"] is None
    assert client.get(f"{BASE}/{body['claim_id']}").status_code == 200


def test_submit_without_optional_report(client):
    data = {k: v for k, v in NEW.items() if k != "police_report_number"}
    assert client.post(BASE, json=data).status_code == 201


def test_submit_missing_field_is_400(client):
    data = {k: v for k, v in NEW.items() if k != "fnol_text"}
    res = client.post(BASE, json=data)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "invalid_request"


def test_submit_blank_text_and_bad_date_are_400(client):
    assert client.post(BASE, json={**NEW, "fnol_text": "   "}).status_code == 400
    assert client.post(BASE, json={**NEW, "filing_date": "20/11/2026"}).status_code == 400


def test_submit_unknown_customer_and_policy_are_404(client):
    res = client.post(BASE, json={**NEW, "customer_id": 999})
    assert (res.status_code, res.json()["error"]["code"]) == (404, "customer_not_found")
    res = client.post(BASE, json={**NEW, "policy_id": 999})
    assert (res.status_code, res.json()["error"]["code"]) == (404, "policy_not_found")


def test_submit_policy_of_other_customer_is_400(client):
    res = client.post(BASE, json={**NEW, "customer_id": 2, "policy_id": 1})
    assert (res.status_code, res.json()["error"]["code"]) == (400, "invalid_request")


def test_list_returns_new_claim_with_null_route(client):
    cid = client.post(BASE, json=NEW).json()["claim_id"]
    items = client.get(BASE, params={"limit": 200}).json()["items"]
    item = next(i for i in items if i["claim_id"] == cid)
    assert item["route"] is None and item["claim_type"] is None and item["severity"] is None


def test_list_filters_and_paging(client):
    before = client.get(BASE).json()["total"]
    for _ in range(3):
        client.post(BASE, json=NEW)
    assert client.get(BASE).json()["total"] == before + 3
    untriaged = client.get(BASE, params={"triaged": "false"}).json()["total"]
    triaged = client.get(BASE, params={"triaged": "true"}).json()["total"]
    assert untriaged + triaged == before + 3
    page = client.get(BASE, params={"limit": 2, "offset": before + 2}).json()
    assert page["total"] == before + 3 and len(page["items"]) == 1


def test_list_shows_stored_route(client, tmp_path):
    import os
    import sqlite3

    cid = client.post(BASE, json=NEW).json()["claim_id"]
    link = sqlite3.connect(os.environ["CLAIMS_DB"])
    link.execute(
        "INSERT INTO triage_results (claim_id, claim_type, severity, route, explanation) "
        "VALUES (?, 'Glass', 'Low', 'Auto-Approve', 'ok')",
        (cid,),
    )
    link.commit()
    link.close()
    items = client.get(BASE, params={"route": "Auto-Approve"}).json()["items"]
    item = next(i for i in items if i["claim_id"] == cid)
    assert (item["claim_type"], item["severity"], item["route"]) == ("Glass", "Low", "Auto-Approve")


def test_list_rejects_bad_params(client):
    assert client.get(BASE, params={"route": "Nope"}).status_code == 400
    assert client.get(BASE, params={"limit": 201}).status_code == 400
    assert client.get(BASE, params={"limit": 0}).status_code == 400


def test_detail_has_policy_and_history(client):
    cid = client.post(BASE, json={**NEW, "customer_id": 6, "policy_id": 6}).json()["claim_id"]
    body = client.get(f"{BASE}/{cid}").json()
    assert body["claim"]["claim_id"] == cid
    assert body["policy"]["policy_id"] == 6
    assert body["policy"]["exclusions"] == ["commercial use"]
    assert len(body["history"]) >= 3
    assert set(body["history"][0]) == {"history_id", "filing_date", "claim_type"}


def test_detail_unknown_claim_is_404(client):
    res = client.get(f"{BASE}/99999")
    assert res.status_code == 404
    assert res.json() == {"error": {"code": "claim_not_found", "message": "Claim 99999 does not exist."}}


def test_triage_get_returns_stored_result(client):
    import os
    import sqlite3

    cid = client.post(BASE, json=NEW).json()["claim_id"]
    link = sqlite3.connect(os.environ["CLAIMS_DB"])
    link.execute(
        "INSERT INTO triage_results (claim_id, injured, missing_fields, claim_type, route, explanation) "
        "VALUES (?, 0, '[\"incident_date\"]', 'Theft', 'Investigation', 'flagged')",
        (cid,),
    )
    link.execute(
        "INSERT INTO triage_fraud_flags (claim_id, flag) VALUES (?, 'THEFT_NO_POLICE_REPORT')",
        (cid,),
    )
    link.commit()
    link.close()
    body = client.get(f"{BASE}/{cid}/triage").json()
    assert body["claim_id"] == cid
    assert body["injured"] is False
    assert body["missing_fields"] == ["incident_date"]
    assert body["fraud_flags"] == ["THEFT_NO_POLICE_REPORT"]
    assert body["route"] == "Investigation"


def test_triage_get_404s(client):
    cid = client.post(BASE, json=NEW).json()["claim_id"]
    assert client.get(f"{BASE}/{cid}/triage").status_code == 404
    assert client.get(f"{BASE}/999999/triage").status_code == 404
