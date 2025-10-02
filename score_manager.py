import os

SCORES_FILE = "scores.txt"


def update_score(username, new_score):
    scores = []

    # Load existing scores
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r") as f:
            for line in f:
                name, sc = line.strip().split()
                scores.append((name, int(sc)))

    # Replace or append the user's score
    updated = False
    for i, (name, sc) in enumerate(scores):
        if name == username:
            if new_score > sc:
                scores[i] = (username, new_score)  # Replace only if it's a better score
            updated = True
            break

    if not updated:
        scores.append((username, new_score))


    # Write back to file
    with open(SCORES_FILE, "w") as f:
        for name, sc in scores:
            f.write(f"{name} {sc}\n")