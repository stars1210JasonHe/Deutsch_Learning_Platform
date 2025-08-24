#!/usr/bin/env python3
"""
Model Selector Utility

This script helps you easily switch between different AI models for different features.
You can set different models for chat, word analysis, translation, and exam generation.

Usage:
    python tools/model_selector.py --feature chat --model gpt-4o
    python tools/model_selector.py --list-models
    python tools/model_selector.py --show-current
"""

import argparse
import os
from pathlib import Path

# Popular model options
AVAILABLE_MODELS = {
    "OpenAI": [
        "gpt-4o",
        "gpt-4o-mini", 
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ],
    "Anthropic (via OpenRouter)": [
        "anthropic/claude-3-5-sonnet-20241022",
        "anthropic/claude-3-sonnet-20240229",
        "anthropic/claude-3-opus-20240229",
        "anthropic/claude-3-haiku-20240307"
    ],
    "Other (via OpenRouter)": [
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.2-90b-vision-instruct",
        "google/gemini-pro-1.5",
        "mistralai/mistral-large"
    ]
}

FEATURES = {
    "chat": "OPENAI_CHAT_MODEL",
    "analysis": "OPENAI_ANALYSIS_MODEL", 
    "translation": "OPENAI_TRANSLATION_MODEL",
    "exam": "OPENAI_EXAM_MODEL",
    "default": "OPENAI_MODEL"
}

def get_env_file_path():
    """Get the path to the .env file"""
    project_root = Path(__file__).parent.parent
    return project_root / ".env"

def read_env_file():
    """Read current environment variables from .env file"""
    env_file = get_env_file_path()
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def write_env_file(env_vars):
    """Write environment variables back to .env file"""
    env_file = get_env_file_path()
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# Vibe Deutsch Configuration\n")
        f.write("# OpenAI Configuration\n")
        f.write(f"OPENAI_API_KEY={env_vars.get('OPENAI_API_KEY', 'your_api_key_here')}\n")
        f.write(f"OPENAI_BASE_URL={env_vars.get('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')}\n")
        f.write(f"OPENAI_MODEL={env_vars.get('OPENAI_MODEL', 'gpt-4o-mini')}\n")
        
        # Feature-specific models
        if env_vars.get('OPENAI_CHAT_MODEL'):
            f.write(f"OPENAI_CHAT_MODEL={env_vars['OPENAI_CHAT_MODEL']}\n")
        if env_vars.get('OPENAI_ANALYSIS_MODEL'):
            f.write(f"OPENAI_ANALYSIS_MODEL={env_vars['OPENAI_ANALYSIS_MODEL']}\n")
        if env_vars.get('OPENAI_TRANSLATION_MODEL'):
            f.write(f"OPENAI_TRANSLATION_MODEL={env_vars['OPENAI_TRANSLATION_MODEL']}\n")
        if env_vars.get('OPENAI_EXAM_MODEL'):
            f.write(f"OPENAI_EXAM_MODEL={env_vars['OPENAI_EXAM_MODEL']}\n")
        
        f.write(f"\n# Database\n")
        f.write(f"DATABASE_URL={env_vars.get('DATABASE_URL', 'sqlite:///./data/app.db')}\n")
        f.write(f"\n# Security\n")
        f.write(f"SECRET_KEY={env_vars.get('SECRET_KEY', 'your_32_character_secret_key')}\n")

def list_models():
    """List all available models"""
    print("🤖 Available Models:\n")
    
    for provider, models in AVAILABLE_MODELS.items():
        print(f"📋 {provider}:")
        for model in models:
            print(f"  • {model}")
        print()
    
    print("💡 Recommendations:")
    print("  • For chat: gpt-4o or claude-3-5-sonnet (more conversational)")  
    print("  • For analysis: gpt-4o-mini (fast and accurate for structured tasks)")
    print("  • For complex tasks: gpt-4o or claude-3-opus (most capable)")
    print()

def show_current():
    """Show current model configuration"""
    env_vars = read_env_file()
    
    print("🔧 Current Model Configuration:\n")
    print(f"Default Model:    {env_vars.get('OPENAI_MODEL', 'gpt-4o-mini')}")
    print(f"Base URL:         {env_vars.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')}")
    print()
    print("Feature-specific models:")
    print(f"  Chat:           {env_vars.get('OPENAI_CHAT_MODEL', '(using default)')}")
    print(f"  Word Analysis:  {env_vars.get('OPENAI_ANALYSIS_MODEL', '(using default)')}")
    print(f"  Translation:    {env_vars.get('OPENAI_TRANSLATION_MODEL', '(using default)')}")
    print(f"  Exam Generation:{env_vars.get('OPENAI_EXAM_MODEL', '(using default)')}")
    print()

def set_model(feature, model):
    """Set model for a specific feature"""
    if feature not in FEATURES:
        print(f"❌ Invalid feature: {feature}")
        print(f"Available features: {list(FEATURES.keys())}")
        return
    
    env_vars = read_env_file()
    env_key = FEATURES[feature]
    
    # Validate model exists in our list
    all_models = []
    for models_list in AVAILABLE_MODELS.values():
        all_models.extend(models_list)
    
    if model not in all_models and not model.startswith('gpt-') and not model.startswith('claude-'):
        print(f"⚠️  Warning: '{model}' is not in our recommended list.")
        confirm = input("Continue anyway? (y/N): ")
        if confirm.lower() != 'y':
            return
    
    env_vars[env_key] = model
    write_env_file(env_vars)
    
    print(f"✅ Set {feature} model to: {model}")
    print("🔄 Restart the server to apply changes")

def recommend_models():
    """Recommend models based on use case"""
    print("🎯 Model Recommendations:\n")
    
    recommendations = {
        "💬 Chat (Conversational)": [
            "anthropic/claude-3-5-sonnet-20241022",  # Most conversational
            "gpt-4o",  # Great balance
            "anthropic/claude-3-sonnet-20240229"  # Good quality
        ],
        "🔍 Word Analysis (Structured)": [
            "gpt-4o-mini",  # Fast and accurate
            "gpt-4o",  # More thorough
            "anthropic/claude-3-haiku-20240307"  # Very fast
        ],
        "🌐 Translation (Nuanced)": [
            "gpt-4o",  # Best for context
            "anthropic/claude-3-sonnet-20240229",  # Great cultural understanding
            "gpt-4-turbo"  # Good alternative
        ],
        "📝 Exam Generation (Creative)": [
            "gpt-4o",  # Most creative
            "anthropic/claude-3-opus-20240229",  # Highest quality
            "gpt-4-turbo"  # Good balance
        ]
    }
    
    for use_case, models in recommendations.items():
        print(f"{use_case}:")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Change AI models for different features")
    parser.add_argument("--feature", choices=list(FEATURES.keys()), help="Feature to configure")
    parser.add_argument("--model", help="Model to use")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--show-current", action="store_true", help="Show current configuration")
    parser.add_argument("--recommend", action="store_true", help="Show model recommendations")
    
    args = parser.parse_args()
    
    if args.list_models:
        list_models()
    elif args.show_current:
        show_current()
    elif args.recommend:
        recommend_models()
    elif args.feature and args.model:
        set_model(args.feature, args.model)
    else:
        parser.print_help()
        print("\n🚀 Quick Examples:")
        print("  python tools/model_selector.py --show-current")
        print("  python tools/model_selector.py --list-models")
        print("  python tools/model_selector.py --recommend")
        print("  python tools/model_selector.py --feature chat --model gpt-4o")
        print("  python tools/model_selector.py --feature analysis --model anthropic/claude-3-sonnet-20240229")

if __name__ == "__main__":
    main()