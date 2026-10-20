import streamlit as st
from config import GEMINI_API_KEY, HF_TOKEN, GEMINI_MODEL, HF_MODEL, APP_NAME

st.set_page_config(page_title=APP_NAME, page_icon="🌈", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp{background:linear-gradient(135deg,#f5f7ff,#effbf8,#fff9ef);color:#17233d}
h1,h2,h3{font-family:'Space Grotesk',sans-serif;color:#17233d}
.hero{padding:1.5rem 1.8rem;border-radius:24px;background:linear-gradient(120deg,#17233d,#30466e);color:white;margin-bottom:1rem}
.hero h1{color:white!important;margin:0}.hero p{color:#e3eaff;margin:.4rem 0 0}
</style>
""", unsafe_allow_html=True)

MOODS = ["Stressed / Overwhelmed", "Tired / Low Energy", "Excited / Energized", "Calm / Happy"]
QUESTS = {
    "Stressed / Overwhelmed": ["🧭 Choose one priority and write the smallest next step.", "🌬️ Try five comfortable slow breaths or a gentle stretch.", "🪜 Work for five minutes, or ask someone you trust for help."],
    "Tired / Low Energy": ["💧 Drink water and have a snack if you are hungry.", "🌙 Take a short quiet break or gently stretch.", "🎯 Choose one tiny task—or decide what can wait."],
    "Excited / Energized": ["✨ Write down what you are excited about.", "🚀 Spend ten focused minutes on one goal.", "🤝 Share your idea or celebrate a small win."],
    "Calm / Happy": ["🌿 Name one thing that is going well.", "💌 Send a kind message or offer a small act of help.", "📓 Write one sentence about a moment you want to remember."]
}


def simple_mood(text):
    t = text.lower()
    groups = {
        "Stressed / Overwhelmed": ["stress", "overwhelmed", "worried", "anxious", "panic", "pressure", "deadline", "scared", "angry"],
        "Tired / Low Energy": ["tired", "exhausted", "sleepy", "drained", "no energy", "can't focus", "cannot focus", "sad"],
        "Excited / Energized": ["excited", "thrilled", "can't wait", "cannot wait", "pumped", "amazing", "won", "awesome"],
        "Calm / Happy": ["calm", "peaceful", "happy", "grateful", "thankful", "relaxed", "good day", "content"]
    }
    scores = {m: sum(1 for word in words if word in t) for m, words in groups.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "Calm / Happy"


def classify_with_hf(text):
    import ollama
    import json

    prompt = f"""
Classify the emotion in this text into exactly one category:
anger, disgust, fear, sadness, joy, love, surprise, neutral.

Text: {text}

Return only JSON in this format:
{{"emotion": "fear"}}
"""

    try:
        response = ollama.chat(
            model="llama3.2:1b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an emotion classifier. "
                        "Return only valid JSON with one emotion label."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            format="json",
            options={"temperature": 0, "num_predict": 50}
        )

        result = json.loads(response["message"]["content"])
        label = str(result.get("emotion", "neutral")).lower()

        valid_labels = {
            "anger", "disgust", "fear", "sadness",
            "joy", "love", "surprise", "neutral"
        }

        if label not in valid_labels:
            label = "neutral"

        mapping = {
            "anger": "Stressed / Overwhelmed",
            "disgust": "Stressed / Overwhelmed",
            "fear": "Stressed / Overwhelmed",
            "sadness": "Tired / Low Energy",
            "joy": "Calm / Happy",
            "love": "Calm / Happy",
            "surprise": "Excited / Energized",
            "neutral": simple_mood(text)
        }

        mood = mapping.get(label, simple_mood(text))

        return mood, label, 1.0

    except Exception:
        return simple_mood(text), "local_fallback", 0.0

def gemini_reply(prompt, history=None, system_instruction=None):
    import ollama

    instructions = system_instruction or (
        "You are Mood AI, a kind, age-appropriate wellbeing companion "
        "for students. Be warm, non-judgmental, and concise. Help users "
        "reflect and break tasks into small steps. Do not diagnose or "
        "claim to be a therapist. If a user may be in immediate danger, "
        "encourage contacting a trusted adult or local emergency help."
    )

    messages = [{"role": "system", "content": instructions}]

    for item in (history or [])[-8:]:
        role = "user" if item["role"] == "user" else "assistant"
        messages.append({
            "role": role,
            "content": item["content"]
        })

    messages.append({"role": "user", "content": prompt})

    response = ollama.chat(
        model="llama3.2:1b",
        messages=messages,
        options={"temperature": 0.7, "num_predict": 500}
    )

    answer = response["message"]["content"].strip()

    if not answer:
        raise RuntimeError("The local AI returned an empty response.")

    return answer
st.markdown('<div class="hero"><h1>🌈 AI Mood Quest</h1><p>Understand the moment. Take one small step. Build momentum.</p></div>', unsafe_allow_html=True)
with st.sidebar:
    st.title("🌈 Quest Hub")
    page = st.radio("Navigate", ["✨ Create a Quest", "💬 Mood AI Chat", "🔌 API Diagnostics", "ℹ️ About & Safety"])
    st.caption("Diary text is sent to an AI provider only when you choose an AI-powered action. Avoid identifying or highly sensitive details.")

if page == "✨ Create a Quest":
    st.subheader("✍️ What's on your mind?")
    entry = st.text_area("Diary entry", placeholder="Example: I have two assignments due tomorrow and feel overwhelmed...", height=140, max_chars=1500)
    if st.button("✨ Understand my mood & build quest", type="primary"):
        if len(entry.strip()) < 5:
            st.warning("Write a little more so the app has something to analyse.")
        else:
            mood = None
            if HF_TOKEN:
                try:
                    mood, label, score = classify_with_hf(entry)
                    st.success(f"Hugging Face detected **{label}** (model score {score:.0%}). Suggested app mood: **{mood}**.")
                except Exception as exc:
                    st.warning(f"Hugging Face request failed: {type(exc).__name__}: {exc}")
            if mood is None:
                mood = simple_mood(entry)
                st.info("Using the local fallback mood guess because model-based classification wasn't available.")
            mood = st.selectbox("Choose the mood that fits you best", MOODS, index=MOODS.index(mood), key="chosen_mood")
            st.markdown(f"### {mood}")
            if GEMINI_API_KEY:
                try:
                    with st.spinner("Gemini is personalising your quest..."):
                        custom = gemini_reply(f"The student's chosen mood is: {mood}. Diary entry: {entry!r}. Create exactly 3 short, safe, age-appropriate, optional actions personalised to this context. Number them 1-3. Do not diagnose or give medical advice.", system_instruction="Create short, supportive and safe wellbeing quests for students. Never diagnose. Actions must be optional and low-risk.")
                    st.markdown("#### ✨ Gemini's personalised quest")
                    st.write(custom)
                except Exception as exc:
                    st.warning(f"Gemini quest generation failed: {type(exc).__name__}: {exc}")
                    for step in QUESTS[mood]: st.markdown(f"- {step}")
            else:
                st.write("Here is a small, optional three-step quest:")
                for step in QUESTS[mood]: st.markdown(f"- {step}")
            st.caption("Mood predictions can be wrong. This is a reflection tool, not a diagnosis.")

elif page == "💬 Mood AI Chat":
    st.subheader("💬 Talk with Mood AI")
    st.write("Talk through a tough moment, plan a small task, or reflect on your day.")
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]): st.markdown(message["content"])
    prompt = st.chat_input("What's on your mind?")
    if prompt:
        st.session_state.chat_history.append({"role":"user", "content":prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                if GEMINI_API_KEY:
                    with st.spinner("Mood AI is thinking..."): answer = gemini_reply(prompt, st.session_state.chat_history[:-1])
                else:
                    answer = "Gemini isn't connected yet. Name one thing that feels hardest right now, then choose one small next step."
            except Exception as exc:
                answer = f"I couldn't reach Gemini just now. Technical detail: {type(exc).__name__}: {exc}"
            st.markdown(answer)
        st.session_state.chat_history.append({"role":"assistant", "content":answer})
    if st.button("Clear chat"):
        st.session_state.chat_history = []
        st.rerun()

elif page == "🔌 API Diagnostics":
    st.subheader("🔌 API connection diagnostics")
    st.write("Credential checks do not reveal the keys themselves.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Google Gemini")
        st.write("Credential detected:", "✅ Yes" if GEMINI_API_KEY else "❌ No")
        if st.button("Test Gemini API"):
            try:
                with st.spinner("Testing Gemini..."): result = gemini_reply("Reply with exactly: Gemini connection successful.", system_instruction="Reply exactly as requested.")
                st.success("Gemini API call succeeded.")
                st.code(result)
            except Exception as exc: st.error(f"Gemini API test failed: {type(exc).__name__}: {exc}")
    with c2:
        st.markdown("### Hugging Face")
        st.write("Credential detected:", "✅ Yes" if HF_TOKEN else "❌ No")
        if st.button("Test Hugging Face API"):
            try:
                with st.spinner("Testing Hugging Face..."): mood, label, score = classify_with_hf("I feel worried and overwhelmed about my work.")
                st.success("Hugging Face API call succeeded.")
                st.write(f"Raw model label: **{label}** · score **{score:.0%}**")
                st.write(f"Mapped app mood: **{mood}**")
            except Exception as exc: st.error(f"Hugging Face API test failed: {type(exc).__name__}: {exc}")
    st.info("If credentials show No, verify the secrets.toml filename and location, then fully stop and restart Streamlit. Request errors may relate to quota, permissions, model/provider availability or network issues.")

else:
    st.subheader("ℹ️ About & Safety")
    st.markdown("**Purpose:** AI Mood Quest supports reflection and small, manageable actions. It is not a diagnosis or a replacement for trusted adults or professional support.\n\n**Privacy:** Chat history is kept in the current app session, not a database. If you use Gemini or Hugging Face, text sent for an AI request is processed by that external service. Avoid names, addresses, passwords and highly sensitive diary details.\n\n**Limitations:** Emotion models can misread sarcasm, slang and mixed feelings. Students can correct the mood. Suggestions are optional.")

st.markdown("---")
st.caption("AI Mood Quest · Student wellbeing prototype · Take one small step at a time 💚")
