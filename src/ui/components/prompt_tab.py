# Orchestrator for SD Forge - Prompt Lab Tab
# This tab allows the user to generate a single prompt using wildcard logic,
# optionally enhance it using a local LLM, and pass it forward for batch building.

import gradio as gr
from src.core.prompt_generator import generate_prompts
from src.core.llm_interface import enhance_prompt_with_llm

def render_prompt_tab(shared_prompt_state=None):
    print(f"[DEBUG] Prompt tab loaded. shared_prompt_state exists: {shared_prompt_state is not None}")
    if shared_prompt_state is not None:
        print(f"[DEBUG] Initial prompt state value in prompt_tab: {shared_prompt_state.value}")

    def generate_single_prompt(template, genre, use_llm):
        base_prompt = generate_prompts(template, genre=genre, batch_size=1)[0]
        final_prompt = enhance_prompt_with_llm(base_prompt, genre) if use_llm else base_prompt
        print(f"[PROMPT LAB] Rerolled prompt: {final_prompt}")
        
        if shared_prompt_state is not None:
            print(f"[DEBUG] Updating shared state from {shared_prompt_state.value} to {final_prompt}")
            shared_prompt_state.value = final_prompt
            print(f"[DEBUG] After update, shared state is now: {shared_prompt_state.value}")
        else:
            print("[DEBUG] WARNING: shared_prompt_state is None, cannot update!")
            
        return final_prompt
    
    template = gr.Textbox(
        label="Prompt Template",
        value="A ^^classes^^ wearing ^^garb^^ in a ^^setting^^",
        lines=3,
        placeholder="Enter a wildcard-based prompt here..."
    )

    genre = gr.Dropdown(
        choices=["fantasy", "sci-fi", "realism", "horror", "characters", "nsfw"],
        value="fantasy",
        label="Genre"
    )

    use_llm = gr.Checkbox(label="✨ Enhance with LLM", value=False)

    output_box = gr.Textbox(label="🧠 Final Prompt", lines=6)
    reroll_btn = gr.Button("🎲 Reroll Prompt")

    reroll_btn.click(
        fn=generate_single_prompt,
        inputs=[template, genre, use_llm],
        outputs=[output_box]
    )
    # # New update: manually sync shared state AFTER generation
    # def update_state(prompt):
    #     shared_prompt_state.value = prompt
    #     return None  # you don't need to output anything

    # output_box.change(
    #     fn=update_state,
    #     inputs=[output_box],
    #     outputs=[]
    # )


    return [template, genre, output_box]