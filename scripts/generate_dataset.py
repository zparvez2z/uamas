#!/usr/bin/env python3
"""Generate a synthetic Kaufland-style product dataset for the demo."""

from __future__ import annotations

import csv
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "products.csv"


CATEGORY_CONFIG = {
    "Electronics": {
        "brands": ["Samsung", "Sony", "LG", "Anker", "Dyson", "JBL", "Philips", "Lenovo"],
        "colors": ["Schwarz", "Silber", "Weiß", "Grau", "Blau"],
        "materials": ["Kunststoff", "Aluminium", "Glas"],
        "sizes": ["compact", "standard", "large"],
        "templates": [
            "{brand} {feature} {noun}",
            "{brand} {adjective} {noun} {feature}",
            "{brand} {noun} with {feature}",
            "{adjective} {noun} for home entertainment",
        ],
        "descriptions": [
            "Smart device with reliable performance, modern connectivity, and everyday convenience.",
            "Designed for fast setup, clear output, and long-lasting use in the home or office.",
            "High-quality electronics product with practical features and a clean user experience.",
        ],
        "nouns": ["TV", "Bluetooth Speaker", "Vacuum", "Monitor", "Wireless Headphones", "Tablet", "Air Fryer", "Smart Plug"],
        "features": ["4K", "Bluetooth", "wireless", "smart", "portable", "energy-saving", "mini"],
        "adjectives": ["compact", "premium", "durable", "modern", "sleek", "intelligent"],
    },
    "Home": {
        "brands": ["IKEA", "Vileda", "Philips", "Leifheit", "Home&More", "Tchibo"],
        "colors": ["Weiß", "Beige", "Grau", "Braun", "Schwarz"],
        "materials": ["Holz", "Metall", "Kunststoff", "Baumwolle"],
        "sizes": ["small", "medium", "large"],
        "templates": [
            "{brand} {noun} {variant}",
            "{adjective} {noun} for everyday home use",
            "{brand} {noun} with practical {feature}",
            "{noun} for kitchen and living room organization",
        ],
        "descriptions": [
            "Practical home item for organizing, cleaning, or furnishing daily spaces.",
            "Reliable household product designed for convenience, durability, and simple use.",
            "Useful home accessory with a straightforward design and versatile application.",
        ],
        "nouns": ["Bookcase", "Storage Box", "Floor Lamp", "Dinnerware Set", "Laundry Basket", "Kitchen Scale", "Coffee Mug Set", "Shelf"],
        "features": ["stackable", "foldable", "space-saving", "adjustable", "easy-clean", "multi-purpose"],
        "adjectives": ["stylish", "functional", "compact", "minimal", "durable", "versatile"],
    },
    "Clothing": {
        "brands": ["Adidas", "Puma", "Nike", "H&M", "Zara", "Tom Tailor", "Only", "Levi's"],
        "colors": ["Schwarz", "Weiß", "Blau", "Rot", "Grün", "Grau"],
        "materials": ["Baumwolle", "Polyester", "Wolle", "Denim"],
        "sizes": ["S", "M", "L", "XL"],
        "templates": [
            "{brand} {noun} {variant}",
            "{adjective} {noun} for everyday wear",
            "{brand} {noun} with {feature} finish",
            "{noun} in classic {color} style",
        ],
        "descriptions": [
            "Comfortable apparel item made for daily wear, layering, and casual styling.",
            "Soft, wearable clothing with a simple fit and versatile use across seasons.",
            "Fashion basic with a modern look and practical comfort for everyday outfits.",
        ],
        "nouns": ["T-Shirt", "Hoodie", "Jacket", "Jeans", "Sweater", "Dress", "Shirt", "Leggings"],
        "features": ["slim fit", "regular fit", "breathable", "stretch", "washed", "oversized"],
        "adjectives": ["casual", "classic", "cozy", "modern", "soft", "elegant"],
    },
    "Shoes": {
        "brands": ["Nike", "Adidas", "Puma", "Skechers", "New Balance", "Reebok", "Salomon"],
        "colors": ["Schwarz", "Weiß", "Grau", "Blau", "Rot"],
        "materials": ["Mesh", "Leder", "Textil", "Synthetik"],
        "sizes": ["40", "41", "42", "43", "44"],
        "templates": [
            "{brand} {noun} {variant}",
            "{adjective} {noun} for daily comfort",
            "{brand} {noun} with {feature} support",
            "{noun} for running and training",
        ],
        "descriptions": [
            "Comfortable footwear built for walking, training, or everyday wear.",
            "Supportive shoe with a lightweight feel and durable construction.",
            "Practical athletic shoe with a clean design and reliable grip.",
        ],
        "nouns": ["Sneakers", "Running Shoes", "Trail Shoes", "Walking Shoes", "Training Shoes", "Slip-Ons"],
        "features": ["cushioned", "lightweight", "breathable", "water-repellent", "grippy", "stabilizing"],
        "adjectives": ["sporty", "comfortable", "durable", "lightweight", "flexible", "premium"],
    },
    "Beauty": {
        "brands": ["L'Oréal", "Nivea", "Balea", "Garnier", "Clinique", "CeraVe", "Weleda"],
        "colors": ["Weiß", "Rosa", "Gold", "Transparent"],
        "materials": ["Kunststoff", "Glas", "Papier"],
        "sizes": ["50 ml", "100 ml", "200 ml"],
        "templates": [
            "{brand} {noun} {variant}",
            "{adjective} {noun} for daily skincare",
            "{brand} {noun} with {feature} formula",
            "{noun} for radiant skin and comfort",
        ],
        "descriptions": [
            "Cosmetic and personal care item for grooming, hydration, or daily routine use.",
            "Gentle beauty product designed for consistent results and easy application.",
            "Everyday personal care formula with a clean, modern presentation.",
        ],
        "nouns": ["Face Cream", "Shampoo", "Body Lotion", "Serum", "Lip Balm", "Shower Gel", "Hand Cream", "Mascara"],
        "features": ["hydrating", "fragrance-free", "nourishing", "repairing", "gentle", "long-lasting"],
        "adjectives": ["smooth", "gentle", "rich", "lightweight", "refreshing", "calming"],
    },
    "Sports": {
        "brands": ["Nike", "Adidas", "Decathlon", "Puma", "Yonex", "Babolat", "Garmin"],
        "colors": ["Schwarz", "Blau", "Rot", "Grün", "Gelb"],
        "materials": ["Carbon", "Aluminium", "Polyester", "Mesh"],
        "sizes": ["S", "M", "L", "XL", "One Size"],
        "templates": [
            "{brand} {noun} {variant}",
            "{adjective} {noun} for training and competition",
            "{brand} {noun} with {feature} design",
            "{noun} for active performance and fitness",
        ],
        "descriptions": [
            "Athletic gear designed for workouts, training, and competitive use.",
            "Sport product with performance-focused materials and a lightweight feel.",
            "Reliable equipment for active movement, exercise, and outdoor sessions.",
        ],
        "nouns": ["Running Racket", "Yoga Mat", "Water Bottle", "Fitness Tracker", "Dumbbell Set", "Cycling Jersey", "Football", "Resistance Band"],
        "features": ["lightweight", "high-grip", "breathable", "shock-absorbing", "performance", "portable"],
        "adjectives": ["dynamic", "athletic", "durable", "lightweight", "focused", "pro-grade"],
    },
}

