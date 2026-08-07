def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "full_name": "Admin User", "password": "strong-password"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "strong-password"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_brand(client, headers, slug="samsung"):
    response = client.post("/api/v1/brands", json={"name": "Samsung", "slug": slug}, headers=headers)
    assert response.status_code == 201
    return response.json()


def create_category(client, headers, slug="smartwatches", parent_id=None):
    response = client.post(
        "/api/v1/categories",
        json={"name": "Smartwatches", "slug": slug, "parent_id": parent_id},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_store(client, headers, slug="amazon-brasil"):
    response = client.post(
        "/api/v1/stores",
        json={"name": "Amazon Brasil", "slug": slug, "base_url": "https://www.amazon.com.br"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_product(client, headers, brand_id=None, category_id=None, slug="galaxy-watch-ultra"):
    response = client.post(
        "/api/v1/products",
        json={
            "name": "Galaxy Watch Ultra",
            "slug": slug,
            "brand_id": brand_id,
            "category_id": category_id,
            "model": "Ultra",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_offer(client, headers, product_id, store_id, seller_id=None, external_id="offer-1"):
    response = client.post(
        "/api/v1/offers",
        json={
            "product_id": product_id,
            "store_id": store_id,
            "seller_id": seller_id,
            "external_id": external_id,
            "url": "https://example.com/offer-1",
            "title": "Galaxy Watch Ultra Samsung Oficial",
            "current_price": "2199.00",
            "currency": "BRL",
            "is_free_shipping": True,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_brand_creation(client):
    headers = auth_headers(client)
    brand = create_brand(client, headers)

    assert brand["name"] == "Samsung"
    assert client.get(f"/api/v1/brands/{brand['id']}").status_code == 200


def test_unique_brand_slug(client):
    headers = auth_headers(client)
    create_brand(client, headers)

    response = client.post("/api/v1/brands", json={"name": "Samsung 2", "slug": "samsung"}, headers=headers)

    assert response.status_code == 409


def test_category_creation_and_parent_category(client):
    headers = auth_headers(client)
    parent = create_category(client, headers, slug="eletronicos")
    child = create_category(client, headers, slug="smartwatches", parent_id=parent["id"])

    assert child["parent_id"] == parent["id"]


def test_store_creation(client):
    headers = auth_headers(client)
    store = create_store(client, headers)

    assert store["slug"] == "amazon-brasil"


def test_seller_creation(client):
    headers = auth_headers(client)
    store = create_store(client, headers)

    response = client.post(
        "/api/v1/sellers",
        json={"store_id": store["id"], "name": "Samsung Oficial", "external_id": "seller-1", "is_official": True},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["store_id"] == store["id"]


def test_product_creation_does_not_store_price(client):
    headers = auth_headers(client)
    brand = create_brand(client, headers)
    category = create_category(client, headers)

    product = create_product(client, headers, brand_id=brand["id"], category_id=category["id"])

    assert "current_price" not in product
    assert product["brand_id"] == brand["id"]


def test_offer_creation_and_duplicate_external_id_by_store(client):
    headers = auth_headers(client)
    store = create_store(client, headers)
    product = create_product(client, headers)
    offer = create_offer(client, headers, product["id"], store["id"])

    duplicate = client.post(
        "/api/v1/offers",
        json={
            "product_id": product["id"],
            "store_id": store["id"],
            "external_id": offer["external_id"],
            "url": "https://example.com/duplicate",
            "title": "Duplicate",
            "current_price": "2099.00",
        },
        headers=headers,
    )

    assert offer["store_id"] == store["id"]
    assert duplicate.status_code == 409


def test_negative_offer_price_is_rejected(client):
    headers = auth_headers(client)
    store = create_store(client, headers)
    product = create_product(client, headers)

    response = client.post(
        "/api/v1/offers",
        json={
            "product_id": product["id"],
            "store_id": store["id"],
            "external_id": "negative-offer",
            "url": "https://example.com/negative",
            "title": "Negative",
            "current_price": "-1.00",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_snapshot_creation_and_price_history(client):
    headers = auth_headers(client)
    store = create_store(client, headers)
    product = create_product(client, headers)
    offer = create_offer(client, headers, product["id"], store["id"])

    first = client.post(
        f"/api/v1/offers/{offer['id']}/price-history",
        json={"price": "2199.00", "captured_at": "2026-08-06T10:00:00Z"},
        headers=headers,
    )
    second = client.post(
        f"/api/v1/offers/{offer['id']}/price-history",
        json={"price": "2099.00", "captured_at": "2026-08-06T11:00:00Z"},
        headers=headers,
    )
    history = client.get(f"/api/v1/offers/{offer['id']}/price-history")

    assert first.status_code == 201
    assert second.status_code == 201
    assert history.status_code == 200
    assert [item["price"] for item in history.json()] == ["2199.00", "2099.00"]


def test_pagination(client):
    headers = auth_headers(client)
    create_brand(client, headers, slug="brand-1")
    create_brand(client, headers, slug="brand-2")
    create_brand(client, headers, slug="brand-3")

    response = client.get("/api/v1/brands?limit=2&offset=1")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_offer_with_missing_product_returns_404(client):
    headers = auth_headers(client)
    store = create_store(client, headers)

    response = client.post(
        "/api/v1/offers",
        json={
            "product_id": 999,
            "store_id": store["id"],
            "external_id": "missing-product",
            "url": "https://example.com/missing-product",
            "title": "Missing product",
            "current_price": "2199.00",
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_create_offer_with_missing_store_returns_404(client):
    headers = auth_headers(client)
    product = create_product(client, headers)

    response = client.post(
        "/api/v1/offers",
        json={
            "product_id": product["id"],
            "store_id": 999,
            "external_id": "missing-store",
            "url": "https://example.com/missing-store",
            "title": "Missing store",
            "current_price": "2199.00",
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Store not found"


def test_create_offer_with_missing_seller_returns_404(client):
    headers = auth_headers(client)
    store = create_store(client, headers)
    product = create_product(client, headers)

    response = client.post(
        "/api/v1/offers",
        json={
            "product_id": product["id"],
            "store_id": store["id"],
            "seller_id": 999,
            "external_id": "missing-seller",
            "url": "https://example.com/missing-seller",
            "title": "Missing seller",
            "current_price": "2199.00",
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Seller not found"


def test_create_offer_with_seller_from_another_store_returns_409(client):
    headers = auth_headers(client)
    store = create_store(client, headers)
    other_store = create_store(client, headers, slug="mercado-livre")
    product = create_product(client, headers)
    seller_response = client.post(
        "/api/v1/sellers",
        json={"store_id": other_store["id"], "name": "Samsung Oficial", "external_id": "seller-other"},
        headers=headers,
    )
    assert seller_response.status_code == 201

    response = client.post(
        "/api/v1/offers",
        json={
            "product_id": product["id"],
            "store_id": store["id"],
            "seller_id": seller_response.json()["id"],
            "external_id": "wrong-store-seller",
            "url": "https://example.com/wrong-store-seller",
            "title": "Wrong store seller",
            "current_price": "2199.00",
        },
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Seller does not belong to the offer store"


def test_update_offer_with_incompatible_seller_store_returns_409(client):
    headers = auth_headers(client)
    store = create_store(client, headers)
    other_store = create_store(client, headers, slug="mercado-livre")
    product = create_product(client, headers)
    offer = create_offer(client, headers, product["id"], store["id"])
    seller_response = client.post(
        "/api/v1/sellers",
        json={"store_id": other_store["id"], "name": "Samsung Oficial", "external_id": "seller-other"},
        headers=headers,
    )
    assert seller_response.status_code == 201

    response = client.patch(
        f"/api/v1/offers/{offer['id']}",
        json={"seller_id": seller_response.json()["id"]},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Seller does not belong to the offer store"
