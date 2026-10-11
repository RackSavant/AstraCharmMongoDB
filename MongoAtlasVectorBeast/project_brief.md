# Project Brief: SF Coastal Table & Michelin AI Lab (`sf-michelin-culinary-concierge`)

## 1. Executive Summary
SF Coastal Table is an agentic culinary concierge application that brings multi-Michelin-star Northern California dining, hyper-local ingredient sourcing, and custom signature recipe creation to users. It combines Bay Area gastronomy (Dungeness Crab, Mendocino Uni, Tartine Sourdough, Central Valley Citrus, Sonoma Wine) with interactive recipe generation, wine pairing, image visualization, and A2UI interfaces.

## 2. Core Capabilities & Architecture
- Conversation Memory (Vertex AI Memory Bank): Remembers user dietary preferences, seafood allergies, favorite SF restaurants, and wine tastes across sessions.
- Structured Database (Firestore): Collection `dishes` storing signature recipes, wine pairings, and ingredient breakdowns.
- Cloud Storage (GCS Bucket): Publicly serves high-resolution generated food photography.
- RAG Engine: Grounded knowledge retrieval over Northern California seasonal produce guides and Michelin technique manuals.
- Image Generation (gemini-3.1-flash-lite-image): Generates high-end culinary plating photos saved to GCS and displayed in A2UI cards.
- Code Execution Sandbox: Calculates baker's percentages, sourdough hydration, ingredient scaling, and nutritional breakdowns in Python.
- A2UI Interfaces: Renders recipe cards, sommelier pairing tables, and ingredient lists.
