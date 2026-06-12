# 🔨 ForgeStudio

ForgeStudio is an AI-powered marketing toolkit designed to help small businesses streamline their content creation workflow. From beating creative blocks to generating polished marketing copy and visuals, ForgeStudio puts the full content pipeline in one place.

---

## Features

### 🧠 Creative Block Assistant
Not sure where to start? ForgeStudio guides you through a structured flow to help you identify what kind of content you need and routes you directly to the right tool — so you never stare at a blank page again.

### ✍️ Marketing Content Generator
Generate professional marketing copy on demand. Describe your product, audience, or campaign goal and ForgeStudio produces ready-to-use content tailored to your brand.

### 🖼️ AI Image Generation
Request custom marketing visuals directly from the platform. Describe the image you need and ForgeStudio generates it alongside your content — no design software required.

### 🔧 Content Improver
Already have a draft? Paste it in and ForgeStudio enhances it based on your instructions. Get multiple iterations back so you can pick the version that fits your brand best.

---

## Tech Stack

- **Backend:** Python, Django
- **AI:** OpenAI API (text generation + image generation)
- **Frontend:** HTML, CSS, JavaScript
- **Environment Management:** python-dotenv

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Keerthailand/ForgeStudio.git
cd ForgeStudio
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

### 7. Open in browser

```
http://localhost:8000
```

---

## Project Structure

```
ForgeStudio/
├── forge/          # Core app logic
├── anvil/          # Content generation
├── improve/        # Content improvement tools
├── posting/        # Content posting features
├── videoscript/    # Video script generation
├── core/           # Shared utilities
├── templates/      # HTML templates
├── static/         # CSS, JS, images
└── media/          # User-uploaded and generated media
```

---

## Future Plans

- User authentication and saved content history
- Social media scheduling and direct posting
- Brand voice customization
- Analytics dashboard to track content performance
