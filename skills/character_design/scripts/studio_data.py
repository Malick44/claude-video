"""
Daily Character Studio - Dynamic Look Director & Prompt Formulas
Ported and enhanced from https://daily-character-studio.higgsfield.app/

Instead of rigid deterministic presets, this module provides an intelligent
styling director that dynamically synthesizes hair, wardrobe, environment,
lighting, camera lens, and micro-expressions from any creative brief or video scene,
while locking the permanent facial identity anchor.
"""

import re
from typing import Dict, Any, List, Optional

# Curated reference taxonomy (Inspirational starting points & vocabulary)
HAIR_INSPIRATION: List[str] = [
    "High ponytail with soft face-framing strands",
    "Long knotless box braids with subtle gold cuffs",
    "Textured wavy French bob with natural volume",
    "Loose beach curls with effortless movement",
    "Sleek low ballet bun with center part",
    "90s voluminous blowout with layered ends",
    "Wavy lob grazing collarbones with tousled texture",
    "Casual messy top knot with wispy edges",
    "Textured pixie cut with tapered sides",
    "Close buzz cut highlighting sharp cheekbones"
]

OUTFIT_INSPIRATION: List[str] = [
    "Vintage washed ivory cotton tee tucked into high-waisted raw denim jeans",
    "Tailored navy wool double-breasted blazer over crisp white silk camisole",
    "Breezy sage green linen sundress with delicate shoulder straps",
    "Heather grey oversized fleece crewneck sweatshirt with vintage wash joggers",
    "Seamless ribbed athletic crop top in terracotta with high-waisted performance leggings",
    "Minimalist black silk slip evening dress with delicate square neckline",
    "Distressed dark brown leather biker jacket over fitted ribbed black turtleneck",
    "Oversized chunky knit merino wool sweater in oatmeal with relaxed trousers",
    "Classic tailored camel double-faced wool trench coat over crisp white poplin shirt",
    "Relaxed French-tucked striped linen button-down shirt with ivory wide-leg trousers"
]

LOCATION_INSPIRATION: List[str] = [
    "Sunlit corner café table with warm morning window light and steam rising from ceramic mugs",
    "Modern Scandinavian living room with sheer linen curtains and warm oak flooring",
    "Chef's kitchen with marble countertops, brass hardware, and warm morning diffused light",
    "Architectural open-plan office with floor-to-ceiling glass windows and soft morning daylight",
    "Green city park pathway lined with flowering jacaranda trees under dappled afternoon sun",
    "Vibrant downtown city street corner with subtle motion blur of pedestrians and soft bokeh",
    "Minimalist modern art gallery with concrete polished floors and museum directional spotlights",
    "Rooftop terrace overlooking city skyline at golden hour with warm sunset rim light",
    "Golden hour coastal beach with soft sea mist, gentle rolling surf, and warm low-angle sun",
    "Modern creator podcast studio with acoustic oak wood slats, warm neon accent tubes, and soft diffused key light",
    "Luxury boutique gym studio with matte black equipment and natural light from warehouse skylights",
    "High-end boutique hotel lobby with velvet armchairs, marble fireplace, and amber architectural uplights"
]

ACTIVITY_INSPIRATION: List[str] = [
    "Relaxed natural portrait making confident eye contact with camera",
    "Reading an open vintage hardcover book, eyes thoughtfully scanning the pages",
    "Carefully pouring hot water into a ceramic pour-over coffee filter, smelling the aroma",
    "Walking purposefully forward towards camera, coat swaying gently with each step",
    "Speaking directly to camera with animated, authentic hand gestures and warm engagement",
    "Typing thoughtfully on an ultrathin aluminum laptop, glancing up at screen",
    "Holding a warm ceramic mug with both hands, taking a gentle sip and smiling",
    "Tilting face upward into the afternoon sun with closed eyes and a contented smile",
    "Turning gracefully over shoulder toward camera as if caught mid-thought",
    "Laughing authentically mid-conversation with natural eye crinkles and radiant warmth"
]

