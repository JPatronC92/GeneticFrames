"""
GeneticFrames High-Performance REST API Server
Exposes machine-first REST endpoints for autonomous AI agents, bots, and external integrators.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from protocol.db_storage import PersistentEconomyLedger
from protocol.engine import GeneticFramesProtocol
from protocol.species_pool import SPECIES_POOL_V1, RarityTier


# -----------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# -----------------------------------------------------------------------------

class FaucetRequest(BaseModel):
    amount: float = Field(default=10.0, gt=0, description="Amount of GF to deposit")


class GenerateRequest(BaseModel):
    agent_id: str = Field(..., description="ID / address of the requesting agent")
    client_entropy: Optional[str] = Field(default=None, description="Optional client randomness entropy salt")


class CreateListingRequest(BaseModel):
    seller_id: str = Field(..., description="Agent ID of the seller")
    frame_id: int = Field(..., description="ID of the frame to list")
    price_gf: float = Field(..., gt=0, description="Asking price in GF")


class PlaceBidRequest(BaseModel):
    bidder_id: str = Field(..., description="Agent ID of the bidder")
    frame_id: int = Field(..., description="ID of the frame to bid on")
    bid_amount_gf: float = Field(..., gt=0, description="Bid offer in GF")


class ProposeSwapRequest(BaseModel):
    initiator_id: str = Field(..., description="Agent ID proposing the swap")
    offered_frame_id: int = Field(..., description="Frame ID offered by initiator")
    requested_frame_id: int = Field(..., description="Target Frame ID desired")
    delta_gf: float = Field(default=0.0, description="Additional GF sweetener offered by initiator")


class BuyListingRequest(BaseModel):
    buyer_id: str = Field(..., description="Agent ID buying the listing")


class AcceptBidRequest(BaseModel):
    seller_id: str = Field(..., description="Agent ID of the seller accepting the bid")


class AcceptSwapRequest(BaseModel):
    counterparty_id: str = Field(..., description="Agent ID accepting the swap")


# -----------------------------------------------------------------------------
# APPLICATION FACTORY
# -----------------------------------------------------------------------------

def create_app(db_path: str = "geneticframes.db") -> FastAPI:
    app = FastAPI(
        title="GeneticFrames Agent API",
        description="Autonomous Asset Economy Protocol for AI Agents",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize persistent protocol engine
    ledger = PersistentEconomyLedger(db_path=db_path)
    protocol = GeneticFramesProtocol(economy_ledger=ledger)
    app.state.protocol = protocol

    # -------------------------------------------------------------------------
    # STATUS & DISCOVERY ENDPOINTS
    # -------------------------------------------------------------------------

    @app.get("/health", tags=["Status"])
    def health_check():
        return {"status": "ok", "protocol": "GeneticFrames", "version": "0.1.0"}

    @app.get("/protocol/status", tags=["Protocol"])
    def get_protocol_status():
        return app.state.protocol.get_protocol_metrics()

    @app.get("/species/pool", tags=["Species Pool"])
    def get_species_pool(tier: Optional[str] = None):
        catalog = SPECIES_POOL_V1.catalog
        if tier:
            try:
                t_enum = RarityTier(tier.capitalize())
                catalog = [s for s in catalog if s.tier == t_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
        return {
            "version": SPECIES_POOL_V1.VERSION,
            "catalog_sha256": SPECIES_POOL_V1.catalog_sha256,
            "count": len(catalog),
            "species": [s.to_dict() for s in catalog],
        }

    # -------------------------------------------------------------------------
    # AGENT WALLET ENDPOINTS
    # -------------------------------------------------------------------------

    @app.get("/agents/{agent_id}/balance", tags=["Agents"])
    def get_agent_balance(agent_id: str):
        wallet = app.state.protocol.economy.get_or_create_wallet(agent_id)
        return wallet.to_dict()

    @app.post("/agents/{agent_id}/faucet", tags=["Agents"])
    def faucet_agent_gf(agent_id: str, req: FaucetRequest = FaucetRequest()):
        new_balance = app.state.protocol.economy.mint_gf(agent_id, req.amount)
        return {"agent_id": agent_id, "amount_minted": req.amount, "new_balance": round(new_balance, 4)}

    @app.get("/agents/{agent_id}/frames", tags=["Agents"])
    def list_agent_frames(agent_id: str):
        frames = app.state.protocol.economy.get_agent_frames(agent_id)
        return {"agent_id": agent_id, "count": len(frames), "frames": [f.to_dict() for f in frames]}

    @app.get("/agents/{agent_id}/collections/{family}", tags=["Agents"])
    def check_agent_collection(agent_id: str, family: str):
        return app.state.protocol.economy.check_collection_completion(agent_id, family)

    # -------------------------------------------------------------------------
    # GENERATION & VERIFICATION ENDPOINTS
    # -------------------------------------------------------------------------

    @app.post("/protocol/generate", status_code=status.HTTP_201_CREATED, tags=["Protocol"])
    def generate_frame(req: GenerateRequest):
        try:
            record = app.state.protocol.generate(
                agent_id=req.agent_id,
                client_entropy=req.client_entropy,
            )
            return {
                "success": True,
                "frame_id": record.frame_id,
                "generation_id": record.generation_id,
                "organism_id": record.organism_id,
                "common_name": record.common_name,
                "scientific_name": record.scientific_name,
                "tier": record.tier.value,
                "creator_id": record.creator_id,
                "owner_id": record.owner_id,
                "manifest": record.manifest,
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    @app.get("/frames/{frame_id}", tags=["Frames"])
    def get_frame_details(frame_id: int):
        frame = app.state.protocol.inspect_frame(frame_id)
        if not frame:
            raise HTTPException(status_code=404, detail=f"Frame #{frame_id} not found")
        return {
            "record": frame.to_dict(),
            "manifest": frame.manifest,
            "provenance": frame.provenance_history,
        }

    @app.get("/frames/{frame_id}/manifest", tags=["Frames"])
    def get_frame_manifest(frame_id: int):
        frame = app.state.protocol.inspect_frame(frame_id)
        if not frame:
            raise HTTPException(status_code=404, detail=f"Frame #{frame_id} not found")
        return frame.manifest

    @app.get("/frames/{frame_id}/svg", tags=["Frames"])
    def get_frame_svg(frame_id: int):
        frame = app.state.protocol.inspect_frame(frame_id)
        if not frame:
            raise HTTPException(status_code=404, detail=f"Frame #{frame_id} not found")
        return Response(content=frame.svg_code, media_type="image/svg+xml")

    @app.post("/frames/{frame_id}/verify", tags=["Verification"])
    def verify_frame_authenticity(frame_id: int):
        frame = app.state.protocol.inspect_frame(frame_id)
        if not frame:
            raise HTTPException(status_code=404, detail=f"Frame #{frame_id} not found")
        result = app.state.protocol.verify_frame(frame_id)
        return result.to_dict()

    # -------------------------------------------------------------------------
    # MARKETPLACE ENDPOINTS
    # -------------------------------------------------------------------------

    @app.get("/market/orders", tags=["Marketplace"])
    def get_market_orders():
        listings = [l.to_dict() for l in app.state.protocol.economy.listings.values()]
        bids = [b.to_dict() for b in app.state.protocol.economy.bids.values()]
        swaps = [s.to_dict() for s in app.state.protocol.economy.swaps.values()]
        recent_trades = [t.to_dict() for t in app.state.protocol.economy.trade_history[-20:]]
        return {
            "active_listings": [l for l in listings if l["status"] == "active"],
            "active_bids": [b for b in bids if b["status"] == "active"],
            "active_swaps": [s for s in swaps if s["status"] == "active"],
            "recent_trades": recent_trades,
        }

    @app.post("/market/listings", status_code=status.HTTP_201_CREATED, tags=["Marketplace"])
    def create_listing(req: CreateListingRequest):
        try:
            listing = app.state.protocol.economy.create_listing(
                seller_id=req.seller_id,
                frame_id=req.frame_id,
                price_gf=req.price_gf,
            )
            return listing.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.delete("/market/listings/{listing_id}", tags=["Marketplace"])
    def cancel_listing(listing_id: str, seller_id: str):
        try:
            app.state.protocol.economy.cancel_listing(seller_id, listing_id)
            return {"success": True, "listing_id": listing_id, "status": "cancelled"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/market/listings/{listing_id}/buy", tags=["Marketplace"])
    def buy_listing(listing_id: str, req: BuyListingRequest):
        try:
            trade = app.state.protocol.economy.buy_listing(
                buyer_id=req.buyer_id,
                listing_id=listing_id,
            )
            return trade.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/market/bids", status_code=status.HTTP_201_CREATED, tags=["Marketplace"])
    def place_bid(req: PlaceBidRequest):
        try:
            bid = app.state.protocol.economy.place_bid(
                bidder_id=req.bidder_id,
                frame_id=req.frame_id,
                bid_amount_gf=req.bid_amount_gf,
            )
            return bid.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/market/bids/{bid_id}/accept", tags=["Marketplace"])
    def accept_bid(bid_id: str, req: AcceptBidRequest):
        try:
            trade = app.state.protocol.economy.accept_bid(
                seller_id=req.seller_id,
                bid_id=bid_id,
            )
            return trade.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/market/swaps", status_code=status.HTTP_201_CREATED, tags=["Marketplace"])
    def propose_swap(req: ProposeSwapRequest):
        try:
            swap = app.state.protocol.economy.propose_swap(
                initiator_id=req.initiator_id,
                offered_frame_id=req.offered_frame_id,
                requested_frame_id=req.requested_frame_id,
                delta_gf=req.delta_gf,
            )
            return swap.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/market/swaps/{swap_id}/accept", tags=["Marketplace"])
    def accept_swap(swap_id: str, req: AcceptSwapRequest):
        try:
            t1, t2 = app.state.protocol.economy.accept_swap(
                counterparty_id=req.counterparty_id,
                swap_id=swap_id,
            )
            return {"trade_1": t1.to_dict(), "trade_2": t2.to_dict()}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
