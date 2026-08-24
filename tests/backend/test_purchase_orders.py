"""
Tests for purchase order API endpoints (used by the Restocking feature).
"""
from datetime import datetime

import pytest


class TestPurchaseOrdersEndpoints:
    """Test suite for purchase order endpoints."""

    def test_get_purchase_orders_returns_list(self, client):
        """Test that listing purchase orders returns 200 and a list."""
        response = client.get("/api/purchase-orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_purchase_order_from_demand_item(self, client):
        """Test creating a purchase order from a demand-forecast-driven restock item."""
        payload = {
            "item_sku": "FLT-405",
            "item_name": "Oil Filter Cartridge",
            "supplier_name": "Filtration Dynamics",
            "quantity": 450,
            "unit_cost": 4.75,
            "lead_time_days": 10,
            "notes": "Restocking order generated from demand forecast"
        }
        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0
        assert data["status"] == "Submitted"
        assert "created_date" in data
        assert "expected_delivery_date" in data
        assert data["item_sku"] == "FLT-405"
        assert data["item_name"] == "Oil Filter Cartridge"
        assert data["quantity"] == 450

        created_date = datetime.strptime(data["created_date"], "%Y-%m-%d")
        expected_delivery_date = datetime.strptime(data["expected_delivery_date"], "%Y-%m-%d")
        assert (expected_delivery_date - created_date).days == 10

    def test_create_purchase_order_appears_in_list(self, client):
        """Test that a newly created purchase order shows up in the list endpoint."""
        before = client.get("/api/purchase-orders").json()
        before_count = len(before)

        payload = {
            "item_sku": "GSK-203",
            "item_name": "High-Temperature Gasket",
            "supplier_name": "Thermal Seal Industries",
            "quantity": 400,
            "unit_cost": 3.25,
            "lead_time_days": 5
        }
        create_response = client.post("/api/purchase-orders", json=payload)
        assert create_response.status_code == 201
        new_id = create_response.json()["id"]

        after = client.get("/api/purchase-orders").json()
        assert len(after) == before_count + 1
        assert any(po["id"] == new_id for po in after)

    def test_create_purchase_order_missing_required_field_returns_422(self, client):
        """Test that omitting a required field (supplier_name) returns a validation error."""
        payload = {
            "item_sku": "WDG-001",
            "item_name": "Industrial Widget Type A",
            "quantity": 300,
            "unit_cost": 45.00,
            "lead_time_days": 12
        }
        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 422

    def test_create_purchase_order_with_backlog_item_id_still_works(self, client):
        """Test that the legacy backlog-item-based payload shape is still accepted."""
        payload = {
            "backlog_item_id": "2",
            "supplier_name": "Volt Motors Inc",
            "quantity": 10,
            "unit_cost": 220.00,
            "lead_time_days": 21
        }
        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["backlog_item_id"] == "2"
        assert data["item_sku"] is None
        assert data["item_name"] is None
