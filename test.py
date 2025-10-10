import requests
from typing import Optional

def get_selected_product_image(query: str) -> Optional[str]:
    """
    Sucht bei OpenFoodFacts nach einem Produkt und liefert nur das
    offiziell 'selected' Front-Image (studio-like), falls vorhanden.
    """
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 1,  # nur bestes Ergebnis
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    products = data.get("products", [])
    if not products:
        return None

    product = products[0]
    selected = product.get("selected_images", {})
    front = selected.get("front", {})
    display = front.get("display", {})

    # Sprachpriorität: englisch, deutsch, französisch
    for lang in ["en", "de", "fr"]:
        if url := display.get(lang):
            return url

    return None


if __name__ == "__main__":
    test_queries = [
        # Klassiker (sollten gute Bilder liefern)
        "Nutella",
        "Coca Cola",
        "Pepsi",
        "Oreo",
        "Haribo Goldbären",
        "Milka Schokolade",
        "Barilla Pasta",
        "Pringles Paprika",
        "Red Bull",
        "Heinz Ketchup",

        # Supermarkt-Eigenmarken (mal ja, mal nein)
        "Rewe Bio Haferdrink",
        "Edeka Gut & Günstig Milch",
        "Aldi River Cola",
        "Lidl Freeway Orange Limo",

        # Gesunde Ecke
        "Alpro Sojadrink",
        "Oatly Hafermilch",
        "Müllermilch Banane",
        "Activia Joghurt",

        # Snacks
        "Twix",
        "Snickers",
        "Kinder Bueno",
        "Hanuta",
        "Chipsfrisch Ungarisch",

        # Getränke
        "Sprite",
        "Fanta Orange",
        "Schweppes Tonic Water",
        "Vittel Mineralwasser",
        "Volvic Naturelle",

        # Deutsche Spezialitäten
        "Maggi Würze",
        "Knorr Fix Lasagne",
        "Ritter Sport Alpenmilch",
        "Dr. Oetker Ristorante Pizza",

        # Nischen / potenziell bodenlos
        "No Name Cracker",
        "Unbekannte Bio Dinkelkekse",
        "Sehr spezieller Asia Snack",
    ]

    for query in test_queries:
        img = get_selected_product_image(query)
        print(f"Query: {query}")
        if img:
            print(f"  ✅ Bild: {img}")
        else:
            print(f"  ❌ Kein Bild gefunden")
        print("-" * 60)
