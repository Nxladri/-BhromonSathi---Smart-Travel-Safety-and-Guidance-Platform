"""
Generates hazard briefing text files for all Sundarban zones,
using reusable templates instead of hand-writing 90+ paragraphs.

How it works:
1. Each hazard type has ONE template (written once)
2. Each zone has a small "profile" — just which hazards apply,
   at what severity, and 1-2 zone-specific facts
3. The script fills the templates with zone-specific facts and
   writes one .txt file per zone — ready to embed for RAG later
"""

import os
import shutil

OUTPUT_DIR = "hazard_docs"
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)  # remove any leftover files from a previous run
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------
# STEP 1: Write each hazard template ONCE.
# {severity} and {detail} get filled in per zone below.
# ---------------------------------------------------------------
HAZARD_TEMPLATES = {
    "tiger": (
        "Royal Bengal Tiger: {severity} risk of tiger straying/encounter in this "
        "forest block, based on peer-reviewed casualty studies. Risk is highest "
        "during pre-monsoon (April-June) and early winter (January-March). "
        "{detail} For boat-based tourists staying on marked watchtower routes, "
        "actual risk is low — recorded incidents mainly involve fishermen, honey "
        "collectors, and crab collectors entering the deep forest, not tourists "
        "on guided boats."
    ),
    "crocodile": (
        "Crocodile: {severity} risk near creek edges and water access points. "
        "Regional data shows attacks peak in winter (December-February) and "
        "early monsoon (May-July), with risk rising further during high tide "
        "when crocodiles move closer to banks. {detail} Avoid standing at the "
        "water's edge near watchtowers, especially during rising tide."
    ),
    "snake": (
        "Snakes: {severity} risk, particularly during monsoon (June-September) "
        "when flooding pushes snakes out of burrows onto the same raised paths "
        "tourists use. {detail} Wear ankle-covering, closed footwear at all times "
        "outside the boat."
    ),
    "tide": (
        "High Tide / Tidal Risk: {severity} — boat schedules at this stop are "
        "tide-dependent, not fixed-clock. {detail} Confirm departure timing with "
        "the boatman directly rather than relying on a printed schedule; boats "
        "can be stranded on mudflats if timing is misjudged."
    ),
    "mud": (
        "Soft Mud / Sinking Ground: {severity} risk near jetty steps and mudflats, "
        "worse after rain. {detail} Mangrove pneumatophores (breathing roots) also "
        "create sharp trip hazards just off marked wooden paths — never step off "
        "the designated plank path."
    ),
    "monsoon": (
        "Monsoon Weather: {severity} risk of sudden squalls, heavy rain, and rough "
        "river conditions during June-September. Storms can turn calm conditions "
        "violent within 30-40 minutes. {detail} Boat operations may be suspended "
        "with little notice during heavy weather."
    ),
    "insects": (
        "Mosquitoes & Insects: {severity} risk, rising with monsoon humidity. "
        "{detail} Sundarban is a malaria-prone zone — carry repellent and consult "
        "a doctor about prophylaxis before traveling, especially for multi-day trips."
    ),
    "boat": (
        "Boat / Water Transport: {severity} risk related to vessel availability and "
        "safety. {detail} Always confirm the boat is registered with West Bengal "
        "Tourism or the Forest Department before booking; avoid unlicensed operators."
    ),
    "connectivity": (
        "Network Connectivity: {severity} — {detail} Download offline "
        "maps and emergency information before reaching this zone; do not rely on "
        "live internet access here."
    ),
    "navigation": (
        "Getting Lost / Navigation: {severity} risk in the surrounding creek network, "
        "which has many visually similar channels. {detail} Never allow the boat to "
        "separate from a known guide or licensed boatman, even for short detours."
    ),
}

