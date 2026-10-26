"""Deterministic rule-based planning engine for EventPilot AI.

Used as a reliable fallback when Gemini is unavailable, unconfigured,
or returns an unparseable response. Clearly labeled as 'rule-based-fallback'.
References user inputs (location, style, theme, requirements) to ensure
tailored, high-value plans without AI hallucinations.
"""

from typing import List, Dict, Any
import uuid
from .budget_engine import BudgetItem, calculate_budget
from .timeline_engine import generate_timeline
from .schemas import (
    EventCreateRequest,
    FullPlanResponse,
    VendorItem,
    GroupedIdeas,
    IdeaCategory,
)


def _allocate_integer_budget(
    total_budget: int,
    guest_count: int,
    item_definitions: List[Dict[str, Any]]
) -> List[BudgetItem]:
    """Distribute budget using percentage weights and convert to integer rupees.

    Calculates per-guest vs fixed cost basis accurately.
    """
    items: List[BudgetItem] = []
    # Calculate initial amounts from basis weights
    total_weight = sum(defn["weight"] for defn in item_definitions)

    for idx, defn in enumerate(item_definitions):
        raw_amount = int(round((defn["weight"] / total_weight) * total_budget))
        # Ensure at least ₹500 per item for realism
        amount = max(500, raw_amount)

        cost_basis = defn["cost_basis"]
        notes = defn.get("notes", "")

        items.append(
            BudgetItem(
                id=f"bi-{idx + 1}-{uuid.uuid4().hex[:6]}",
                name=defn["name"],
                category=defn["category"],
                cost_basis=cost_basis,
                estimated_amount=amount,
                actual_amount=None,
                notes=notes
            )
        )

    return items


