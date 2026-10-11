from .llm import ask_llm

print(ask_llm("Say OK in one word"))
print(ask_llm("What is photosynthesis? One sentence.", system="You are a concise tutor."))