import os
import time
from queue import Queue
import threading
import signal

import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TextIteratorStreamer

from utils import Printer

class CodeEvaluator:
    def __init__(self, model_id, hf_token, quantize=False):
        self.quantize = quantize
        self.model = model_id
        self.hf_token = hf_token

        self.num_test = 0
        self.passed_test = 0

        self.tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True)
        self.queue = Queue()

        if self.quantize:
            self.model = self.load_quantized_model()

        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            pad_token_id=self.tokenizer.eos_token_id,
            token=self.hf_token,
        )


    def load_quantized_model(self):
        print("Loading quantized model...")
        bnb_config = BitsAndBytesConfig(load_in_4bit=True)

        model = AutoModelForCausalLM.from_pretrained(
            self.model,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )

        return model


    def clear_last_row(self):
        print(f"\r{' ' * 40}\r", end='', flush=True) # Clear last line
        
    def print_test_time(self, index, inference_time, ttft):
        self.clear_last_row()
        print(f"\r{index+1} ({inference_time:.2f}s TTFT: {ttft:.2f}s) ", end='', flush=True)

    def print_test_status(self):
        self.clear_last_row()
        percentage = 0
        if self.num_test > 0: percentage = (self.passed_test / self.num_test) * 100
        Printer.print_cyan(f"\rTests Passed: {self.passed_test}/{self.num_test} ({percentage:.2f}%)", end='', flush=True)


    def handle_stream_output(self, streamer, queue, start_time, ttft_list, verbose=False):
        first_token = True
        for token in streamer:
            if first_token:
                ttft = time.time() - start_time
                ttft_list.append(ttft)
                first_token = False
            
            if verbose:
                print(f"{token}", end='', flush=True)
            queue.put(token)


    def preprocess_data(self, data):
        if f"```python" in data:
            data = data[data.find(f"```python") + len(f"```python"):]
            data = data[:data.find("```")]
        return data


    def timeout_handler(self, signum, frame):
        raise TimeoutError("Execution timed out!")


    def validate_code(self, code, test, shots):
        indent_format = f"\033[{30}G" if shots > 0 else f"\033[{25}G"

        full_code_to_execute = f"{code}\n\n{test}"
        Printer.print_yellow(f"{indent_format}{shots} ", end='', flush=True)
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(10)
        try:
            exec(full_code_to_execute, globals())
        except AssertionError:
            Printer.print_red(f"FAILED: ", end='')
            print(f"test {str(test)} FAILED")
            return 0, f"There is a logical error in the code. TEST: {str(test)} FAILED"
        except Exception as error:
            Printer.print_red(f"FAILED: ", end='')
            print(f"An error occurred: {error}")
            return 0, f"ERROR: {error}"
        except TimeoutError as error:
            Printer.print_red(f"FAILED: ", end='')
            print(f"{error}")
            return 0, f"FAILED: {error}"
        finally:
            signal.alarm(0)
        
        Printer.print_green(f"PASSED")
        return 1, "PASSED"


    def run(self, prompts, few_shot=False):

        for index, (prompt, test) in enumerate(prompts):
            response, inference_time, ttft = self.generate_response(prompt)

            self.print_test_time(index, inference_time, ttft)

            extracted_code = self.preprocess_data(response).strip()
            passed, message = self.validate_code(extracted_code, test, 0)

            if few_shot and not passed:
                shots = 1
                few_shot_prompt = [
                    *prompt,  # Unpacking the list
                    {
                        "role": "assistant",
                        "content": response
                    },
                    {
                        "role": "user",
                        "content": f' While running that code I received the following: {message}. Can you update the code and fix the problem?',
                    }
                ]
                while not passed and shots <= 2:
                    self.print_test_status()
                   
                    response, inference_time, ttft = self.generate_response(few_shot_prompt)
                    self.print_test_time(index, inference_time, ttft)

                    extracted_code = self.preprocess_data(response).strip()
                    passed, message = self.validate_code(extracted_code, test, shots)
                    few_shot_prompt.append(
                        {
                            "role": "assistant",
                            "content": response
                        })
                    few_shot_prompt.append(
                        {
                            "role": "user",
                            "content": f' While running that code I received the following: {message}. Can you update the code and fix the problem?',
                        })
                    
                    shots += 1
            
            self.num_test += 1
            if passed: self.passed_test += 1

            self.print_test_status()


    def generate_response(self, prompt):
        ttft_list = []
        start_time = time.time()

        streaming_thread = threading.Thread(target=self.handle_stream_output, args=(self.streamer, self.queue, start_time, ttft_list))
        streaming_thread.start()

        generation = self.generator(
            prompt,
            streamer=self.streamer,
            do_sample=False,
            temperature=1.0,
            top_p=1,
            max_new_tokens=512,
        )
        end_time = time.time()

        streaming_thread.join()
        
        response = generation[0]['generated_text'][-1]['content']
        # print(f"{response}")

        return response, (end_time-start_time), ttft_list[-1]
