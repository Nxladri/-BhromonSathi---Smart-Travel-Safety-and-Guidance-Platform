# BhromonSathi — Smart Travel Safety & Guidance Platform

A monsoon trip-safety and risk-intelligence platform for tourists visiting the Sundarban, built around real historical weather data, a SQL-driven risk engine, and a Retrieval-Augmented Generation (RAG) hazard assistant.


---

## What it does

A user selects a **zone** and **month**, and the platform returns:
- A statistically-derived risk score (rainfall + wind), not an arbitrary threshold
- Zone-specific safety precautions
- Nearby emergency reference centers
- A conversational assistant (RAG-based) that answers open-ended hazard questions, grounded strictly in curated hazard documents
- A downloadable offline PDF safety kit for use in low-connectivity zones

---

## Architecture

```
Frontend (HTML/CSS/JS)
        │
        ▼
FastAPI Backend ── SQL Server (risk data, precautions, emergency centers)
        │
        └──► RAG Pipeline (FAISS + sentence-transformers + Groq LLM)
                    │
                    └──► hazard_docs/ (curated zone-specific text)
```

---

## Key design decisions

- **Risk thresholds are percentile-derived from 10 years of real ERA5 weather data** (36,500+ records across 10 verified zones), not arbitrary cutoffs. Low/Moderate/High boundaries come from the 33rd/66th percentile of the actual data distribution.
- **Precomputed risk table** (`ZoneRiskByMonth`) avoids recalculating aggregates over raw data on every request.
- **Smart zone-input handling**: exact match → fuzzy typo correction → geocoded nearest-zone suggestion for places outside current coverage.
- **RAG is used only where it adds value.** Hazard narratives use semantic retrieval (RAG); safety precautions use direct SQL lookup, since completeness matters more than relevance ranking for safety-critical checklists.
- **No fabricated emergency contact numbers.** Only verified facility names are shown; the universal 100/108 fallback is always displayed instead of guessed phone numbers.
- **Grounded generation.** The LLM is constrained to only use retrieved context and is instructed to disclose gaps honestly rather than infer plausible-sounding but ungrounded claims.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python |
| Database | SQL Server, pyodbc |
| RAG | LangChain, FAISS, sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | Groq API (`openai/gpt-oss-120b`) |
| Frontend | HTML, CSS, JavaScript |
| Weather Data | Open-Meteo (ERA5 reanalysis) |

---

## Evaluation

The RAG pipeline was tested against a 10-question evaluation set scored on four dimensions: retrieval accuracy, groundedness, gap-honesty, and zone-specificity.

**Result: 9/10 passed all dimensions.** The one failure revealed inconsistent gap-disclosure behavior (the model fabricated plausible but ungrounded details for an out-of-scope question), documented as a known limitation rather than concealed.

---

## Setup

```bash
# Clone the repo
git clone https://github.com/Nxladri/-BhromonSathi---Smart-Travel-Safety-and-Guidance-Platform.git
cd BhromonSathi

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r Backend/requirements.txt

# Set up environment variables
# Create Backend/.env with:
# GROQ_API_KEY=your_groq_api_key_here

# Run the backend
cd Backend
uvicorn main:app --reload
```

Open `Frontend/index.html` (via a local server, not `file://`) once the backend is running.

---

## Project Structure

```
Backend/            FastAPI app, SQL connection, RAG pipeline
Frontend/           Dashboard UI, chat assistant, offline kit generation
hazard/             Curated hazard documents (RAG source)
RAG_Architecture/   Notebook used for building/testing the RAG pipeline
Databases/          SQL schema and setup scripts
```

---

## Future Work

- Full offline map tiles (currently: coordinates + Google Maps link only)
- Multi-agent architecture for live weather monitoring and automatic rerouting
- Multi-region expansion (Ayodhya Hills, Jaldapara, Dooars)
- Fine-tuned classifier for community report urgency triage
- Multilingual (Banglish) query normalization

---

## Disclaimer

Student project. Not an official emergency service. Always verify critical information through official government and forest department channels.