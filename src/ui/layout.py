import gradio as gr
from src.ui.components.prompt_tab import render_prompt_tab
from src.ui.components.image_settings_tab import render_image_settings_tab
from src.ui.components.batch_tab import render_batch_tab
from src.ui.components.dispatch_tab import render_dispatch_tab
from src.ui.components.tools_tab import render_tools_tab
from src.utils.raw_loader import load_models_and_loras
from src.utils.config_loader import load_config



def build_ui():
    
    cfg = load_config()
    models_loaded, _, loras_loaded = load_models_and_loras(
        cfg["paths"]["model_folder"],
        cfg["paths"]["lora_folder"]
    )
    
    with gr.Blocks(title="Orchestrator Gradio UI") as app:
        prompt_state = gr.State("")
        available_loras = loras_loaded
        active_tab = gr.State(value=0)

        with gr.Tabs() as tabs:
            with gr.TabItem("🧠 Prompt Lab"):
                prompt_tab_components = render_prompt_tab(shared_prompt_state=prompt_state, available_loras=available_loras)

            with gr.TabItem("🎨 Image Gen Settings"):
                render_image_settings_tab()

            with gr.TabItem("📦 Batch Builder"):
                batch_components = render_batch_tab(shared_prompt_state=prompt_state)
                batch_prompt_display = batch_components[3]

            with gr.TabItem("🚀 Dispatch Center"):
                render_dispatch_tab()

            with gr.TabItem("🛠️ Tools"):
                render_tools_tab()

        # Add a manual check that happens whenever a tab is selected
        def on_tab_select(evt: gr.SelectData):
            tab_index = evt.index
            print(f"[DEBUG] Tab selected: {tab_index}")
            return tab_index

        tabs.select(
            on_tab_select,
            None,
            active_tab
        )

        # Add an event that fires when the active tab changes
        def sync_to_batch_tab(index):
            print(f"[DEBUG] Tab index changed to: {index}")
            updates = []

            if index == 2:  # Batch Builder
                print(f"[DEBUG] Syncing prompt to batch tab: {prompt_state.value}")
                updates.append(prompt_state.value)
            else:
                updates.append(gr.skip())

            return updates

        active_tab.change(
            fn=sync_to_batch_tab,
            inputs=[active_tab],
            outputs=[batch_prompt_display]
        )

    print(f"[DEBUG] Available LORAs loaded into state: {len(loras_loaded)} found.")

    return app

    if __name__ == "__main__":
        app = build_ui()
        app.launch()
