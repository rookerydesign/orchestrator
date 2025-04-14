# Orchestrator for SD Forge
# Main app launcher — initializes and runs the Gradio interface
# Uses modular UI components defined in /src/ui/layout.py

from src.ui.layout import build_ui

if __name__ == "__main__":
    app = build_ui()
    app.launch()
