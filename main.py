import sys
from src.agent import EmporioAgent

def main():
    agent = EmporioAgent()
    history = []

    print("=" * 60)
    print(" Empório da Música - Customer Service AI Assistant ")
    print("=" * 60)
    print("Type 'exit' or 'quit' to finish the session.\n")

    while True:
        try:
            user_input = input("Customer: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("Ending conversation session. Goodbye!")
                break

            response_text = agent.chat(user_input, history=history)
            print(f"\nAssistant: {response_text}\n")

            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response_text})

        except KeyboardInterrupt:
            print("\nSession terminated by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\nError processing request: {e}\n")

if __name__ == "__main__":
    main()