FRAMINGS: List[str] = [
    "Waist-up medium portrait (ideal for dialogue and UGC talking heads)",
    "Full body fashion editorial framing (head to toe outfit showcase)",
    "Front-facing selfie handheld perspective (authentic vlog aesthetic)",
    "Tight close-up portrait (intense emotion, facial details, and eye contact)",
    "Wide cinematic establishing shot (character positioned within environment)"
]

EXPRESSIONS: List[str] = [
    "Relaxed, approachable smile with warm authentic eye crinkles",
    "Quietly confident, self-assured direct gaze with subtle knowing smile",
    "Deeply thoughtful and contemplative, gaze drifting toward window",
    "Energetic and excited, radiant smile and lively wide eyes",
    "Calm, grounded neutral resting expression with serene posture",
    "Intensely engaged and focused, leaning slightly in with keen interest",
    "Playful warmth, eyebrow slightly raised with an amused grin"
]

LIGHTING_INSPIRATION: List[str] = [
    "Warm diffused morning window light with soft fill and subtle catchlights in eyes",
    "Cinematic golden hour sunlight flaring softly with warm golden rim light on hair",
    "Moody chiaroscuro with soft warm key light and deep atmospheric shadows",
    "Crisp overcast daylight providing ultra-flattering shadowless skin illumination",
    "Warm 3200K tungsten practical lamp glow mixed with cool blue twilight window fill",
    "Vibrant neon ambient glow casting magenta and cyan highlights across cheekbones"
]

ASPECT_RATIOS: List[str] = ["9:16", "16:9", "1:1"]

# Default permanent seed avatar reference sheet from daily-character-studio.higgsfield.app
SEED_REFERENCE: Dict[str, Any] = {
    "name": "Original avatar reference sheet",
    "type": "image/png",
    "id": "41caaf52-6a98-47f1-ac60-7e17f94a852a",
    "url": "https://d2ol7oe51mr4n9.cloudfront.net/user_3GmR7Jp2PzgbsQ3k2MF0dSXcthM/41caaf52-6a98-47f1-ac60-7e17f94a852a.png",
    "src": "https://d2ol7oe51mr4n9.cloudfront.net/user_3GmR7Jp2PzgbsQ3k2MF0dSXcthM/41caaf52-6a98-47f1-ac60-7e17f94a852a.png",
}

DEFAULT_SETTINGS: Dict[str, Any] = {
    "hair": HAIR_INSPIRATION[0],
    "outfit": OUTFIT_INSPIRATION[0],
    "location": LOCATION_INSPIRATION[0],
    "activity": ACTIVITY_INSPIRATION[0],
    "framing": "Waist-up",
    "expression": EXPRESSIONS[0],
    "lighting": LIGHTING_INSPIRATION[0],
    "lens": "35mm lens, f/1.8 shallow depth of field",
    "accessories": "Small gold hoop earrings; no microphone",
    "notes": "",
    "aspectRatio": "9:16",
}