# ---------------------------------------------------------------
# STEP 2: Define each zone's profile — just the specifics that
# differ from zone to zone. This is the only part you need to
# fill in by hand, and it's short (a few words per hazard).
# ---------------------------------------------------------------
ZONE_PROFILES = {
    "Sajnekhali": {
        "tiger": ("Moderate", "This is a core forest-entry watchtower zone with regular tiger movement nearby."),
        "crocodile": ("Moderate", "The mangrove interpretation centre pond and creek edge are known crocodile habitat."),
        "snake": ("Moderate", "Ground-level paths near the watchtower flood easily in monsoon."),
        "tide": ("Moderate", "Main forest-entry jetty; tide timing affects both arrival and return."),
        "mud": ("Moderate", "Jetty steps are a known slip hazard in wet conditions."),
        "monsoon": ("Moderate-High", "Open water crossing to reach this zone is exposed to sudden squalls."),
        "insects": ("Moderate", "Dense mangrove cover near the interpretation centre increases exposure."),
        "boat": ("Low", "This is an official, well-regulated forest department entry point."),
        "connectivity": ("Poor", "drops to zero shortly after departing Gosaba."),
        "navigation": ("Low", "Main entry channel is well-marked and frequently traveled."),
    },
    "Sudhanyakhali": {
        "tiger": ("Moderate", "Frequent deer and tiger sightings reported near this watchtower."),
        "crocodile": ("Moderate-High", "Known crocodile basking area directly below the watchtower."),
        "snake": ("Moderate", "Mangrove park trail floods in heavy rain."),
        "tide": ("Moderate", "Watchtower creek access depends on tide level."),
        "mud": ("Moderate", "Sweet-water pond area gets slippery after rain."),
        "monsoon": ("Moderate-High", "Similar squall exposure to Sajnekhali."),
        "insects": ("Moderate-High", "Standing sweet-water pond increases mosquito breeding nearby."),
        "boat": ("Low", "Regulated stop within the eco-tourism zone."),
        "connectivity": ("Poor", "no reliable signal at the watchtower itself."),
        "navigation": ("Low", "Short, well-marked creek route from Sajnekhali."),
    },
    "Dobanki": {
        "tiger": ("Moderate-High", "This forest block shows elevated straying risk per casualty studies, peaking pre-monsoon and early winter."),
        "crocodile": ("Moderate", "Creek crossing to reach the canopy walk passes known crocodile zones."),
        "snake": ("Moderate-High", "Canopy walk's forest floor approach is a common snake area in monsoon."),
        "tide": ("Moderate-High", "Remote location — return boat is strictly tide-dependent."),
        "mud": ("Moderate", "Approach path to the canopy walk gets muddy quickly."),
        "monsoon": ("High", "Farthest core stop from Gosaba — longest exposure to open water during storms."),
        "insects": ("Moderate-High", "Dense canopy cover increases insect exposure along the walkway."),
        "boat": ("Moderate", "Longer transit distance means boat reliability matters more here."),
        "connectivity": ("Poor", "effectively zero signal throughout this stop."),
        "navigation": ("Moderate", "Approach creek has several similar-looking branches."),
    },
    "Netidhopani": {
        "tiger": ("Moderate", "Remote forest block with regular tiger presence near the temple ruins."),
        "crocodile": ("Moderate", "Watchtower creek has recorded crocodile activity."),
        "snake": ("Moderate-High", "Overgrown ruins area is a known snake habitat."),
        "tide": ("High", "One of the farthest stops — tide miscalculation risks a long stranded wait."),
        "mud": ("Moderate", "Ruins site access path is uneven and slippery when wet."),
        "monsoon": ("High", "Most remote core stop — longest return journey if weather turns."),
        "insects": ("Moderate-High", "Ruins and surrounding forest hold standing water after rain."),
        "boat": ("Moderate", "Longest boat transit of the core circuit — plan buffer time."),
        "connectivity": ("Poor", "no signal — the most isolated of the core stops."),
        "navigation": ("Moderate-High", "Furthest creek approach with multiple similar channels."),
    },
    "Jharkhali": {
        "tiger": ("Low", "Gateway zone with the tiger rescue center — controlled environment, not open forest."),
        "crocodile": ("Low-Moderate", "Some creek exposure near the rescue center boundary."),
        "snake": ("Low-Moderate", "Less dense forest cover than core zones."),
        "tide": ("Low-Moderate", "Partially road-accessible, reducing full tide dependency."),
        "mud": ("Low", "Better-maintained paths than deep-forest stops."),
        "monsoon": ("Moderate", "Still exposed to regional storm patterns."),
        "insects": ("Moderate", "Standard monsoon mosquito exposure."),
        "boat": ("Low", "Short water crossings only, from a well-established gateway point."),
        "connectivity": ("Fair", "partial signal available near the main gateway area."),
        "navigation": ("Low", "Road + short boat access reduces route confusion."),
    },
    "Gosaba": {
        "tiger": ("Low", "Inhabited town — not a forest-entry zone."),
        "crocodile": ("Low-Moderate", "Some risk along the town's river edge, historically the highest-recorded block for incidents, though mainly affecting local fishers, not tourists."),
        "snake": ("Low", "Developed area with limited forest cover."),
        "tide": ("Low", "Road and ferry access reduce tide dependency."),
        "mud": ("Low", "Paved/maintained areas in the town center."),
        "monsoon": ("Moderate", "Still subject to regional storm and rainfall patterns."),
        "insects": ("Moderate", "Standard monsoon-season exposure."),
        "boat": ("Low", "Well-established ferry routes."),
        "connectivity": ("Good", "last point with reliable network before the forest zones."),
        "navigation": ("Low", "Town with clear roads and signage."),
    },
    "Pakhiralay": {
        "tiger": ("Low", "Village stay-point, not a forest-entry zone."),
        "crocodile": ("Low-Moderate", "Some river-edge exposure near homestay jetties."),
        "snake": ("Low-Moderate", "Village and agricultural land, less dense forest."),
        "tide": ("Low-Moderate", "Homestay jetty access is mildly tide-affected."),
        "mud": ("Low-Moderate", "Jetty paths can be slippery after rain."),
        "monsoon": ("Moderate", "Regional storm exposure applies."),
        "insects": ("Moderate", "Village pond areas can increase mosquito presence."),
        "boat": ("Low", "Short, frequent local boat services."),
        "connectivity": ("Fair", "patchy but sometimes available near the village center."),
        "navigation": ("Low", "Well-known village with established routes."),
    },
    "Dayapur": {
        "tiger": ("Low", "Village/stay point, not core forest."),
        "crocodile": ("Low-Moderate", "River-edge exposure near sunset viewing points."),
        "snake": ("Low-Moderate", "Semi-rural surroundings."),
        "tide": ("Moderate", "Boat-only access — tide timing affects arrival/departure."),
        "mud": ("Low-Moderate", "Riverside paths can be slick after rain."),
        "monsoon": ("Moderate", "Regional exposure, boat-only access adds sensitivity to storms."),
        "insects": ("Moderate", "Standard monsoon exposure near water."),
        "boat": ("Low-Moderate", "Regular but boat-only service."),
        "connectivity": ("Fair-Poor", "inconsistent, weaker than Gosaba."),
        "navigation": ("Low", "Short, well-traveled route from Gosaba."),
    },
    "Gadkhali": {
        "tiger": ("Low", "Departure point, not forest zone."),
        "crocodile": ("Low", "Minimal water-edge tourist exposure at the jetty."),
        "snake": ("Low", "Developed departure-point area."),
        "tide": ("Moderate", "Boat departures from here are tide-scheduled."),
        "mud": ("Low", "Maintained jetty infrastructure."),
        "monsoon": ("Moderate", "Open jetty exposed to wind/rain during departures."),
        "insects": ("Low-Moderate", "Less standing water than deep-forest stops."),
        "boat": ("Low", "Main organized departure point for tours."),
        "connectivity": ("Good", "road-accessible with reasonably reliable signal."),
        "navigation": ("Low", "Clear, signed departure point."),
    },
    "Panchamukhani": {
        "tiger": ("Moderate", "Deep-forest river confluence, not a livelihood/tourist walking zone but near known forest blocks."),
        "crocodile": ("Moderate-High", "Confluence of five channels increases water-edge encounter probability."),
        "snake": ("N/A", "River-route point, not a walking/disembark zone — minimal direct snake exposure."),
        "tide": ("High", "Multiple converging tidal channels make timing especially complex here."),
        "mud": ("N/A", "Not a disembark point in most itineraries."),
        "monsoon": ("High", "Open confluence is highly exposed to wind and sudden weather shifts."),
        "insects": ("Moderate", "Standard monsoon exposure over open water."),
        "boat": ("Moderate-High", "Complex currents at the confluence require experienced boat handling."),
        "connectivity": ("Poor", "zero signal — deep interior river route."),
        "navigation": ("High", "Five converging channels are a well-known point of route confusion."),
    },
}

