import os
import json
from flask import Flask, request, render_template
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch



# -----------------------
# Load config.json paths
# -----------------------
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "project_config.json")

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

# Convert relative paths to absolute paths
base_dir = os.path.dirname(__file__)
tokenizer_dir = os.path.abspath(os.path.join(base_dir, config["tokenizer_dir"]))
base_model_dir = os.path.abspath(os.path.join(base_dir, config["base_model_dir"]))
adapter_dir = os.path.abspath(os.path.join(base_dir, config["adapter_dir"]))

print("Tokenizer path:", tokenizer_dir)
print("Base model path:", base_model_dir)
print("Adapter path:", adapter_dir)

# -----------------------
# Load tokenizer and model
# -----------------------
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)

print("Loading base model...")
model = AutoModelForCausalLM.from_pretrained(
    base_model_dir,
    torch_dtype=torch.float32,
    device_map=None              
)

# -----------------------
# Load LoRA adapter
# -----------------------
from peft import PeftModel
print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(model, adapter_dir)

model.eval()

# -----------------------
# Flask app
# -----------------------
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    response_text = ""
    user_input = ""
    if request.method == "POST":
        user_input = request.form.get("user_input")
        if user_input:
            # Wrap input in instruction-style prompt
            prompt = f"### Instruction:\n{user_input}\n### Response:"
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            #inputs = tokenizer(user_input, return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=200
                )
            full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
            #try:
              #full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
            #except Exception as e:
              #full_output = f"[Error decoding output: {e}]"
            print("MODEL OUTPUT:", repr(full_output))

            #print("FULL MODEL OUTPUT:", repr(full_output))
            if full_output.startswith(prompt):
                response_text = full_output[len(prompt):].strip()
            else:
                response_text = full_output.strip()
            # Remove the original prompt from the output so only the answer shows
            #if full_output.startswith(user_input):
               #response_text = full_output[len(user_input):].strip()
            #else:
              #response_text = full_output.strip()
           # response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    #return render_template("index.html", response=response_text)
    return render_template("index.html", user_input=user_input, response=response_text)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