def generate_rule_based_plan(
    event: EventCreateRequest,
    fallback_reason: str = "Rule-based planner executed"
) -> FullPlanResponse:
    """Generate a comprehensive, culturally rich Indian event plan from rule tables."""
    etype = event.event_type.lower()
    loc = event.location
    theme_label = event.theme if event.theme else "Festive Indian"
    style_label = event.style if event.style else "Traditional Elegance"
    reqs_label = f"Special considerations: {event.special_requirements}" if event.special_requirements else "Standard arrangements"

    # 1. Budget item definitions by event type
    if etype == "wedding":
        budget_defs = [
            {"name": "Traditional Wedding & Banquet Venue", "category": "Venue", "cost_basis": "fixed", "weight": 25, "notes": f"Mandap & reception hall in {loc}"},
            {"name": "Multi-course Catering & Live Stalls", "category": "Catering", "cost_basis": "per_guest", "weight": 35, "notes": f"Includes welcome drinks, chaat counters, and main buffet for {event.guest_count} guests"},
            {"name": "Floral Mandap & Stage Décor", "category": "Décor", "cost_basis": "fixed", "weight": 14, "notes": f"Themed with {theme_label} aesthetic"},
            {"name": "Candid Photography & Cinematic Film", "category": "Photography", "cost_basis": "fixed", "weight": 10, "notes": "Pre-wedding, Muhurat and reception coverage"},
            {"name": "Bridal & Groom Attire / Hair & Makeup", "category": "Attire & Beauty", "cost_basis": "fixed", "weight": 6, "notes": "Ceremonial lehenga/sherwani styling"},
            {"name": "DJ, Dhol Players & Sound Setup", "category": "Entertainment", "cost_basis": "fixed", "weight": 4, "notes": "Sangeet & baraat musical coordination"},
            {"name": "Traditional Mithai & Return Favors", "category": "Gifts & Favors", "cost_basis": "per_guest", "weight": 4, "notes": f"Custom sweets and token boxes for {event.guest_count} guests"},
            {"name": "Guest Shuttles & Pandit Ji Samagri", "category": "Logistics & Rituals", "cost_basis": "fixed", "weight": 2, "notes": "Local conveyance & ceremonial supplies"},
        ]
        vendor_defs = [
            {"service_name": "Banquets & Lawn Coordinator", "category": "Venue", "ratio": 0.25},
            {"service_name": "Royal Indian Caterers", "category": "Catering", "ratio": 0.35},
            {"service_name": "Floral Designers & Stage Artists", "category": "Décor", "ratio": 0.14},
            {"service_name": "Wedding Photographers & Videographers", "category": "Media", "ratio": 0.10},
            {"service_name": "Professional DJ & Live Dhol Troupe", "category": "Entertainment", "ratio": 0.04},
            {"service_name": "Bridal Mehndi & Makeup Studio", "category": "Attire & Beauty", "ratio": 0.06},
            {"service_name": "Local Fleet & Shuttle Operators", "category": "Logistics", "ratio": 0.02},
        ]
        decor_ideas = [
            IdeaCategory(title=f"Marigold & Brass Elegance for {loc}", description=f"Incorporate fresh marigolds, brass urlis with floating diyas, and fragrant mogra strings reflecting {style_label}.", practical_tip="Source flowers early morning from local wholesale mandis to save up to 40%."),
            IdeaCategory(title=f"Themed Photo Corner ({theme_label})", description=f"A photobooth installation featuring vintage jharokhas, cane furniture, and personalized couple signage customized for {loc}.", practical_tip="Use fairy lights and warm LEDs for flattering mobile phone photography."),
        ]
        food_ideas = [
            IdeaCategory(title=f"Regional Specialities in {loc}", description=f"Curate interactive live counters: local street chaat, wood-fired tandoor, and traditional mithai stations honoring {theme_label}.", practical_tip="Plan 3 live counters + 2 welcome drinks to keep guests engaged during arrival."),
            IdeaCategory(title="Dietary Accommodating Menus", description=f"Distinct Jain and vegetarian counters with clear signage. Accommodating: {reqs_label}.", practical_tip="Label counters clearly with allergen and dietary indicators."),
        ]
        activity_ideas = [
            IdeaCategory(title="Interactive Sangeet Flashmob & Games", description="Curated playlist spanning retro Bollywood to trending dance tracks, paired with playful trivia about the couple.", practical_tip="Appoint one family anchor from each side to keep energy levels high."),
            IdeaCategory(title="Live Henna / Mehndi Corner", description="Skilled mehendi artists providing quick Arabic and traditional patterns for guests during high tea.", practical_tip="Keep paper cones and clove vapor oil handy for deeper color."),
        ]
        theme_ideas = [
            IdeaCategory(title=f"Cultural Fusion: {style_label}", description=f"Harmonious blend of ceremonial solemnity and vibrant celebration suited for {loc}.", practical_tip="Use matching fabric color palettes across napkins, runners, and stage drapes."),
        ]
        logistics_ideas = [
            IdeaCategory(title=f"Guest Welcome & Transit in {loc}", description=f"Dedicated WhatsApp helpline and welcome desk at primary transit points in {loc}.", practical_tip="Pre-book tempo travellers or pooled cabs for family airport/station pickups."),
            IdeaCategory(title="Ritual Coordination Desk", description=f"Centralized station for puja samagri, havan wood, garland chill boxes, and dakshina envelopes.", practical_tip="Assign a trusted cousin to manage the ritual items checklist."),
        ]

    elif etype == "birthday":
        budget_defs = [
            {"name": "Party Hall / Garden Venue Rental", "category": "Venue", "cost_basis": "fixed", "weight": 22, "notes": f"Space in {loc}"},
            {"name": "Party Buffet & Finger Foods", "category": "Catering", "cost_basis": "per_guest", "weight": 38, "notes": f"Appetizers, main meal, and beverages for {event.guest_count} guests"},
            {"name": "Themed Balloon Arch & Backdrop Décor", "category": "Décor", "cost_basis": "fixed", "weight": 14, "notes": f"Tailored to {theme_label}"},
            {"name": "Customized Designer Cake & Desserts", "category": "Bakery", "cost_basis": "fixed", "weight": 8, "notes": f"Tiered cake adhering to {style_label}"},
            {"name": "Game Host / Emcee & Magic/Activity Show", "category": "Entertainment", "cost_basis": "fixed", "weight": 10, "notes": "Engaging activities and music setup"},
            {"name": "Return Gift Hampers", "category": "Favors", "cost_basis": "per_guest", "weight": 6, "notes": f"Customized gift bags for {event.guest_count} guests"},
            {"name": "Event Photography & Memory Reel", "category": "Media", "cost_basis": "fixed", "weight": 2, "notes": "Cake cutting and guest portraits"},
        ]
        vendor_defs = [
            {"service_name": "Birthday Party Venue Host", "category": "Venue", "ratio": 0.22},
            {"service_name": "Party Caterers & Snack Master", "category": "Catering", "ratio": 0.38},
            {"service_name": "Balloon & Stage Stylist", "category": "Décor", "ratio": 0.14},
            {"service_name": "Artisan Cake Baker", "category": "Bakery", "ratio": 0.08},
            {"service_name": "Kids Emcee & Magician / DJ", "category": "Entertainment", "ratio": 0.10},
            {"service_name": "Event Candid Photographer", "category": "Media", "ratio": 0.02},
        ]
        decor_ideas = [
            IdeaCategory(title=f"Balloon Extravaganza: {theme_label}", description=f"Pastel or chrome balloon garland with neon signage and cardboard cutouts reflecting {style_label} in {loc}.", practical_tip="Use balloon weights to keep outdoor installations stable against wind."),
        ]
        food_ideas = [
            IdeaCategory(title="Kid-Friendly & Crowd-Pleasing Bites", description=f"Slider burgers, mini pizzas, pasta bowls, fruit skewers, and Indian chaat. Notes: {reqs_label}.", practical_tip="Serve finger food on bite-sized eco-friendly bamboo plates for quick clean-up."),
        ]
        activity_ideas = [
            IdeaCategory(title="Interactive Games & Dance Freeze", description="Musical statues, balloon scavenger hunt, and DIY craft counter (pottery or face painting).", practical_tip="Prepare small prize chocolates so every child wins something."),
        ]
        theme_ideas = [
            IdeaCategory(title=f"Visual Identity: {theme_label}", description=f"Consistent aesthetic matching {style_label} with customized photobooth props.", practical_tip="Match cake frosting palette with the main entrance arch."),
        ]
        logistics_ideas = [
            IdeaCategory(title=f"Venue & Parking Setup in {loc}", description="Ensuring easy stroller access, baby-friendly corners, and clear drop-off points.", practical_tip="Confirm power sockets availability for the DJ amplifier and chocolate fountain."),
        ]

    else:  # community event
        budget_defs = [
            {"name": "Community Ground / Hall Booking & Municipal Clearances", "category": "Infrastructure", "cost_basis": "fixed", "weight": 20, "notes": f"Venue reservation in {loc}"},
            {"name": "Community Feast / Prasad / Refreshments", "category": "Catering", "cost_basis": "per_guest", "weight": 40, "notes": f"Wholesome dining for {event.guest_count} community members"},
            {"name": "Stage, Tent (Shamiana) & Sound/Mic Setup", "category": "Stage & Tech", "cost_basis": "fixed", "weight": 20, "notes": "Podium, lights, and PA audio system"},
            {"name": "Banners, Welcome Gate & Area Lighting", "category": "Décor & Signage", "cost_basis": "fixed", "weight": 10, "notes": f"Signboards supporting {theme_label}"},
            {"name": "Cultural Performances & Guest Honoraria", "category": "Performances", "cost_basis": "fixed", "weight": 5, "notes": "Folk artists, school bands, or guest speakers"},
            {"name": "Sanitation, First Aid & Waste Segregation", "category": "Safety & Logistics", "cost_basis": "fixed", "weight": 5, "notes": f"Cleanliness and safety setup for {event.guest_count} attendees. Note: {reqs_label}"},
        ]
        vendor_defs = [
            {"service_name": "Community Ground / Shamiana Tent House", "category": "Infrastructure", "ratio": 0.20},
            {"service_name": "Large-Scale Community Caterers", "category": "Catering", "ratio": 0.40},
            {"service_name": "Sound & Lighting Engineers", "category": "Stage & Tech", "ratio": 0.20},
            {"service_name": "Print & Signage Supplier", "category": "Décor & Signage", "ratio": 0.10},
            {"service_name": "Local Security & Housekeeping Agency", "category": "Safety & Logistics", "ratio": 0.05},
        ]
        decor_ideas = [
            IdeaCategory(title=f"Eco-friendly Banners & Fabric Hangings", description=f"Cloth banners, marigold garlands, and jute accents representing {style_label} in {loc}.", practical_tip="Avoid single-use plastics; opt for compostable flags and recycled paper signage."),
        ]
        food_ideas = [
            IdeaCategory(title="Hygienic Community Dining & Prasad", description=f"Traditional satvik or multi-course regional spread distributed efficiently. {reqs_label}", practical_tip="Set up 2 parallel queue lanes to manage high footfall without congestion."),
        ]
        activity_ideas = [
            IdeaCategory(title="Cultural Performances & Community Felicitation", description="Folk dance, patriotic songs, elder appreciation, and youth sports/talent showcase.", practical_tip="Keep each stage item under 8 minutes to maintain schedule adherence."),
        ]
        theme_ideas = [
            IdeaCategory(title=f"Unity & Heritage ({theme_label})", description=f"Reflecting the collective cultural spirit of {loc} and bringing neighbors together.", practical_tip="Have community elders inaugurate with a traditional lamp lighting."),
        ]
        logistics_ideas = [
            IdeaCategory(title="Crowd Safety, Parking & Drinking Water Stations", description=f"Designated parking marshals, 20L water dispensers, and accessible medical first-aid kit.", practical_tip="Assign volunteer squad leaders with fluorescent jackets for quick recognition."),
        ]

    # Calculate integer items
    raw_budget_items = _allocate_integer_budget(event.total_budget, event.guest_count, budget_defs)
    budget_result = calculate_budget(event.total_budget, raw_budget_items)

    # Timeline with IST engine
    timeline_result = generate_timeline(event.event_date, event.event_type)

    # Vendors
    vendors: List[VendorItem] = [
        VendorItem(
            id=f"v-{i + 1}-{uuid.uuid4().hex[:6]}",
            category=v["category"],
            service_name=v["service_name"],
            estimated_cost=int(round(event.total_budget * v["ratio"])),
            status="not_contacted",
            contact_notes=f"Recommended for {loc}"
        )
        for i, v in enumerate(vendor_defs)
    ]

    ideas = GroupedIdeas(
        decor=decor_ideas,
        food=food_ideas,
        activities=activity_ideas,
        themes=theme_ideas,
        logistics=logistics_ideas
    )

    now_iso = timeline_result.current_ist_date

    return FullPlanResponse(
        id=f"plan-{uuid.uuid4().hex[:8]}",
        name=event.name,
        event_type=event.event_type,
        event_date=event.event_date,
        location=event.location,
        guest_count=event.guest_count,
        total_budget=event.total_budget,
        style=event.style,
        theme=event.theme,
        special_requirements=event.special_requirements,
        source="rule-based-fallback",
        source_explanation=fallback_reason,
        budget=budget_result,
        timeline=timeline_result,
        vendors=vendors,
        ideas=ideas,
        created_at=now_iso,
        updated_at=now_iso
    )
