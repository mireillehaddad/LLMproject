from src.chatbot.qa import ask


def main() -> None:
    question = "What digital initiatives are supported in Lebanon?"

    answer = ask(question)

    print()
    print("QUESTION")
    print("--------")
    print(question)

    print()
    print("ANSWER")
    print("------")
    print(answer)


if __name__ == "__main__":
    main()