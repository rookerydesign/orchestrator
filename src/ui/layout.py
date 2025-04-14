import gradio as gr
from src.ui.components.prompt_tab import render_prompt_tab
from src.ui.components.lora_tab import render_lora_tab
from src.ui.components.batch_tab import render_batch_tab
from src.ui.components.dispatch_tab import render_dispatch_tab
from src.ui.components.tools_tab import render_tools_tab

def build_ui():
    with gr.Blocks(title="Orchestrator Gradio UI") as app:
        prompt_state = gr.State("")
        print("[DEBUG] Initializing shared prompt state in layout.py")
        
        # Create a numeric state to track active tab index
        active_tab = gr.State(value=0)
        
        with gr.Tabs() as tabs:
            with gr.TabItem("🧠 Prompt Lab"):
                prompt_tab_components = render_prompt_tab(shared_prompt_state=prompt_state)
                
            with gr.TabItem("🎨 LORA Lab"):
                lora_components = render_lora_tab(prompt_state)
                
            with gr.TabItem("📦 Batch Builder"):
                batch_components = render_batch_tab(shared_prompt_state=prompt_state)
                batch_prompt_display = batch_components[3]  # The base_prompt_display component
                
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
            # If we're switching to the Batch Builder tab (index 2)
            if index == 2:
                print(f"[DEBUG] Syncing prompt to batch tab: {prompt_state.value}")
                return prompt_state.value
            return gr.skip()
            
        active_tab.change(
            fn=sync_to_batch_tab,
            inputs=[active_tab],
            outputs=[batch_prompt_display]
        )
        
    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch()