BRIEF_VARIANTS = [
    "for everyday use",
    "with modern styling",
    "for home and travel",
    "in a practical design",
    "with reliable performance",
]

AMBIGUOUS_OVERRIDES = [
    ("Electronics", "Smart Rice Cooker", "smart appliance for kitchen use"),
    ("Home", "Cordless Hand Vacuum", "compact cleaner for quick household tasks"),
    ("Sports", "Fitness Tracker Watch", "wearable device for training metrics"),
    ("Beauty", "Spa Gift Set", "self-care set with mixed personal care items"),
    ("Clothing", "Thermal Hoodie Set", "comfortable layer for cold-weather wear"),
    ("Shoes", "Trail Sneakers", "hybrid shoe for walking, running, and outdoor use"),
]


def make_ean(index: int) -> str:
    base = 4000000000000 + index
    return f"{base:013d}"


def build_row(index: int, category: str) -> dict[str, str]:
    config = CATEGORY_CONFIG[category]
    brand = random.choice(config["brands"])
    color = random.choice(config["colors"])
    material = random.choice(config["materials"])
    size = random.choice(config["sizes"])
    noun = random.choice(config["nouns"])
    feature = random.choice(config["features"])
    adjective = random.choice(config["adjectives"])
    variant = random.choice(BRIEF_VARIANTS)
    title = random.choice(config["templates"]).format(
        brand=brand,
        noun=noun,
        variant=variant,
        feature=feature,
        adjective=adjective,
        color=color,
    )
    description = random.choice(config["descriptions"])
    if index % 11 == 0:
        override_category, override_title, override_description = random.choice(AMBIGUOUS_OVERRIDES)
        if override_category == category:
            title = override_title
            description = override_description
    if index % 7 == 0:
        description = f"{description} Available in {color.lower()} with {material.lower()} details and {feature} features."

    return {
        "ean": make_ean(index),
        "locale": "de-DE",
        "title": title,
        "description": description,
        "category": category,
        "colour": color,
        "manufacturer": brand,
        "picture": f"https://example.com/products/{index:04d}.jpg",
        "material": material,
        "size": size,
    }


def generate_rows() -> list[dict[str, str]]:
    random.seed(42)
    rows: list[dict[str, str]] = []
    category_counts = {
        "Electronics": 36,
        "Home": 30,
        "Clothing": 30,
        "Shoes": 30,
        "Beauty": 24,
        "Sports": 30,
    }

    index = 1
    for category, count in category_counts.items():
        for _ in range(count):
            rows.append(build_row(index, category))
            index += 1

    return rows


def main() -> None:
    rows = generate_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ean",
        "locale",
        "title",
        "description",
        "category",
        "colour",
        "manufacturer",
        "picture",
        "material",
        "size",
    ]

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()