# ---------------------------------------------------------------
# STEP 3: Generate one text file PER HAZARD TYPE, with a section
# for each of the 10 zones inside it. This groups content the
# other way around — e.g. "snakes.txt" covers snake risk across
# all zones in one file, instead of one file per zone covering
# all hazards.
# ---------------------------------------------------------------
HAZARD_DISPLAY_NAMES = {
    "tiger": "Royal Bengal Tiger Risk",
    "crocodile": "Crocodile Risk",
    "snake": "Snake Risk",
    "tide": "High Tide / Tidal Risk",
    "mud": "Soft Mud / Sinking Ground Risk",
    "monsoon": "Monsoon Weather Risk",
    "insects": "Mosquitoes & Insect-Borne Disease Risk",
    "boat": "Boat / Water Transport Risk",
    "connectivity": "Network Connectivity Risk",
    "navigation": "Getting Lost / Navigation Risk",
}


def generate_zone_document(zone_name, profile):
    lines = [f"HAZARD BRIEFING: {zone_name.upper()}", "=" * 60, ""]
    for hazard_key, template in HAZARD_TEMPLATES.items():
        if hazard_key not in profile:
            continue
        severity, detail = profile[hazard_key]
        if severity == "N/A":
            continue
        filled = template.format(severity=severity, detail=detail)
        lines.append(filled)
        lines.append("")
    return "\n".join(lines)


def main():
    for zone_name, profile in ZONE_PROFILES.items():
        doc = generate_zone_document(zone_name, profile)
        filename = zone_name.lower().replace(" ", "_") + ".txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"Generated: {filepath}")

    print(f"\nDone. {len(ZONE_PROFILES)} zone hazard-briefing files created in '{OUTPUT_DIR}/'")
    print("Each file covers all applicable hazards for that one zone.")
    print("These are ready to be chunked and embedded for the RAG pipeline.")


if __name__ == "__main__":
    main()
