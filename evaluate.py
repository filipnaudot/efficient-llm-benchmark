import os
import time
import json

from dotenv import load_dotenv
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

from code_evaluator import CodeEvaluator




def create_prompts(json_list, system_command):
    prompts = []
    for json_str in json_list:
        result = json.loads(json_str)
        promt = (
            [
                system_command,
                {
                    "role": "user",
                    "content": result["text"] + f' The function should pass the following test: {result["test_list"][0]}.',
                }
            ], result["test_list"][1]
        )
        prompts.append(promt)
    
    return prompts


def main(stream: bool = False, QUANTIZE: bool = False):

    load_dotenv()
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    # tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
    # device = "cuda" if torch.cuda.is_available() else "cpu"
    models = ["meta-llama/Llama-3.2-3B-Instruct", "meta-llama/Llama-3.1-8B-Instruct"]


    start_test_line = 11
    end_test_line = 510
    with open('./data/mbpp/mbpp.jsonl', 'r') as json_file:
        json_list = list(json_file)[start_test_line-1:end_test_line]

    system_command = {
        "role": "system",
        "content": "You are a Python programming assistant. Your task is to write Python functions according to the user's prompt. Respond only with the necessary Python code, including python package imports if needed. Do not provide example usage, only the python function.",
    }
    
    prompts = create_prompts(json_list, system_command)
    
    models = [("meta-llama/Llama-3.2-3B-Instruct", False), ("meta-llama/Llama-3.2-3B-Instruct", True), ("meta-llama/Llama-3.1-8B-Instruct", True)]
    for model, quantize in models:
        print(f"\n---- {'quantized' if quantize else 'unmodified'} {model} ----\n")
        code_evaluator = CodeEvaluator(model, hf_token, quantize=quantize, few_shot=False, verbose=False)
        code_evaluator.run(prompts)

        code_evaluator.print_summary()


if __name__ == "__main__":
    main(stream=True, QUANTIZE=False)
