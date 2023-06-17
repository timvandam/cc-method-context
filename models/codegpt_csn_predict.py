from CodeGPT import create_predict_fn
import os

# relative path
csn_checkpoint_dir = os.path.join(os.path.dirname(__file__), "codegpt-csn-checkpoint")

if not os.path.exists(csn_checkpoint_dir):
    raise Exception(f"CodeGPT checkpoint directory {csn_checkpoint_dir} does not exist. This directory should contain the CodeGPT checkpoint files trained on CSN.")

codegpt_csn = {
    "name": "CodeGPT-CSN",
    "generate": create_predict_fn(csn_checkpoint_dir),
}
