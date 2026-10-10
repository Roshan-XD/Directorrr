"""Fixed stock ComfyUI T2VA graph. No user nodes, paths or repository scripts."""
import re


def build_h3_workflow(prompt, seed, job_id, settings):
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 2000 or not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise ValueError("Invalid H3 prompt/job")
    if not isinstance(seed, int) or not 0 <= seed <= 9007199254740991:
        raise ValueError("Invalid seed")
    if (settings["width"], settings["height"], settings["frames"], settings["steps"]) != (960, 544, 124, 20):
        raise ValueError("Only the reviewed H3 T2VA recipe is enabled")
    return {
        "37": {"class_type": "UNETLoader", "inputs": {"unet_name": "MiniMax-H3_FL2VA-NVFP4.safetensors", "weight_dtype": "default"}},
        "38": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "39": {"class_type": "VAELoader", "inputs": {"vae_name": "MiniMax-H3_VideoVAE-FP16.safetensors"}},
        "41": {"class_type": "VAELoader", "inputs": {"vae_name": "MiniMax-H3_AudioVAE-FP32.safetensors"}},
        "6": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {"clip": ["38", 0], "vae": ["39", 0], "prompt": prompt, "width": 960, "height": 544, "length": 124}},
        "48": {"class_type": "MiniMaxH3SigmaShift", "inputs": {"model": ["37", 0], "shift_video": 12.0, "shift_audio": 3.0}},
        "50": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "51": {"class_type": "BasicGuider", "inputs": {"model": ["48", 0], "conditioning": ["6", 0]}},
        "52": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "53": {"class_type": "BasicScheduler", "inputs": {"model": ["48", 0], "scheduler": "simple", "steps": 20, "denoise": 1.0}},
        "3": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["50", 0], "guider": ["51", 0], "sampler": ["52", 0], "sigmas": ["53", 0], "latent_image": ["6", 1]}},
        "54": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["3", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["54", 0], "vae": ["39", 0]}},
        "55": {"class_type": "LTXVAudioVAEDecode", "inputs": {"samples": ["54", 1], "audio_vae": ["41", 0]}},
        "56": {"class_type": "CreateVideo", "inputs": {"images": ["8", 0], "audio": ["55", 0], "fps": 24.0}},
        "47": {"class_type": "SaveVideo", "inputs": {"video": ["56", 0], "filename_prefix": "Director_Stage8_" + job_id, "format": "mp4", "format.codec": "h264"}},
    }
