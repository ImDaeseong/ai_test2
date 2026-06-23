"""k-pop, modern-kpop 프로파일을 kpop-girl 바로 앞에 삽입"""
import json

with open("genre_profiles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

kpop_profile = {
    "name": "k-pop",
    "softening_type": "groove",
    "keywords": [
        "k-pop",
        "kpop",
        "korean pop",
        "idol pop",
        "idol group"
    ],
    "stage_energy": "bright synchronized idol live performance, choreography-driven group energy, vibrant chorus lift",
    "lighting_style": "bright colorful idol stage lighting, sharp choreography-sync strobes, vivid neon color wash, crowd lightstick shimmer",
    "camera_style": "fast choreography-sync cuts, tight idol close-ups, wide synchronized formation shots, vivid chorus crane reveal",
    "special_effects": "colorful sparkle bursts, synchronized strobe flashes, idol neon glow particles, lightstick shimmer waves",
    "roles": {
        "vocal": "performing with bright confident screen-face display, idol synchronization energy",
        "vocal_action": "clean precise pointing gesture on the hook, bright smile-nod on the chorus beat",
        "guitar": "delivering crisp bright idol-band gesture with vivid clean precision",
        "bass": "maintaining energetic synchronized bass-groove stance with idol group drive",
        "drum": "delivering synchronized beat with crisp idol-stage precision pose",
        "crowd": "with vibrant lightstick shimmer, bright neon glow, and synchronized fan chant energy",
        "stage": "performing a bright synchronized K-pop idol concert under vivid colorful stage light",
        "outfit": "coordinated idol stage suit with vivid color trim and star badge detail",
        "prop": "glowing lightstick or holographic idol card held raised with idol confidence",
        "color": "vivid mint and electric pink",
        "reference_image": "k-pop.png",
        "outfit_girl": "bright coordinated idol outfit with vivid pink and white trim, star badge on white helmet, idol performance detail"
    }
}

modern_kpop_profile = {
    "name": "modern-kpop",
    "softening_type": "groove",
    "keywords": [
        "modern k-pop",
        "modern kpop",
        "new k-pop",
        "new kpop",
        "contemporary k-pop",
        "4th gen kpop",
        "4세대 아이돌"
    ],
    "stage_energy": "sleek contemporary K-pop live performance, refined synchronized energy, sophisticated chorus lift",
    "lighting_style": "sleek monochrome idol stage lighting, refined color accent wash, smooth choreography-sync lighting, subtle crowd shimmer",
    "camera_style": "smooth refined close-ups, elegant wide stage shots, sophisticated chorus camera movement, clean contemporary idol framing",
    "special_effects": "subtle sleek sparkle accents, refined light pulses, smooth neon bloom, sophisticated stage shimmer",
    "roles": {
        "vocal": "performing with refined sophisticated screen-face display, sleek contemporary idol energy",
        "vocal_action": "elegant composed gesture toward the crowd, confident chin-up expression on the chorus",
        "guitar": "delivering sleek sophisticated idol-band gesture with refined contemporary energy",
        "bass": "maintaining smooth refined bass-groove stance with contemporary idol presence",
        "drum": "delivering crisp contemporary beat with sleek idol-stage precision pose",
        "crowd": "with refined light shimmer, subtle neon glow, and composed synchronized fan energy",
        "stage": "performing a sleek contemporary K-pop concert under refined monochrome stage light",
        "outfit": "sleek contemporary idol outfit with refined metallic trim and sophisticated badge",
        "prop": "wireless mic held with sleek contemporary idol presence",
        "color": "deep navy and electric white",
        "reference_image": "modern k-pop.png",
        "outfit_girl": "sleek contemporary idol outfit with deep navy and silver trim, refined badge on dark helmet, sophisticated performance detail"
    }
}

profiles = data["profiles"]
names = [p["name"] for p in profiles]

# kpop-girl 앞에 삽입
kpop_girl_idx = names.index("kpop-girl")
profiles.insert(kpop_girl_idx, modern_kpop_profile)
profiles.insert(kpop_girl_idx, kpop_profile)

data["profiles"] = profiles
print("추가 후 k-pop 관련 순서:")
for i, p in enumerate(profiles):
    if "kpop" in p["name"].lower() or "k-pop" in p["name"].lower():
        print(f"  [{i}] {p['name']}")

with open("genre_profiles.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("저장 완료 — 총", len(profiles), "개 프로파일")
