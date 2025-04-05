import requests
import base64
import os
import json
from datetime import datetime
import streamlit as st
import time


FORGE_API = "http://127.0.0.1:7860/queue/join"
FN_INDEX = 465
SESSION_HASH = "uuhnqx1qqor"  # scrape from UI dynamically later



def build_forge_payload(prompt, config):
    return {
        "data": [
            # 0–16
            "",  # 0: task ID (set dynamically if needed)
            prompt,  # 1
            "",  # 2: negative prompt
            [],  # 3: styles
            1,  # 4: batch size
            1,  # 5: n_iter
            1,  # 6: face restore
            config.get("cfg_scale", 4.2),  # 7: Base Distilled CFG
            config.get("height", 1216),  # 8
            config.get("width", 832),  # 9
            config.get("hires_fix", True),  # 10
            config.get("denoising_strength", 0.45),  # 11
            config.get("hr_scale", 1.43),  # 12
            config.get("upscaler", "4x-AnimeSharp"),  # 13
            config.get("hires_steps", 4),  # 14: Hi-res steps
            0,  # 15
            0,  # 16

            # 17–26
            "Use same checkpoint",  # 17
            ["Use same choices"],  # 18
            "Use same sampler",  # 19 (hires sampler)
            "Use same scheduler",  # 20 (hires scheduler)
            "",  # 21
            "",  # 22
            1,  # 23
            config.get("hr_cfg_scale", 3.5),  # 24: Hi-res Distilled CFG
            None,  # 25
            "None",  # 26

            # 27–33
            int(config.get("steps", 10)),  # 27: Base steps
            config.get("sampler", "Euler"),  # 28: Main sampler
            config.get("scheduler", "Beta"),  # 29: Main scheduler
            False,  # 30
            "",  # 31
            0.8,  # 32
            -1,  # 33: Seed

            # 34–44
            False, -1, 0, 0, 0,
            False, False, None, None, None, None,

            # 45–62
            True, False, 1, False, False, False,
            1.1, 1.5, 100, 0.7,
            False, False, True, False, False, 0,
            "Gustavosta/MagicPrompt-Stable-Diffusion", "",

            # 63–65: Three JSON blobs (ControlNet etc.)
            config.get("controlnet", {}),  # 63
            config.get("controlnet_extra_1", {}),  # 64
            config.get("controlnet_extra_2", {}),  # 65

            # 66–160
            False, 7, 1, "Constant", 0, "Constant", 0,
            1, "enable", "MEAN", "AD", 1,
            False, 1.01, 1.02, 0.99, 0.95, 0, 1, False,
            0.5, 2, 1, False, 3, 0, 0, 1,
            False, 3, 2, 0, 0.35, True,
            "bicubic", "bicubic", False, 0,
            "anisotropic", 0, "reinhard", 100, 0,
            "subtract", 0, 0, "gaussian", "add", 0,
            100, 127, 0, "hard_clamp", 5, 0,
            "None", "None", False, "MultiDiffusion",
            768, 768, 64, 4, False, 1, False, False, False, False,
            "positive", "comma", 0, False, False, "start", "", False,
            "Seed", "", "", "Nothing", "", "", "Nothing", "", "",
            True, False, False, False, False, False, False, 0, False
        ],
          "fn_index": 465,
        "session_hash": "uuhnqx1qqor"
    }



def send_jobs(jobs, output_dir, ui_config, on_job_progress=None, on_batch_progress=None):
    os.makedirs(output_dir, exist_ok=True)

    for idx, job in enumerate(jobs):
        # Respect pause toggle
        while st.session_state.get("batch_paused", False):
            time.sleep(0.5)

        prompt = job.get("prompt", "")
        # Clean config: merge only allowed fields
        allowed_fields = ["sampler", "scheduler", "width", "height", "hires_fix", "denoising_strength", "hr_scale", "upscaler", "sampler", "cfg_scale", "hr_cfg_scale", "steps", "hires_steps"]
        config = {key: ui_config.get(key) for key in allowed_fields}

        payload = job.get("payload")

        # Fallback if only prompt exists (older batches)
        if not payload:
            prompt = job.get("prompt", "")
            payload = build_forge_payload(prompt, ui_config)

        # Update batch progress
        if on_batch_progress:
            on_batch_progress(idx, len(jobs))

        try:
            res = requests.post(FORGE_API, json=payload)
            res.raise_for_status()
            data = res.json()

            # ⬇️ Capture the event_id from the Forge response
            event_id = data.get("event_id")
            if event_id:
                st.session_state["last_event_id"] = event_id
                
            # Track real Forge progress
            if on_job_progress:
                progress_url = "http://127.0.0.1:7860/internal/progress"
                for _ in range(60):  # ~30 seconds
                    try:
                        res = requests.post(progress_url, json={"id": 1})
                        if res.ok:
                            prog_data = res.json()
                            pct = int(prog_data.get("progress", 0) * 100)
                            eta = prog_data.get("eta", 0)
                            on_job_progress(pct, f"🧠 Generating... {pct}% ({eta:.1f}s)")
                    except Exception:
                        pass
                    time.sleep(0.5)

            if "data" in data or "images" in data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img_data = data.get("images", [None])[0]

                if img_data:
                    img_bytes = base64.b64decode(img_data.split(",", 1)[-1])
                    file_name = f"job_{idx + 1:02}.png"

                    with open(os.path.join(output_dir, file_name), "wb") as f:
                        f.write(img_bytes)

                    st.success(f"✅ Job {idx+1} complete → `{file_name}`")
                else:
                    st.warning(f"⚠️ No image returned for job {idx + 1}")

        except Exception as e:
            st.error(f"❌ Error during job {idx + 1}: {e}")