# Inspirational preset archetypes (illustrative reference points, not rigid boundaries)
PRESETS: List[Dict[str, Any]] = [
    {
        "id": "cafe",
        "title": "Weekend café",
        "prompt": "A relaxed café moment",
        "src": "/assets/cafe.webp",
        "settings": {
            "hair": "High ponytail with soft face-framing strands",
            "outfit": "Vintage washed ivory cotton tee tucked into high-waisted raw denim jeans",
            "location": "Sunlit corner café table with warm morning window light and steam rising from ceramic mugs",
            "activity": "Carefully pouring hot water into a ceramic pour-over coffee filter, smelling the aroma",
            "framing": "Waist-up",
            "expression": "Relaxed, approachable smile with warm authentic eye crinkles",
            "lighting": "Warm diffused morning window light with soft fill",
            "lens": "50mm lens, f/2.0, gentle background blur",
            "accessories": "Small gold hoop earrings, delicate gold chain necklace",
            "notes": "Natural window light, warm ceramic coffee cup in hand",
            "aspectRatio": "9:16",
        },
        "animation": {
            "motion": "Use the approved image as the exact first frame. Gentle steam rising from coffee, natural breathing, subtle eye contact and relaxed smile. Smooth subtle handheld movement. Continuous camera, no cuts.",
            "duration": 5
        }
    },
    {
        "id": "office",
        "title": "Office day",
        "prompt": "A confident day at work",
        "src": "/assets/office.webp",
        "settings": {
            "hair": "Long knotless box braids with subtle gold cuffs",
            "outfit": "Tailored navy wool double-breasted blazer over crisp white silk camisole",
            "location": "Architectural open-plan office with floor-to-ceiling glass windows and soft morning daylight",
            "activity": "Relaxed natural portrait making confident eye contact with camera",
            "framing": "Waist-up",
            "expression": "Quietly confident, self-assured direct gaze with subtle knowing smile",
            "lighting": "Clean architectural diffused morning daylight",
            "lens": "85mm portrait prime lens, crisp subject separation",
            "accessories": "Minimalist wristwatch, small stud earrings",
            "notes": "Clean architectural glass interior, soft diffused morning daylight",
            "aspectRatio": "9:16",
        },
        "animation": {
            "motion": "Use the approved image as the exact first frame. Confident head tilt, subtle blink, slight nod as if listening in a business meeting. No morphing, continuous camera.",
            "duration": 5
        }
    },
    {
        "id": "home",
        "title": "At-home reader",
        "prompt": "An easy afternoon at home",
        "src": "/assets/home.webp",
        "settings": {
            "hair": "Textured wavy French bob with natural volume",
            "outfit": "Breezy sage green linen sundress with delicate shoulder straps",
            "location": "Modern Scandinavian living room with sheer linen curtains and warm oak flooring",
            "activity": "Reading an open vintage hardcover book, eyes thoughtfully scanning the pages",
            "framing": "Waist-up",
            "expression": "Deeply thoughtful and contemplative, gaze drifting toward window",
            "lighting": "Soft indirect daylight filtering through sheer curtains",
            "lens": "35mm documentary focal length, authentic organic depth",
            "accessories": "Tortoiseshell reading glasses perched on nose or resting on table",
            "notes": "Cozy sunbeam on wooden floor, peaceful domestic vibe",
            "aspectRatio": "9:16",
        },
        "animation": {
            "motion": "Use the approved image as the exact first frame. Eyes glance up from the book toward the camera with a gentle warm smile, delicate finger turns the page. Continuous camera.",
            "duration": 5
        }
    },
    {
        "id": "podcast",
        "title": "Creator podcast host",
        "prompt": "Authentic creator speaking to camera",
        "src": "/assets/podcast.webp",
        "settings": {
            "hair": "90s voluminous blowout with layered ends",
            "outfit": "Heather grey oversized fleece crewneck sweatshirt with vintage wash",
            "location": "Modern creator podcast studio with acoustic oak wood slats, warm neon accent tubes",
            "activity": "Speaking directly to camera with animated, authentic hand gestures and warm engagement",
            "framing": "Close-up portrait",
            "expression": "Intensely engaged and focused, leaning slightly in with keen interest",
            "lighting": "Warm studio key light, subtle cyan and amber rim lighting on shoulders",
            "lens": "50mm f/1.4 cinematic lens, creamy background bokeh",
            "accessories": "Minimalist black wireless earbuds, subtle gold ring",
            "notes": "Warm studio bokeh, acoustic slat wood backdrop, vibrant rim lighting",
            "aspectRatio": "9:16",
        },
        "animation": {
            "motion": "Use the approved image as the exact first frame. Authentic talking-head speech motion, expressive facial articulation, natural head movement, realistic mouth gestures. Continuous camera.",
            "duration": 5
        }
    },
    {
        "id": "fitness",
        "title": "Morning fitness session",
        "prompt": "Active lifestyle workout look",
        "src": "/assets/fitness.webp",
        "settings": {
            "hair": "High ponytail with sleek brushed back finish",
            "outfit": "Seamless ribbed athletic crop top in terracotta with high-waisted performance leggings",
            "location": "Luxury boutique gym studio with matte black equipment and natural light from warehouse skylights",
            "activity": "Walking purposefully forward towards camera with energetic stride",
            "framing": "Full body",
            "expression": "Energetic and excited, radiant smile and lively wide eyes",
            "lighting": "Bright diffused overhead skylight illuminating natural skin sheen",
            "lens": "35mm dynamic wide lens, energetic perspective",
            "accessories": "Matte black smart fitness tracker, insulated stainless steel water bottle",
            "notes": "Bright daylight studio, matte rubber flooring, energetic posture",
            "aspectRatio": "9:16",
        },
        "animation": {
            "motion": "Use the approved image as the exact first frame. Athlete taking an energetic step forward, smiling confidently, smooth camera push-in. High frame rate feel.",
            "duration": 5
        }
    },
    {
        "id": "rooftop",
        "title": "Golden hour rooftop",
        "prompt": "Cinematic evening skyline portrait",
        "src": "/assets/rooftop.webp",
        "settings": {
            "hair": "Loose beach curls with effortless movement caught in breeze",
            "outfit": "Relaxed French-tucked striped linen button-down shirt with ivory wide-leg trousers",
            "location": "Rooftop terrace overlooking city skyline at golden hour with warm sunset rim light",
            "activity": "Tilting face upward into the afternoon sun with closed eyes and a contented smile",
            "framing": "Waist-up",
            "expression": "Relaxed, approachable smile with warm authentic eye crinkles",
            "lighting": "Warm 2800K low-angle golden hour backlight creating glowing halo on hair",
            "lens": "85mm cinema prime, breathtaking golden hour flares",
            "accessories": "Vintage round tortoiseshell sunglasses pushed up on head, simple gold band",
            "notes": "Warm golden hour backlight, city skyline bokeh, gentle breeze",
            "aspectRatio": "9:16",
        },
        "animation": {
            "motion": "Use the approved image as the exact first frame. Wind gently blowing hair, golden sunlight flaring softly across the lens, subject turns toward camera with a smile. Continuous cinematic slow motion.",
            "duration": 5
        }
    }
]


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a preset definition by its ID."""
    for p in PRESETS:
        if p["id"] == preset_id:
            return p
    return None


def synthesize_look_from_brief(
    brief: str,
    overrides: Optional[Dict[str, Any]] = None,
    aspect_ratio: str = "9:16"
) -> Dict[str, Any]:
    """
    Intelligently synthesize a cohesive 7-point character styling blueprint
    from any freeform creative brief, story beat, or video script.

    Extracts or infers:
    - hair (texture, cut, styling)
    - outfit (fabrics, colors, tailoring)
    - location (environment, architectural details, depth)
    - activity (natural kinetic micro-actions)
    - framing (camera distance & angle)
    - expression (micro-emotional nuance)
    - lighting (color temperature, direction, atmosphere)
    - lens (focal length and depth of field)
    - accessories (props and realistic accents)
    """
    clean_brief = brief.strip()
    lower_brief = clean_brief.lower()

    # 1. Infer Location / Setting
    location = ""
    if any(k in lower_brief for k in ["cafe", "coffee", "latte", "barista"]):
        location = "Cozy neighborhood coffee shop with warm wooden counters, espresso machine steam, and amber pendant lights"
    elif any(k in lower_brief for k in ["office", "startup", "corporate", "meeting", "workday", "boardroom"]):
        location = "Architectural sunlit office space with frosted glass partitions, fiddle-leaf fig, and morning light"
    elif any(k in lower_brief for k in ["kitchen", "cooking", "dinner", "breakfast", "bake", "chef"]):
        location = "Modern chef's kitchen with butcher-block island, hanging copper cookware, and warm diffused sunlight"
    elif any(k in lower_brief for k in ["living room", "home", "bedroom", "couch", "cozy", "sunday"]):
        location = "Warm lived-in living room with bouclé sofa, stacked art books, and natural window daylight"
    elif any(k in lower_brief for k in ["street", "city", "downtown", "urban", "sidewalk", "commute", "tokyo", "new york"]):
        location = "Textured downtown city street corner with cast-iron architecture, warm storefront glows, and soft bokeh"
    elif any(k in lower_brief for k in ["rooftop", "sunset", "golden hour", "skyline", "terrace"]):
        location = "Boutique rooftop terrace overlooking a glowing metropolitan skyline during late golden hour"
    elif any(k in lower_brief for k in ["gym", "workout", "fitness", "yoga", "athletic", "running"]):
        location = "Minimalist natural light fitness studio with white brick walls and polished maple wood flooring"
    elif any(k in lower_brief for k in ["podcast", "interview", "microphone", "studio", "creator", "youtube"]):
        location = "Acoustic-treated studio with warm walnut wood slat panels and soft directional rim lighting"
    elif any(k in lower_brief for k in ["beach", "ocean", "coast", "sea", "sand"]):
        location = "Pebbled coastal beach under breezy late-afternoon skies with soft ocean foam in distant background"
    elif any(k in lower_brief for k in ["cyberpunk", "neon", "future", "sci-fi", "night"]):
        location = "Rain-slicked alleyway with vibrant magenta and cyan neon sign reflections and atmospheric street steam"
    elif any(k in lower_brief for k in ["hospital", "doctor", "clinic", "nurse", "er", "medical"]):
        location = "Quiet hospital corridor near large glass windows with soft blue-grey morning light"
    elif any(k in lower_brief for k in ["library", "bookstore", "study", "books"]):
        location = "Sunlit historic library with towering dark walnut bookshelves and green banker's lamps"
    else:
        # Default to clean contextual environment derived directly from brief
        location = f"Atmospheric environment reflecting {clean_brief}, rich with natural textures and practical light sources"

    # 2. Infer Wardrobe / Outfit
    outfit = ""
    if any(k in lower_brief for k in ["doctor", "hospital", "nurse", "medical"]):
        outfit = "Fitted deep navy blue surgical scrubs with soft cotton undershirt and clean lines"
    elif any(k in lower_brief for k in ["cyberpunk", "futuristic", "sci-fi"]):
        outfit = "Matte black technical waterproof jacket with subtle iridescent lining over dark ribbed compression shirt"
    elif any(k in lower_brief for k in ["workout", "fitness", "gym", "yoga", "running", "sweat"]):
        outfit = "Seamless clay-tone athletic compression crop top and matching high-waisted performance leggings"
    elif any(k in lower_brief for k in ["business", "professional", "office", "lawyer", "executive", "meeting"]):
        outfit = "Tailored charcoal grey wool blazer with silk lapel over ivory silk scoop-neck camisole"
    elif any(k in lower_brief for k in ["evening", "party", "gala", "dinner", "cocktail", "formal"]):
        outfit = "Floor-length minimalist emerald satin dress with delicate draping and open back"
    elif any(k in lower_brief for k in ["casual", "cozy", "lazy", "sunday", "morning", "relax"]):
        outfit = "Oversized waffle-knit cream cardigan over worn vintage cotton tee and washed relaxed denim"
    elif any(k in lower_brief for k in ["summer", "hot", "sun", "beach", "vacation"]):
        outfit = "Breezy ochre linen wrap dress with breathable natural weave"
    elif any(k in lower_brief for k in ["streetwear", "cool", "edgy", "skate", "trendy"]):
        outfit = "Boxy cropped washed leather jacket over vintage band tee and wide-leg olive cargo trousers"
    elif any(k in lower_brief for k in ["winter", "cold", "snow", "autumn", "fall"]):
        outfit = "Heavyweight camel cashmere turtleneck under structured double-breasted wool overcoat"
    else:
        outfit = f"Stylishly tailored, believable outfit suited for {clean_brief}, rendered in premium natural textiles"

    # 3. Infer Hairstyle
    hair = ""
    if any(k in lower_brief for k in ["tired", "exhausted", "late night", "2am", "3am", "bed"]):
        hair = "Tousled lived-in bun with loose face-framing tendrils and natural texture"
    elif any(k in lower_brief for k in ["workout", "gym", "running", "fitness", "active"]):
        hair = "High snatched athletic ponytail with neat brushed finish"
    elif any(k in lower_brief for k in ["professional", "office", "executive", "formal"]):
        hair = "Sleek low chignon bun with razor-sharp center part and smooth glossy sheen"
    elif any(k in lower_brief for k in ["casual", "cafe", "weekend", "breeze", "wind"]):
        hair = "Soft effortless shoulder-length waves with natural bounce and sun-kissed dimension"
    elif any(k in lower_brief for k in ["cyberpunk", "edgy", "futuristic"]):
        hair = "Sharp asymmetrical textured bob with wet-look styling"
    elif any(k in lower_brief for k in ["cozy", "autumn", "fall", "coffee"]):
        hair = "Voluminous wavy lob with soft curtain bangs framing cheekbones"
    else:
        hair = "Natural textured hair styled effortlessly with believable volume and organic flyaways"

    # 4. Infer Activity
    activity = ""
    if any(k in lower_brief for k in ["coffee", "tea", "drink", "sip"]):
        activity = "Cradling warm ceramic mug with both hands, pausing mid-thought to take a slow sip"
    elif any(k in lower_brief for k in ["read", "book", "studying"]):
        activity = "Gently turning page of book, eyes deeply focused then glancing up thoughtfully"
    elif any(k in lower_brief for k in ["walk", "commute", "street", "stroll"]):
        activity = "Walking naturally towards camera with relaxed gait and confident posture"
    elif any(k in lower_brief for k in ["speak", "talk", "podcast", "explain", "pitch", "vlog"]):
        activity = "Speaking animatedly to camera with expressive hand gestures and authentic engagement"
    elif any(k in lower_brief for k in ["laptop", "computer", "type", "code", "work"]):
        activity = "Hands hovering over laptop keyboard in moment of creative breakthrough, subtle smile"
    elif any(k in lower_brief for k in ["laugh", "joy", "fun", "happy"]):
        activity = "Throwing head back in spontaneous genuine laughter with natural radiance"
    elif any(k in lower_brief for k in ["tired", "exhausted", "hard day"]):
        activity = "Resting chin gently in hand, taking a slow deep breath with relaxed posture"
    else:
        activity = f"Engaging naturally in action: {clean_brief}, avoiding stiff poses"

    # 5. Infer Framing & Lens
    framing = "Waist-up"
    lens = "50mm f/1.8 lens, natural human eye perspective with gentle background separation"
    if any(k in lower_brief for k in ["close-up", "eyes", "face", "portrait", "emotion", "whisper"]):
        framing = "Close-up portrait"
        lens = "85mm f/1.4 cinema prime lens with razor-sharp focus on iris and soft creamy background blur"
    elif any(k in lower_brief for k in ["full body", "outfit", "head to toe", "walking", "runway"]):
        framing = "Full body"
        lens = "35mm f/2.0 documentary lens capturing subject in relation to environment"
    elif any(k in lower_brief for k in ["selfie", "vlog", "phone", "pov"]):
        framing = "Front-camera handheld selfie"
        lens = "24mm wide mobile lens with subtle natural wide-angle intimacy"
    elif any(k in lower_brief for k in ["wide", "cinematic", "epic", "landscape"]):
        framing = "Wide cinematic medium-long shot"
        lens = "35mm anamorphic lens with subtle horizontal light streaks and wide cinematic depth"

    # 6. Infer Expression
    expression = "Relaxed smile"
    if any(k in lower_brief for k in ["tired", "exhausted", "late", "weary"]):
        expression = "Quietly weary but resilient gaze, soft knowing half-smile with tired eyes"
    elif any(k in lower_brief for k in ["confident", "boss", "leader", "pitch", "proud"]):
        expression = "Quietly confident, self-assured direct gaze with a subtle empowered smirk"
    elif any(k in lower_brief for k in ["laugh", "happy", "joy", "celebrate"]):
        expression = "Bursting into radiant spontaneous laughter with genuine eye crinkles"
    elif any(k in lower_brief for k in ["focused", "study", "code", "intense", "craft"]):
        expression = "Intense creative focus with eyes locked intently on work"
    elif any(k in lower_brief for k in ["thoughtful", "nostalgic", "wistful", "dreamy"]):
        expression = "Thoughtful, contemplative gaze looking gently off-camera"
    elif any(k in lower_brief for k in ["mysterious", "secret", "thriller", "drama"]):
        expression = "Enigmatic, calm and observant with unreadable subtle poise"

    # 7. Infer Lighting
    lighting = "Warm diffused daylight with soft shadow transitions"
    if any(k in lower_brief for k in ["sunset", "golden hour", "dusk"]):
        lighting = "Low-angle 2700K golden hour sunlight creating warm rim light on hair and soft amber flare"
    elif any(k in lower_brief for k in ["neon", "cyberpunk", "night club", "party"]):
        lighting = "Vibrant contrast of magenta neon key light and deep cyan ambient shadow fill"
    elif any(k in lower_brief for k in ["morning", "breakfast", "sunrise", "dawn"]):
        lighting = "Soft pale morning sunlight streaming through windows with delicate dust motes"
    elif any(k in lower_brief for k in ["dramatic", "moody", "noir", "shadow"]):
        lighting = "Dramatic chiaroscuro with single directional warm spotlight and deep atmospheric shadows"
    elif any(k in lower_brief for k in ["overcast", "rain", "fog", "cloudy"]):
        lighting = "Soft, diffused overcast sky providing perfectly even, cinematic, flattering illumination"

    # 8. Accessories & Props
    accessories = "Minimal jewelry matching the context, realistic tangible props"
    if any(k in lower_brief for k in ["coffee", "cafe", "latte"]):
        accessories = "Handcrafted ceramic mug with subtle glaze, thin gold band on finger"
    elif any(k in lower_brief for k in ["doctor", "medical", "hospital"]):
        accessories = "Lightweight matte black stethoscope draped loosely around neck, clean digital watch"
    elif any(k in lower_brief for k in ["business", "office", "exec"]):
        accessories = "Slim leather folio notebook, minimalist brushed steel watch, subtle stud earrings"
    elif any(k in lower_brief for k in ["podcast", "creator"]):
        accessories = "Discreet black wireless ear monitor, minimal silver signet ring"

    synthesized = {
        "hair": hair,
        "outfit": outfit,
        "location": location,
        "activity": activity,
        "framing": framing,
        "expression": expression,
        "lighting": lighting,
        "lens": lens,
        "accessories": accessories,
        "notes": f"Creative brief: {clean_brief}",
        "aspectRatio": aspect_ratio,
    }

    # Apply manual overrides if user provided specific flags
    if overrides:
        for k, v in overrides.items():
            if v is not None and str(v).strip():
                synthesized[k] = v

    return synthesized


def image_prompt(settings: Dict[str, Any], mode: str = "new") -> str:
    """
    Construct the canonical Character Studio prompt with anti-drift identity anchor.
    Takes either synthesized or customized settings and produces a high-fidelity
    image generation prompt suitable for GPT Image 2.5 / 2.0.

    Modes:
      - 'new': Create a fresh lifestyle shot using the identity reference.
      - 'hair': Edit only hairstyle from an approved image while locking everything else.
      - 'outfit': Edit only clothing from an approved image while locking everything else.
    """
    mode_lower = mode.lower().strip()
    if mode_lower in ("hair", "change hair"):
        change = "Edit only the hairstyle of the final reference image. Preserve its clothing, pose, background, lighting, and framing."
    elif mode_lower in ("outfit", "change outfit"):
        change = "Edit only the clothing of the final reference image. Preserve its hairstyle, pose, background, lighting, and framing."
    else:
        change = "Create one photorealistic cinematic photograph."

    hair_val = settings.get("hair", HAIR_INSPIRATION[0])
    outfit_val = settings.get("outfit", OUTFIT_INSPIRATION[0])
    location_val = settings.get("location", LOCATION_INSPIRATION[0])
    activity_val = settings.get("activity", ACTIVITY_INSPIRATION[0])
    framing_val = settings.get("framing", "Waist-up")
    expression_val = settings.get("expression", "Relaxed smile")
    lighting_val = settings.get("lighting", "Natural diffused light")
    lens_val = settings.get("lens", "35mm prime lens, shallow depth of field")
    accessories_val = settings.get("accessories", "Natural understated accessories")
    notes_val = settings.get("notes", "").strip()

    if mode_lower in ("hair", "change hair"):
        styling_clause = f"Hairstyle: {hair_val}."
        context_clause = "Keep all other details (outfit, pose, lighting, background) identical to the final reference."
    elif mode_lower in ("outfit", "change outfit"):
        styling_clause = f"Outfit: {outfit_val}."
        context_clause = "Keep all other details (hairstyle, pose, lighting, background) identical to the final reference."
    else:
        styling_clause = f"Hairstyle: {hair_val}. Outfit: {outfit_val}."
        context_clause = (
            f"Location: {location_val}. Activity: {activity_val}. "
            f"Framing: {framing_val}. Expression: {expression_val}. "
            f"Lighting & Atmosphere: {lighting_val}. Camera Lens: {lens_val}. "
            f"Accessories & Details: {accessories_val}."
        )

    notes_clause = f"\nCreative Direction: {notes_val}" if notes_val else ""

    prompt = (
        f"{change}\n"
        f"IDENTITY: The first reference is the permanent identity source. "
        f"Preserve the exact same recognizable facial geometry, eyes, nose, smile, skin tone, "
        f"apparent adult age, and body proportions. Reference sheets depict ONE person: "
        f"output only one person in one photograph, never a collage. Hair and wardrobe are changeable, not identity.\n"
        f"{styling_clause} {context_clause}"
        f"{notes_clause}\n"
        f"Natural human skin texture, believable micro-shadows, photographic grain. "
        f"No labels, no text overlays, no contact sheet, no watermark, no digital airbrushing."
    )
    return prompt.strip()


def motion_prompt(
    motion_direction: Optional[str] = None,
    framing: str = "Waist-up",
    expression: str = "Relaxed smile",
    activity: str = "portrait",
    lighting: str = "ambient light"
) -> str:
    """
    Construct the canonical Seedance 2.5 video motion prompt.
    Takes an approved look still image as the starting frame and generates
    smooth temporal physics, realistic breathing, and subtle kinetic motion.
    """
    if motion_direction and motion_direction.strip():
        base_motion = motion_direction.strip()
    else:
        base_motion = (
            f"Natural breathing, gentle head movement and {expression.lower()}. "
            f"Subtle realistic motion matching: {activity.lower()}. Keep the exact same face, "
            f"hairstyle, outfit, and scene throughout."
        )

    prompt = (
        f"Use the approved image as the exact first frame. "
        f"{base_motion} "
        f"Continuous camera, steady focal distance, believable micro-expressions, no morphing, no cuts."
    )
    return prompt.strip()


def synthesize_story_pack(
    story_brief: str,
    scene_count: int = 5,
    identity_ref: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dynamically synthesize a complete multi-scene character wardrobe pack
    matching a narrative story arc or video script.
    """
    ref_id = identity_ref or SEED_REFERENCE["id"]

    # Arc progressions
    arc_beats = [
        ("scene_01_hook_opening", "Opening Hook / Morning Preparation", "morning", "intense curious focus"),
        ("scene_02_rising_action", "Rising Action / Journey & Commute", "daylight", "purposeful determination"),
        ("scene_03_core_confrontation", "Core Beat / Main Activity & Speaking", "afternoon", "deep engagement"),
        ("scene_04_turning_point", "Climax / Turning Point", "golden hour", "emotional resonance"),
        ("scene_05_resolution_outro", "Resolution / Sunset Reflection & CTA", "sunset / evening", "relaxed confidence")
    ]

    scenes = []
    for idx, (scene_id, title, time_of_day, mood) in enumerate(arc_beats[:scene_count]):
        beat_brief = f"{story_brief} — {title}. Time: {time_of_day}, Mood: {mood}."
        settings = synthesize_look_from_brief(beat_brief)

        img_prompt = image_prompt(settings, mode="new")
        motion_dir = (
            f"Use the approved image as the exact first frame. "
            f"Subject demonstrates {settings['activity'].lower()} with {settings['expression'].lower()}. "
            f"Subtle natural breathing, soft head movement, continuous camera."
        )
        vid_prompt = motion_prompt(
            motion_direction=motion_dir,
            framing=settings["framing"],
            expression=settings["expression"],
            activity=settings["activity"]
        )

        scenes.append({
            "scene_id": scene_id,
            "scene_number": idx + 1,
            "title": title,
            "beat_summary": beat_brief,
            "settings": settings,
            "image_prompt": img_prompt,
            "video_prompt": vid_prompt,
            "suggested_duration": 5
        })

    return {
        "story_brief": story_brief,
        "identity_reference": ref_id,
        "aspect_ratio": "9:16",
        "scenes": scenes
    }
