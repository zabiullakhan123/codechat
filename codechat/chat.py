"""Send retrieved context + question to Claude."""
import anthropic

from . import config

SYSTEM = """You are an expert engineer helping a developer understand a codebase.
Answer using ONLY the code excerpts provided. Cite sources inline as `path:start-end`.
If the excerpts don't contain the answer, say so and suggest which files or terms to look for.
Be concise; include short code snippets when they help."""


def format_context(results):
    parts = []
    for chunk, score in results:
        parts.append(
            f"<excerpt source=\"{chunk.path}:{chunk.start_line}-{chunk.end_line}\">\n"
            f"{chunk.text}\n</excerpt>"
        )
    return "\n\n".join(parts)


class ChatSession:
    def __init__(self, index):
        self.index = index
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        self.history = []  # past Q&A turns (without context, to save tokens)

    def ask(self, question, stream_to=None):
        results = self.index.search(question)
        user_msg = f"{format_context(results)}\n\nQuestion: {question}"
        messages = self.history + [{"role": "user", "content": user_msg}]

        answer = []
        with self.client.messages.stream(
            model=config.LLM_MODEL, max_tokens=config.MAX_TOKENS,
            system=SYSTEM, messages=messages,
        ) as stream:
            for text in stream.text_stream:
                answer.append(text)
                if stream_to:
                    stream_to(text)
        answer = "".join(answer)

        self.history += [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
        self.history = self.history[-8:]  # keep last 4 turns
        return answer, results
