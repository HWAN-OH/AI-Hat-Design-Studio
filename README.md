# AI Hat Design Studio: A Persona-Driven Design Automation MVP

This project is a proof-of-concept for a revolutionary approach to manufacturing R&D. It's a simple, interactive application that demonstrates how a **role-based AI agent**, powered by a Large Language Model (LLM), can understand natural language, interpret structured data (BOM), and control 3D modeling software to automate the initial product design process.

**This isn't just about designing hats. It's about proving a new way of working.**

![Simulator Screenshot](https://github.com/HWAN-OH/AI-Hat-Design-Studio/assets/174906093/b5b5b0e5-7798-466d-979f-d31e9c5625b5)


## The Vision: Solving the "Knowledge Drain"

In modern manufacturing, the most critical challenge is the permanent loss of expert knowledge when talented engineers leave. This project is the first step toward solving this "Knowledge Drain" by creating an AI system that can learn, execute, and preserve the core knowledge of our best designers and engineers.

The "AI Hat Design Studio" serves as a simple, elegant, and visually intuitive testbed to validate this grand vision.

## Key Features

-   **Persona-Driven AI (`Forma`):** The core of the system is an AI agent named `Forma`, whose role, personality, and knowledge are defined in an external `persona_forma.yml` file. This makes the AI's behavior predictable and controllable.
-   **Natural Language Interface:** Interact with `Forma` using plain English. Simply tell it what you want, from changing a color to applying a complex style like a "cowboy hat."
-   **BOM-Aware Logic (`BoMi`):** The system's initial agent, `BoMi`, parses a Bill of Materials (`bom_data.csv`) to understand available parts, materials, and costs, grounding the AI's suggestions in reality.
-   **Live 3D Assembly & Modification:** `Forma` translates your commands into actions, controlling a live 3D viewer to assemble parts and modify the design in real-time.

## System Architecture

This MVP demonstrates a powerful concept: separating the AI's **'brain' (LLM)** from its **'hands' (Python code & APIs)**, orchestrated by a human architect.

1.  **User Input:** The user provides a natural language command (e.g., "make it a cowboy hat").
2.  **Persona Imprinting:** The `app.py` sends the user's command along with `Forma`'s entire persona (`persona_forma.yml`) and the list of available parts (`bom_data.csv`) to the Gemini LLM.
3.  **LLM as the 'Brain':** The LLM, now acting as `Forma`, doesn't just translate words. It *understands* the request based on its given knowledge and returns a structured JSON command (e.g., `{"action": "apply_style", "style_name": "cowboy hat", ...}`).
4.  **Python as the 'Hands':** The `app.py` receives this structured command and executes it. It looks up the correct 3D models from the BOM and updates the 3D viewer.

This clear separation of roles is the core of the **MirrorMind** philosophy.

## How to Run

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/HWAN-OH/AI-Hat-Design-Studio.git](https://github.com/HWAN-OH/AI-Hat-Design-Studio.git)
    cd AI-Hat-Design-Studio
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your API Key:**
    -   Get your Google AI API key from [Google AI Studio](https://aistudio.google.com/).
    -   Deploy this app to Streamlit Community Cloud and add your key to the `Secrets` management. The key name should be `GOOGLE_AI_API_KEY`.

4.  **Run the app:**
    ```bash
    streamlit run app.py
    ```

## Developed By

This project was architected and developed by **[OH SEONG-HWAN](https://www.linkedin.com/in/shoh1224/)**, a leader with deep expertise across the energy, manufacturing, and technology sectors, as a proof-of-concept for a new paradigm in human-AI collaboration.

## License

This project is licensed under the MIT License. Copyright (c) 2025, OH SEONG-HWAN.
