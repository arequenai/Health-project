from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Function to load the LLaMA 2 model
def load_model(model_name="meta-llama/Llama-2-7b-chat"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    return tokenizer, model

# Function to generate insights using LLaMA 2
def generate_insights(summary, tokenizer, model):
    prompt = f"Provide insights based on the following metrics:\n\n{summary}\n\nInsights:"
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(inputs.input_ids, max_length=150, num_return_sequences=1)
    insights = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return insights
