from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

SESSION_DATA = {}

app = FastAPI()

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Sentences
SENTENCES = [
    "I want to explain my idea clearly and confidently today.",
    "Today I am going to describe my favorite hobby in detail.",
    "Please read this sentence at a steady and comfortable speed.",
    "The students completed their assignments before the deadline.",
    "Sally sees seven shiny seashells by the seashore."
]

# -------------------------------
# PAGE ROUTES
# -------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/speech", response_class=HTMLResponse)
def speech_page(request: Request):
    return templates.TemplateResponse(
        "index1.html",
        {
            "request": request,
            "sentence": SENTENCES[0]
        }
    )

@app.get("/final/{session_id}", response_class=HTMLResponse)
def final_page(request: Request, session_id: str):
    return templates.TemplateResponse(
        "index2.html",
        {
            "request": request,
            "session_id": session_id
        }
    )

# -------------------------------
# ANALYSIS ENDPOINT
# -------------------------------

@app.post("/analyze")
def analyze(data: dict):
    session_id = data["session_id"]
    text = data["speech"].lower()
    index = data["index"]
    duration = data["duration"]

    if session_id not in SESSION_DATA:
        SESSION_DATA[session_id] = []

    # ---- Pace (for all sentences)
    words_count = len(text.split())
    wpm = (words_count / duration) * 60 if duration > 0 else 0
    SESSION_DATA[session_id].append({"type": "pace", "wpm": int(wpm)})

    # ---- Sentence-specific checks
    if index == 0:  # Stuttering
        words = text.split()
        repetitions = sum(
            1 for i in range(len(words) - 1)
            if words[i] == words[i + 1]
        )
        SESSION_DATA[session_id].append(
            {"type": "stuttering", "count": repetitions}
        )

    elif index == 1:  # Fillers
        expected_words = SENTENCES[index].lower().split()
        spoken_words = text.split()
        filler_prefixes = ["uh", "um", "ah", "a", "ea", "er", "li"]

        filler_count = 0
        min_len = min(len(expected_words), len(spoken_words))

        for i in range(min_len):
            if spoken_words[i] != expected_words[i]:
                if (spoken_words[i][:1] in filler_prefixes or
                        spoken_words[i][:2] in filler_prefixes):
                    filler_count += 1

        if len(spoken_words) > len(expected_words):
            for w in spoken_words[len(expected_words):]:
                if w[:1] in filler_prefixes or w[:2] in filler_prefixes:
                    filler_count += 1

        SESSION_DATA[session_id].append(
            {"type": "fillers", "count": filler_count}
        )

    elif index == 3:  # Clarity
        expected = SENTENCES[index].lower().split()
        spoken = text.split()
        missing = max(len(expected) - len(spoken), 0)
        SESSION_DATA[session_id].append(
            {"type": "clarity", "missing": missing}
        )

    elif index == 4:  # Lisp
        expected_s = SENTENCES[index].lower().count("s")
        spoken_s = text.count("s")
        mismatch = abs(expected_s - spoken_s)
        SESSION_DATA[session_id].append(
            {"type": "lisp", "mismatch": mismatch}
        )

    return {"status": "saved"}

# -------------------------------
# NORMALIZED RESULTS
# -------------------------------

@app.get("/results/{session_id}")
def get_results(session_id: str):
    data = SESSION_DATA.get(session_id, [])

    summary = {
        "stuttering": 0,
        "pace": [],
        "clarity": 0,
        "hesitation": 0,
        "articulation": 0
    }

    for item in data:
        if item["type"] == "stuttering":
            summary["stuttering"] += item.get("count", 0)

        elif item["type"] == "pace":
            summary["pace"].append(item.get("wpm", 0))

        elif item["type"] == "clarity":
            summary["clarity"] += item.get("missing", 0)

        elif item["type"] == "fillers":
            summary["hesitation"] += item.get("count", 0)

        elif item["type"] == "lisp":
            summary["articulation"] += item.get("mismatch", 0)

    def level(val, low, med):
        if val == 0:
            return 0
        elif val <= low:
            return 1
        elif val <= med:
            return 2
        else:
            return 3

    avg_pace = sum(summary["pace"]) / max(len(summary["pace"]), 1)
    pace_deviation = abs(avg_pace - 135) / 135 * 100

    return {
        "Stuttering": level(summary["stuttering"], 2, 5),
        "Hesitation": level(summary["hesitation"], 2, 4),
        "Pace": level(pace_deviation, 20, 30),
        "Clarity": level(summary["clarity"], 2, 4),
        "Articulation": level(summary["articulation"], 1, 2)
    }

# -------------------------------
# FINAL FLUENCY SCORING
# -------------------------------

@app.post("/final_results")
def final_results(data: dict):

    st = data["stuttering"]
    hs = data["hesitation"]
    pc = data["pace"]
    cl = data["clarity"]
    ar = data["articulation"]

    weighted_score = (
        st * 25 * 0.15 +
        hs * 25 * 0.25 +
        pc * 25 * 0.20 +
        cl * 25 * 0.30 +
        ar * 25 * 0.10
    )

    fluency = max(0, min(100, round(100 - weighted_score)))

    verdict = (
        "Excellent" if fluency >= 90 else
        "Good" if fluency >= 75 else
        "Needs Improvement" if fluency >= 50 else
        "Low Clarity"
    )

    feedback = {
        "stuttering": [
            "Great! No stuttering detected.",
            "Minor repetitions.",
            "Some stuttering affected flow.",
            "Frequent stuttering — slow down beginnings."
        ][st],
        "hesitation": [
            "No hesitation or fillers.",
            "A few fillers — overall good.",
            "Moderate fillers — try silent pauses.",
            "High fillers — replace 'um' with calm pauses."
        ][hs],
        "pace": [
            "Natural pace — smooth delivery.",
            "Slightly fast/slow.",
            "Uneven pacing — try speaking in steady chunks.",
            "Very fast/slow — clarity drops noticeably."
        ][pc],
        "clarity": [
            "Clear and complete sentences.",
            "A few unclear words.",
            "Some incomplete phrases.",
            "Many unclear words — slow down."
        ][cl],
        "articulation": [
            "Pronunciation is clear.",
            "Minor unclear sounds.",
            "Some consonant distortion.",
            "Multiple articulation errors."
        ][ar]
    }

    # weakest = max(
    #     {"stuttering": st, "hesitation": hs, "pace": pc, "clarity": cl, "articulation": ar},
    #     key=lambda k: locals()[k]
    # )
    severity_map = {
        "stuttering": st,
        "hesitation": hs,
        "pace": pc,
        "clarity": cl,
        "articulation": ar
    }

    weakest = max(severity_map, key=severity_map.get)


    exercises = {
        "stuttering": "Practice slow sentence starts.",
        "hesitation": "Replace fillers with silent pauses.",
        "pace": "Read alternating slow & fast lines.",
        "clarity": "Over-articulate each word once.",
        "articulation": "Practice 'sa-sha-tha' sounds."
    }

    return {
        "fluency_score": fluency,
        "verdict": verdict,
        "feedback": feedback,
        "training_plan": {
            "weak_area": weakest,
            "exercise": exercises[weakest]
        }
    }
