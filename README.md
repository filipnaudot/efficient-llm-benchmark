<div align='center'>
    <picture>
        <source media="(prefers-color-scheme: light)" srcset="/readme_assets/lightbench_logo_minimalistic.jpg">
        <img alt="lighbench logo" src="/readme_assets/lightbench_logo_minimalistic.jpg" width="50%" height="50%">
    </picture>
    <p>
        <img src="https://img.shields.io/badge/Ubuntu-20.04-orange">
        <img src="https://img.shields.io/badge/python->=3.11.3-blue">
        <br>
        <img src="https://img.shields.io/badge/-HuggingFace-FDEE21?style=for-the-badge&logo=HuggingFace&logoColor=black">
        <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white">
    </p>
</div>


# LLM Benchmark Framework

## Chat example
Example of a chat using [Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct), running on a GTX 1080 TI.

![Demo of Terminal Chat Interface](./readme_assets/demo.gif)

## Getting Started
1. Download the appropriate PyTorch version for your system using the **[Start Locally](https://pytorch.org/get-started/locally/)** guide.

2. Install the required dependencies by running the following commands:

```bash
pip3 install transformers
```

```bash
pip3 install python-dotenv
```

```bash
pip3 install bitsandbytes
```

```bash
pip3 install 'accelerate>=0.26.0'
```

## Paper
***Efficient LLMs: A Study in Resource Reduction***