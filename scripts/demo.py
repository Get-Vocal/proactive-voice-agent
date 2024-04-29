"""Demo file to test different scenarios.

Run with:
```
poetry run python -m scripts.demo
```
"""

from app.llm import LlmClient
from app.schema import CustomLlmRequest

llm_client = LlmClient()
first_event = llm_client.greetings()


def complete_scenario(name, scenario):
    it_scenario = iter(scenario)
    transcript = []
    print(f"\n[BEGIN] scenario: {name}")
    try:
        while True:
            message = next(it_scenario)
            print(f"Message: {message}")
            transcript.append({"role": "user", "content": message})
            request = CustomLlmRequest(interaction_type="response_required", transcript=transcript)

            response = ""
            for event in llm_client.stream_response(request):
                response += event.content
            print(f"Response: {response}")
            transcript.append({"role": "agent", "content": response})
    except StopIteration:
        print(f"[END] scenario: {name}\n")
    except Exception as e:
        print(f"[Error]: {e}")


scenarios = {
    "final_demo": [
        "Hello, I need to book an appointment",
        "I am having teeth pain",
        "I'm mister Smith",
        "Monday at 10am",
        "Okay, then on Monday at 3pm",
        "Yes please",
        "Perfect, what is the nearest metro sataion?",
        "By the way, could you ask my dentist if I can take a painkiller ?",
    ],
    "ask_doctor_demo": [
        "Hello, I have a high teeth pain. Please ask a dentist what I should do.",
    ],
    "basic_scenario": [
        "Hello, I need to book an appointment",
        "On Monday at 3pm",
        "Okay, then on Tuesday at 4pm",
        "Great, thanks",
        "Okay, bye",
    ],
    "information_scenario": [
        "Hello, what is the nearest metro sataion to the clinic?",
    ],
}

for name, scenario in scenarios.items():
    complete_scenario(name, scenario)
