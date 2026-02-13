import random

base_topics = [
    "dating app", "line message", "first date", "cheating", "marriage",
    "breakup", "ex-boyfriend", "office romance", "long distance", "age gap",
    "unrequited love", "jealousy", "friends with benefits", "communication",
    "trust issues", "in-laws", "money", "sex life", "self-improvement", "fashion"
]

modifiers = [
    "trouble", "advice", "success tip", "mistake", "regret",
    "secret", "psychology", "strategy", "panic", "anxiety"
]

contexts = [
    "with older man", "with younger man", "with coworker", "with friend",
    "after 3 months", "after 1 year", "before marriage", "after breakup",
    "during work", "late at night"
]

with open("ideas.txt", "r") as f:
    existing = f.readlines()

current_count = len(existing)
target = 500

new_ideas = []
while len(new_ideas) + current_count < target:
    t = random.choice(base_topics)
    m = random.choice(modifiers)
    c = random.choice(contexts)
    idea = f"{t} {m} {c}\n"
    if idea not in existing and idea not in new_ideas:
        new_ideas.append(idea)

with open("ideas.txt", "a") as f:
    f.writelines(new_ideas)

print(f"Added {len(new_ideas)} new ideas. Total: {len(new_ideas) + current_count}")
