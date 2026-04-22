import json
import sys
from pathlib import Path


SUBPROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SUBPROJECT_DIR.parent
CONFIG_PATH = SUBPROJECT_DIR / "config" / "agora_final_ffid231_config.json"


def rewrite_stage8_names(script_text: str) -> str:
    replacements = {
        'CONFIG_PATH = Path("./agora_final_ffid231_config.json")': 'CONFIG_PATH = CONFIG_PATH',
    }
    for old, new in replacements.items():
        script_text = script_text.replace(old, new)
    return script_text


def load_root_pipeline_source() -> str:
    pipeline_path = REPO_ROOT / "agora_final_ffid231_pipeline.py"
    return pipeline_path.read_text(encoding="utf-8")


def resolve_config_paths(cfg, base_dir: Path):
    def resolve_rel(path_str: str) -> str:
        return str((base_dir / path_str).resolve())

    for key in ["segy_path", "twt_path", "sps_path", "rps_path", "xps_path", "output_dir"]:
        cfg["input"][key] = resolve_rel(cfg["input"][key])
    return cfg


def main():
    sys.path.insert(0, str(REPO_ROOT))

    pipeline_source = rewrite_stage8_names(load_root_pipeline_source())
    namespace = {
        "__name__": "__subproject_runner__",
        "CONFIG_PATH": CONFIG_PATH,
    }
    exec(compile(pipeline_source, str(REPO_ROOT / "agora_final_ffid231_pipeline.py"), "exec"), namespace)

    load_config = namespace["load_config"]
    stage_1_input_gather_grouping = namespace["stage_1_input_gather_grouping"]
    stage_2_geometry_header_qc = namespace["stage_2_geometry_header_qc"]
    stage_3_preclean = namespace["stage_3_preclean"]
    stage_4_first_break_protection = namespace["stage_4_first_break_protection"]
    stage_5_bandlimit_resample = namespace["stage_5_bandlimit_resample"]
    stage_6_agora_characterization = namespace["stage_6_agora_characterization"]
    stage_7_fx_modeling_backscatter_cleanup = namespace["stage_7_fx_modeling_backscatter_cleanup"]
    stage_8_qc_and_tuning = namespace["stage_8_qc_and_tuning"]

    cfg = load_config(CONFIG_PATH)
    cfg = resolve_config_paths(cfg, SUBPROJECT_DIR)

    output_dir = Path(cfg["input"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    state = stage_1_input_gather_grouping(cfg)
    state = stage_2_geometry_header_qc(cfg, state)
    state = stage_3_preclean(cfg, state)
    state = stage_4_first_break_protection(cfg, state)
    state = stage_5_bandlimit_resample(cfg, state)
    state = stage_6_agora_characterization(cfg, state)
    state = stage_7_fx_modeling_backscatter_cleanup(cfg, state)
    summary = stage_8_qc_and_tuning(cfg, state, str(output_dir))

    print("Subproject AGORA final workflow complete")
    print("Config path          :", CONFIG_PATH)
    print("Output directory     :", output_dir)
    print("Removed energy ratio :", summary["output_metrics"]["removed_energy_ratio"])


if __name__ == "__main__":
    main()
