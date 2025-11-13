"""
Brain Module - Conversational Logic & Response Generation
Encapsulated for easy upgrade to LLM (GPT4All, etc.)
"""

from PyQt5.QtCore import QObject, pyqtSignal
import random
from pathlib import Path


class Brain(QObject):
    response_generated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.conversation_history = []
        self.gpt4all_available = self._check_gpt4all()
        
        if self.gpt4all_available:
            try:
                from gpt4all import GPT4All
                model_path = Path(__file__).parent / "models" / "mistral-7b-openorca.Q4_0.gguf"
                print(f"[JARVIS] Loading GPT4All model from {model_path}...")
                self.model = GPT4All(str(model_path))
                print("[JARVIS] GPT4All model loaded")
            except Exception as e:
                print(f"[WARNING] GPT4All loading failed: {e}")
                self.gpt4all_available = False
    
    def _check_gpt4all(self):
        try:
            import gpt4all
            return True
        except ImportError:
            return False
    
    def process_input(self, text):
        """Process user input and generate response"""
        self.conversation_history.append({"user": text})
        
        if self.gpt4all_available:
            response = self._generate_with_gpt4all(text)
        else:
            response = self._generate_rule_based(text)
        
        self.conversation_history.append({"assistant": response})
        return response
    
    def _generate_with_gpt4all(self, text):
        """Generate response using GPT4All"""
        try:
            prompt = f"""You are Jarvis, an AI assistant inspired by Iron Man's JARVIS. 
You are sophisticated, helpful, and formal. Keep responses to 1-2 sentences.
User: {text}
Jarvis:"""
            
            response = self.model.generate(
                prompt=prompt,
                max_tokens=100,
                temp=0.7
            )
            return response.strip()
        except Exception as e:
            print(f"[ERROR] GPT4All generation failed: {e}")
            return self._generate_rule_based(text)
    
    def _generate_rule_based(self, text):
        """Fallback: Generate rule-based responses"""
        text_lower = text.lower()
        
        # Greetings
        if any(word in text_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return random.choice([
                "Good day, sir. How may I be of service?",
                "Hello, sir. I am at your disposal.",
                "Greetings, sir. What can I do for you?"
            ])
        
        # Acknowledgments
        if any(word in text_lower for word in ['thanks', 'thank you', 'appreciate']):
            return random.choice([
                "You are most welcome, sir.",
                "It is my pleasure to assist, sir.",
                "Always happy to help, sir."
            ])
        
        # Questions about capabilities
        if any(word in text_lower for word in ['what can you', 'can you', 'what do you']):
            return "I can assist with system tasks, information retrieval, and command execution, sir."
        
        # Fallback
        return random.choice([
            "Very good, sir. I shall attend to that.",
            "Right away, sir.",
            "Certainly, sir.",
            "As you wish, sir.",
            "I am at your service, sir."
        ])
