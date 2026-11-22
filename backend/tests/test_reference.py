API = "/api/v1"


def test_customers_list_and_get(client):
    rows = client.get(f"{API}/customers").json()
    assert rows and set(rows[0]) == {"customer_id", "full_name"}
    one = client.get(f"{API}/customers/{rows[0]['customer_id']}")
    assert one.status_code == 200 and one.json() == rows[0]


def test_customer_unknown_is_404(client):
    res = client.get(f"{API}/customers/999")
    assert (res.status_code, res.json()["error"]["code"]) == (404, "customer_not_found")


def test_policies_list_filter_and_get(client):
    rows = client.get(f"{API}/policies").json()
    assert rows and isinstance(rows[0]["exclusions"], list)
    cid = rows[0]["customer_id"]
    mine = client.get(f"{API}/policies", params={"customer_id": cid}).json()
    assert mine and all(p["customer_id"] == cid for p in mine)
    assert client.get(f"{API}/policies/{rows[0]['policy_id']}").json() == rows[0]


def test_policy_unknown_is_404(client):
    res = client.get(f"{API}/policies/999")
    assert (res.status_code, res.json()["error"]["code"]) == (404, "policy_not_found")
