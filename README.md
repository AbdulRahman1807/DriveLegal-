# DriveLegal ⚖️🚗
**AI-Powered Traffic Law Advisor for the Indian Motor Vehicles Act**

DriveLegal is an intelligent, multi-platform ecosystem designed to make Indian traffic laws accessible, understandable, and actionable. Powered by Gemini AI and a vector-based legal database, it provides instant legal citations, fine calculations, and compliance checks for everyday drivers and legal professionals.

---

## 📖 Project Overview

### The Problem
Navigating the Indian Motor Vehicles Act (1988, Amended 2019) is complex. Drivers often struggle to understand specific violation codes, associated fines, and their legal rights. Finding accurate, context-aware legal information quickly is a significant challenge.

### The Solution
DriveLegal solves this by combining a highly structured legal database with Advanced AI capabilities. Users can ask natural language questions (e.g., "What is the fine for speeding?") or upload traffic tickets to get immediate, legally sound answers complete with exact citations and penalty details.

### Primary Use Cases
* **Drivers & Citizens:** Quickly understand traffic violations, fines, and compliance requirements.
* **Legal Professionals:** Rapidly retrieve relevant sections of the Motor Vehicles Act with AI-assisted contextual search.
* **Traffic Authorities:** Standardize fine explanations and reference materials.

---

## 🚀 Project Journey & History

* **Inception:** The project began as a backend-focused API to digitize the Motor Vehicles Act using vector embeddings for semantic search.
* **Phase 1 (Backend Foundation):** Development of the FastAPI backend, integration of PostgreSQL with `pgvector`, and implementation of the AI retrieval engine using the Gemini API.
* **Phase 2 (Web App):** Launch of a responsive Next.js frontend, providing a sleek chat interface and ticket upload functionality.
* **Phase 3 (Mobile App):** Expansion to mobile devices via Flutter, ensuring users can access legal advice on the go. Overcame significant challenges with Android SDK configurations and library desugaring to ensure smooth mobile performance.
* **Current State:** A fully operational, three-tier ecosystem (Backend, Web, Mobile) running seamlessly in local development, ready for production deployment and database population.

---

## 🛠 Technical Details

### Technology Stack
* **Backend:** Python, FastAPI, SQLAlchemy (Async), Alembic, Pydantic
* **Database:** PostgreSQL with `pgvector` extension (Vector Database), Redis (Rate Limiting & Caching)
* **AI Model:** Google Gemini 2.5 Flash
* **Web Frontend:** Next.js (React), TypeScript, Vanilla CSS
* **Mobile Frontend:** Flutter (Dart) targeting Android/iOS
* **Infrastructure:** Docker, Docker Compose

### System Architecture
DriveLegal utilizes a Retrieval-Augmented Generation (RAG) architecture:
1. **User Input:** Query is received via Web or Mobile app.
2. **Retrieval (pgvector):** The backend converts the query into an embedding and performs a similarity search against the legal database in PostgreSQL.
3. **Generation (Gemini):** Relevant legal context is injected into a prompt and sent to the Gemini API.
4. **Response:** A highly accurate, cited response is returned to the client.

### Key Design Decisions
* **pgvector over external Vector DBs:** Kept the infrastructure simple and consolidated relational data with vector embeddings in a single PostgreSQL instance.
* **Gemini 2.5 Flash:** Chosen for its extremely fast response times and strong reasoning capabilities.
* **Multi-Platform UI:** Separated Web (Next.js) and Mobile (Flutter) to leverage the specific strengths of each platform while sharing a single unified backend.

---

## 💻 Installation & Setup

### Prerequisites
* Python 3.10+
* Node.js 18+ & npm
* Flutter SDK & Android Studio
* Docker & Docker Compose
* Google Gemini API Key

### Step-by-Step Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/your-org/DriveLegal.git
cd DriveLegal
```

**2. Start Infrastructure (PostgreSQL & Redis)**
```bash
docker-compose up -d
```

**3. Backend Setup**
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and set MASTER_API_KEY=drivelegal-secret-dev-key

# Run Database Migrations
alembic upgrade head

# Start FastAPI Server
PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**4. Web App Setup**
```bash
cd web_app
npm install
# Start Next.js Development Server
npm run dev
```

**5. Mobile App Setup (Android Emulator)**
```bash
cd mobile
flutter pub get
# Ensure an Android Emulator is running, then execute:
flutter run
```

---

## 🧑‍💼 Business Context & Target Audience
DriveLegal democratizes access to legal information. By translating dense legal jargon into easily digestible insights, it empowers Indian citizens to make informed decisions and ensures transparency in traffic law enforcement. 

**Target Audience:**
- Daily commuters and commercial drivers.
- Law students and junior advocates needing rapid legal references.

---

## ✨ Features & Usage

* **AI Chat Advisor:** Ask "What happens if I jump a red light?" and receive a cited answer.
* **Ticket Analysis:** Upload a photo or enter the details of a traffic challan to verify the fine amount and legal basis.
* **Cross-Platform Sync:** (Upcoming) Consistent session management across web and mobile.

### Common Workflow
1. Open the Web App (`localhost:3000`) or Mobile App.
2. Type a scenario into the chat interface.
3. Review the AI's response, which includes `relevance_scores` and direct links/citations to the Motor Vehicles Act.

---

## 🤝 Development & Contributing

### Contributing Workflow
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

### Code Organization
* `/backend/` - FastAPI application, database models, and AI engine logic.
  * `/backend/api/` - REST API routes.
  * `/backend/chat/` - Gemini integration and prompt engineering.
* `/web_app/` - Next.js frontend application.
* `/mobile/` - Flutter application.
* `/alembic/` - Database migration scripts.

### Testing
We use `pytest` for backend testing.
```bash
pytest tests/
```

---

## 🗺 Roadmap & Future Plans

- [ ] **Data Seeding:** Populate the PostgreSQL database with the complete text of the Motor Vehicles Act and state-specific fine tables.
- [ ] **OCR Integration:** Automatically extract text from uploaded traffic challan images.
- [ ] **Multi-lingual Support:** Add support for Hindi and regional Indian languages.
- [ ] **User Authentication:** Allow users to save their chat history and track multiple vehicles/tickets.

---

## 🚑 Troubleshooting

* **Hydration Errors in Web App:** If using browser extensions (like Grammarly), they may inject HTML into the `<body>`. We have mitigated this with `suppressHydrationWarning`, but keep extensions in mind if UI issues arise.
* **Mobile Build Fails (Android):** Ensure you have an explicit `minSdk = 21` and `coreLibraryDesugaring` enabled in `android/app/build.gradle.kts` due to modern Java time APIs used by plugins.
* **Backend API returns 401:** Ensure your frontend applications are sending the `Authorization: Bearer <your-master-key>` header.

---

## 🔗 Resources

* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* [pgvector GitHub](https://github.com/pgvector/pgvector)
* [Next.js Documentation](https://nextjs.org/docs)
* [Flutter Documentation](https://flutter.dev/docs)

*For bug reports or feature requests, please open an issue in the GitHub repository.*
