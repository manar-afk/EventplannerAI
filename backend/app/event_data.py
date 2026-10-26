"""Template data tables for rule-based planning.

Culturally neutral templates by event type. Ritual-specific items are included
only if explicitly mentioned in the user's preferences.
"""

from typing import Dict, List, Any

# Budget definitions: categories are standardized across items and vendors.
# Weight percentages sum to 100 including contingency.
BUDGET_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "wedding": [
        {"key": "venue", "name": "Event Venue & Reception Hall", "category": "Venue", "cost_basis": "fixed", "weight": 24, "notes": "Main ceremony and celebration venue rental"},
        {"key": "catering", "name": "Event Catering & Beverages", "category": "Catering", "cost_basis": "per_guest", "weight": 34, "notes": "Buffet spread, welcome drinks, and food counters"},
        {"key": "decor", "name": "Stage & Ambient Floral Décor", "category": "Décor", "cost_basis": "fixed", "weight": 14, "notes": "Stage backdrop, lighting, and table arrangements"},
        {"key": "media", "name": "Photography & Videography", "category": "Media", "cost_basis": "fixed", "weight": 10, "notes": "Full day coverage and edited highlights"},
        {"key": "entertainment", "name": "Music & Sound System Setup", "category": "Entertainment", "cost_basis": "fixed", "weight": 5, "notes": "Audio system, DJ, or live performance setup"},
        {"key": "attire", "name": "Event Attire & Personal Styling", "category": "Attire", "cost_basis": "fixed", "weight": 4, "notes": "Ceremonial garments and styling"},
        {"key": "favors", "name": "Guest Favors & Welcome Gifts", "category": "Favors", "cost_basis": "per_guest", "weight": 3, "notes": "Gift hampers and appreciation tokens"},
        {"key": "contingency", "name": "Contingency & Incidentals Reserve", "category": "Contingency", "cost_basis": "fixed", "weight": 6, "notes": "Reserve for unexpected expenses and adjustments"},
    ],
    "birthday": [
        {"key": "venue", "name": "Party Hall / Garden Venue Rental", "category": "Venue", "cost_basis": "fixed", "weight": 22, "notes": "Party hall or reserved gathering area"},
        {"key": "catering", "name": "Party Meal Buffet & Refreshments", "category": "Catering", "cost_basis": "per_guest", "weight": 38, "notes": "Appetizers, main meal spread, and drinks"},
        {"key": "decor", "name": "Themed Balloon & Backdrop Décor", "category": "Décor", "cost_basis": "fixed", "weight": 14, "notes": "Entrance arch, backdrop, and table centerpieces"},
        {"key": "cake", "name": "Designer Cake & Celebration Desserts", "category": "Catering", "cost_basis": "fixed", "weight": 6, "notes": "Customized celebration cake and desserts"},
        {"key": "entertainment", "name": "Party Host, Games & Entertainment", "category": "Entertainment", "cost_basis": "fixed", "weight": 8, "notes": "Interactive games, anchor, and audio setup"},
        {"key": "favors", "name": "Return Gift Hampers", "category": "Favors", "cost_basis": "per_guest", "weight": 5, "notes": "Party favors and takeaway gifts"},
        {"key": "contingency", "name": "Contingency & Incidentals Reserve", "category": "Contingency", "cost_basis": "fixed", "weight": 7, "notes": "Emergency buffer for extra guests or requests"},
    ],
    "community": [
        {"key": "venue", "name": "Community Hall / Grounds Reservation", "category": "Venue", "cost_basis": "fixed", "weight": 22, "notes": "Community space reservation and permits"},
        {"key": "catering", "name": "Community Dining & Refreshments", "category": "Catering", "cost_basis": "per_guest", "weight": 38, "notes": "Shared community dining service and drinking water"},
        {"key": "infrastructure", "name": "Stage, Tent & Technical Infrastructure", "category": "Infrastructure", "cost_basis": "fixed", "weight": 18, "notes": "Covered shamiana, seating, and sound setup"},
        {"key": "decor", "name": "Banners, Lighting & Area Directional Décor", "category": "Décor", "cost_basis": "fixed", "weight": 8, "notes": "Welcome signage, entrance lighting, and banners"},
        {"key": "logistics", "name": "Sanitation, First Aid & Waste Management", "category": "Logistics", "cost_basis": "fixed", "weight": 6, "notes": "Waste bins, cleaning crew, and first-aid station"},
        {"key": "contingency", "name": "Contingency & Reserve Fund", "category": "Contingency", "cost_basis": "fixed", "weight": 8, "notes": "Reserve for weather contingencies or permits"},
    ],
}

# Vendor templates mapped directly to budget item keys
VENDOR_TEMPLATES: Dict[str, List[Dict[str, str]]] = {
    "wedding": [
        {"budget_key": "venue", "service_name": "Venue Reservation & Management", "category": "Venue"},
        {"budget_key": "catering", "service_name": "Catering & Banquet Service Team", "category": "Catering"},
        {"budget_key": "decor", "service_name": "Floral Designers & Stage Stylists", "category": "Décor"},
        {"budget_key": "media", "service_name": "Event Photographers & Cinematographers", "category": "Media"},
        {"budget_key": "entertainment", "service_name": "Audio-Visual & Music Engineers", "category": "Entertainment"},
    ],
    "birthday": [
        {"budget_key": "venue", "service_name": "Party Hall Coordinator", "category": "Venue"},
        {"budget_key": "catering", "service_name": "Party Catering Specialists", "category": "Catering"},
        {"budget_key": "decor", "service_name": "Balloon Artists & Theme Stylists", "category": "Décor"},
        {"budget_key": "entertainment", "service_name": "Event Emcee & Game Coordinator", "category": "Entertainment"},
    ],
    "community": [
        {"budget_key": "venue", "service_name": "Community Ground Coordinator", "category": "Venue"},
        {"budget_key": "catering", "service_name": "Community Dining Operators", "category": "Catering"},
        {"budget_key": "infrastructure", "service_name": "Tent, Audio & Electrical Contractors", "category": "Infrastructure"},
        {"budget_key": "logistics", "service_name": "Local Facilities & Sanitisation Crew", "category": "Logistics"},
    ],
}
