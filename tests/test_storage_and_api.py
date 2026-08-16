"""
Unit and integration tests for SQLite persistence, REST API, and FastMCP Server.
"""
import json
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from api.server import create_app
from protocol.db_storage import PersistentEconomyLedger, SQLiteEconomyStorage
from protocol.engine import GeneticFramesProtocol
from protocol import mcp_server


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass



class TestSQLitePersistence:
    def test_wallet_and_frame_persistence_across_instances(self, temp_db):
        # 1. First instance: mint and transact
        ledger1 = PersistentEconomyLedger(db_path=temp_db)
        ledger1.mint_gf("0xAlice", 25.0)
        protocol1 = GeneticFramesProtocol(economy_ledger=ledger1)

        f1 = protocol1.generate("0xAlice")
        f2 = protocol1.generate("0xAlice")

        listing = ledger1.create_listing("0xAlice", f1.frame_id, 4.0)

        # 2. Second instance: reload from same SQLite file
        ledger2 = PersistentEconomyLedger(db_path=temp_db)
        assert ledger2.get_balance("0xAlice") == 23.0 # 25 - 2 burns
        assert len(ledger2.frames) == 2
        assert f1.frame_id in ledger2.frames
        assert ledger2.frames[f1.frame_id].owner_id == "0xAlice"
        assert listing.listing_id in ledger2.listings
        assert ledger2.listings[listing.listing_id].status.value == "active"

        # 3. Buy listing in second instance
        ledger2.mint_gf("0xBob", 10.0)
        trade = ledger2.buy_listing("0xBob", listing.listing_id)
        assert trade.price_gf == 4.0

        # 4. Third instance: verify ownership transferred permanently
        ledger3 = PersistentEconomyLedger(db_path=temp_db)
        assert ledger3.frames[f1.frame_id].owner_id == "0xBob"
        assert len(ledger3.frames[f1.frame_id].provenance_history) >= 2


class TestRestAPI:
    @pytest.fixture
    def client(self, temp_db):
        app = create_app(db_path=temp_db)
        return TestClient(app)

    def test_health_and_protocol_status(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

        r = client.get("/protocol/status")
        assert r.status_code == 200
        data = r.json()
        assert data["epoch"] == 1
        assert data["total_generations"] == 0

    def test_species_pool_endpoint(self, client):
        r = client.get("/species/pool")
        assert r.status_code == 200
        assert r.json()["count"] >= 15

        r_rare = client.get("/species/pool?tier=Rare")
        assert r_rare.status_code == 200
        assert all(s["protocol_tier"] == "Rare" for s in r_rare.json()["species"])

    def test_agent_workflow_and_generation(self, client):
        # 1. Faucet agent
        r_faucet = client.post("/agents/0xAgent_Alpha/faucet", json={"amount": 15.0})
        assert r_faucet.status_code == 200
        assert r_faucet.json()["new_balance"] == 15.0

        # 2. Check balance
        r_bal = client.get("/agents/0xAgent_Alpha/balance")
        assert r_bal.status_code == 200
        assert r_bal.json()["gf_balance"] == 15.0

        # 3. Generate Frame (burns 1 GF)
        r_gen = client.post("/protocol/generate", json={"agent_id": "0xAgent_Alpha", "client_entropy": "seed_1"})
        assert r_gen.status_code == 201
        gen_data = r_gen.json()
        assert gen_data["success"] is True
        frame_id = gen_data["frame_id"]

        # Check updated balance
        r_bal2 = client.get("/agents/0xAgent_Alpha/balance")
        assert r_bal2.json()["gf_balance"] == 14.0

        # 4. Get Frame details, manifest, svg
        r_frame = client.get(f"/frames/{frame_id}")
        assert r_frame.status_code == 200
        assert r_frame.json()["record"]["frame_id"] == frame_id

        r_manifest = client.get(f"/frames/{frame_id}/manifest")
        assert r_manifest.status_code == 200
        assert r_manifest.json()["schema"] == "geneticframes-manifest-v1"

        r_svg = client.get(f"/frames/{frame_id}/svg")
        assert r_svg.status_code == 200
        assert "image/svg+xml" in r_svg.headers["content-type"]
        assert "<svg" in r_svg.text

        # 5. Verify Frame
        r_verify = client.post(f"/frames/{frame_id}/verify")
        assert r_verify.status_code == 200
        assert r_verify.json()["is_valid"] is True

        # 6. List agent frames
        r_my_frames = client.get("/agents/0xAgent_Alpha/frames")
        assert r_my_frames.status_code == 200
        assert r_my_frames.json()["count"] == 1

    def test_marketplace_orderbook_via_api(self, client):
        client.post("/agents/0xSeller/faucet", json={"amount": 10.0})
        client.post("/agents/0xBuyer/faucet", json={"amount": 20.0})

        r_gen = client.post("/protocol/generate", json={"agent_id": "0xSeller"})
        frame_id = r_gen.json()["frame_id"]

        # Create Listing
        r_list = client.post("/market/listings", json={"seller_id": "0xSeller", "frame_id": frame_id, "price_gf": 6.0})
        assert r_list.status_code == 201
        listing_id = r_list.json()["listing_id"]

        # Check market depth
        r_orders = client.get("/market/orders")
        assert r_orders.status_code == 200
        assert len(r_orders.json()["active_listings"]) == 1

        # Buy Listing
        r_buy = client.post(f"/market/listings/{listing_id}/buy", json={"buyer_id": "0xBuyer"})
        assert r_buy.status_code == 200
        assert r_buy.json()["price_gf"] == 6.0

        # Check updated ownership
        r_frame = client.get(f"/frames/{frame_id}")
        assert r_frame.json()["record"]["owner_id"] == "0xBuyer"


class TestFastMCPServerTools:
    def test_mcp_status_and_species_pool(self):
        status_json = json.loads(mcp_server.get_protocol_status())
        assert "epoch" in status_json
        assert "total_frames_minted" in status_json

        pool_json = json.loads(mcp_server.get_species_pool(tier="Common"))
        assert pool_json["species_count"] >= 1
        assert all(s["protocol_tier"] == "Common" for s in pool_json["species"])

    def test_mcp_generate_and_audit(self):
        mcp_server.faucet_gf("0xMCP_Agent", 10.0)
        bal_json = json.loads(mcp_server.get_agent_balance("0xMCP_Agent"))
        assert bal_json["gf_balance"] >= 10.0

        gen_json = json.loads(mcp_server.generate_frame("0xMCP_Agent", "mcp_salt_123"))
        assert gen_json["success"] is True
        frame_id = gen_json["frame_id"]

        inspect_json = json.loads(mcp_server.inspect_frame(frame_id))
        assert inspect_json["record"]["frame_id"] == frame_id

        verify_json = json.loads(mcp_server.verify_frame(frame_id))
        assert verify_json["is_valid"] is True
