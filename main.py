import time
from agent import run_agent


def stream_response(agent_response: str):
    """Stream the agent response character by character for better UX."""
    for char in agent_response:
        print(char, end='', flush=True)
        time.sleep(0.02)
    print()  # Add newline at the end


def main():
    print("=" * 60)
    print("Welcome to the Agentic RAG Application!")
    print("=" * 60)
    print("Ask questions about your financial documents and reports.")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        # Get user input
        user_query = input("Your question: ").strip()
        
        # Check for exit commands
        if user_query.lower() in ['exit', 'quit']:
            print("\nThank you for using the RAG application. Goodbye!")
            break
        
        # Skip empty queries
        if not user_query:
            continue
        
        # Get agent response
        print("\nAgent: ", end='', flush=True)
        try:
            agent_response = run_agent(user_query)
            stream_response(agent_response)
        except Exception as e:
            print(f"\nError: {str(e)}")
        
        print()  # Add extra newline for spacing


if __name__ == "__main__":
    main()