
import json
import subprocess
from datetime import date
from pathlib import Path

DATA_FILE = Path("problems.json")
README_FILE = Path("README.md")

TOPICS = [
    "Arrays", "Strings", "Hashing",
    "Searching", "Sorting", "Recursion"
]

DIFFICULTIES = ["Basic", "Easy", "Medium", "Hard"]

PLATFORMS = [
    "LeetCode", "GeeksforGeeks",
    "HackerRank", "Practice"
]


def load_problems():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_problems(problems):
    with open(DATA_FILE, "w") as file:
        json.dump(problems, file, indent=4)


def add_problem():
    problems = load_problems()

    print("\n--- Add Completed Question ---")

    title = input("Question name: ").strip()

    if not title:
        print("Question name cannot be empty.")
        return

    print("Topics:", ", ".join(TOPICS))
    topic = input("Topic: ").strip().title()

    if topic not in TOPICS:
        print("Invalid topic.")
        return

    print("Difficulty:", ", ".join(DIFFICULTIES))
    difficulty = input("Difficulty: ").strip().title()

    if difficulty not in DIFFICULTIES:
        print("Invalid difficulty.")
        return

    print("Platforms:", ", ".join(PLATFORMS))
    platform = input("Platform: ").strip()

    matching_platform = next(
        (p for p in PLATFORMS if p.lower() == platform.lower()),
        None
    )

    if matching_platform is None:
        print("Invalid platform.")
        return

    for problem in problems:
        if (
            problem["title"].lower() == title.lower()
            and problem["topic"] == topic
        ):
            print("This question is already recorded.")
            return

    problems.append({
        "title": title,
        "topic": topic,
        "difficulty": difficulty,
        "platform": matching_platform,
        "date": str(date.today())
    })

    save_problems(problems)
    update_readme(problems)

    print("\nQuestion added successfully!")
    print("GitHub README progress updated.")


def update_readme(problems):
    lines = [
        "## Progress Overview",
        "",
        "| Topic | Basic | Easy | Medium | Hard | Total |",
        "|---|---:|---:|---:|---:|---:|"
    ]

    for topic in TOPICS:
        counts = {
            difficulty: sum(
                1 for p in problems
                if p["topic"] == topic
                and p["difficulty"] == difficulty
            )
            for difficulty in DIFFICULTIES
        }

        total = sum(counts.values())

        lines.append(
            f"| {topic} | {counts['Basic']} | "
            f"{counts['Easy']} | {counts['Medium']} | "
            f"{counts['Hard']} | {total} |"
        )

    lines.extend([
        "",
        f"**Total Questions Solved: {len(problems)}**",
        ""
    ])

    if README_FILE.exists():
        readme = README_FILE.read_text(encoding="utf-8")

        start = "<!-- PROGRESS_START -->"
        end = "<!-- PROGRESS_END -->"

        if start in readme and end in readme:
            before, remaining = readme.split(start, 1)
            _, after = remaining.split(end, 1)

            readme = (
                before + start + "\n"
                + "\n".join(lines) + "\n"
                + end + after
            )
        else:
            readme += (
                "\n" + start + "\n"
                + "\n".join(lines) + "\n"
                + end + "\n"
            )

        README_FILE.write_text(readme, encoding="utf-8")


def show_progress():
    problems = load_problems()

    print("\n========== DSA PROGRESS ==========")

    for topic in TOPICS:
        count = sum(
            1 for p in problems if p["topic"] == topic
        )
        print(f"{topic}: {count} questions")

    print("----------------------------------")
    print("Total completed:", len(problems))


def sync_to_github():
    try:
        # Stage all changes
        subprocess.run(
            ["git", "add", "."],
            check=True
        )

        # Commit changes
        result = subprocess.run(
            ["git", "commit", "-m", "Update DSA progress"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            if "nothing to commit" in result.stdout.lower():
                print("No new changes to upload.")
                return

            print(result.stdout)
            print(result.stderr)
            return

        # Push to GitHub
        subprocess.run(
            ["git", "push", "origin", "main"],
            check=True
        )

        print("\nSuccessfully synced with GitHub!")

    except subprocess.CalledProcessError as error:
        print("Git synchronization failed:", error)
    except FileNotFoundError:
        print("Git is not installed or not available in PATH.")

def main():
    while True:
        print("\n===== DSA PROGRESS TRACKER =====")
        print("1. Add completed question")
        print("2. View progress")
        print("3. Exit")
        print("4. Sync with GitHub")

        choice = input("Choose option: ").strip()

        if choice == "1":
            add_problem()
        elif choice == "2":
            show_progress()
        elif choice == "3":
            print("Goodbye!")
            break
        elif choice == "4":
            sync_to_github()
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
