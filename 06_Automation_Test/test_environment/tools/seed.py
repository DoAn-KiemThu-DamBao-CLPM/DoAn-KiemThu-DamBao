#!/usr/bin/env python3
"""Deterministic seed data for the Anyn test database (SQLite emulation of the MySQL schema).

phase 1  (before the first web request)  : users, bots, themes, ratings, comments, collections
phase 2  (after the app auto-migrations) : gallery, community posts, ideas

Usage:  seed.py <sqlite-file> <phase 1|2> <bcrypt-hash-of-seed-password> [--big]
Seed password for all fixture accounts is documented in the Test Plan (Test Data section).
"""
import random
import sqlite3
import sys

db, phase, pw_hash = sys.argv[1], sys.argv[2], sys.argv[3]
big = '--big' in sys.argv
random.seed(20261111)
con = sqlite3.connect(db)
cur = con.cursor()

THEMES = ["Fantasy", "Romance", "Sci-Fi", "Slice of Life", "Mystery", "Horror", "Comedy", "Action", "Drama", "Isekai"]
FIRST = ["Aria", "Kael", "Luna", "Ryo", "Mira", "Dante", "Sora", "Elara", "Zane", "Nova", "Hana", "Orion", "Yuki", "Vex", "Iris",
         "Kai", "Selene", "Rex", "Mei", "Thorn"]
LAST = ["the Starweaver", "of the Ashen Court", "Nightblade", "the Wanderer", "Stormcaller", "of Silverpine", "the Archivist",
        "Dawnbringer", "the Last Ronin", "Moonwhisper"]


def phase1():
    # fixture accounts: id 1 becomes admin through the app's own migration (UPDATE users SET role='admin' WHERE id = 1)
    users = [
        ("anyn_admin", "admin@anyn.test", 0),
        ("alice_qa", "alice@anyn.test", 0),
        ("bob_qa", "bob@anyn.test", 0),
        ("carol_premium", "carol@anyn.test", 25),
    ]
    for u, e, spent in users:
        cur.execute("INSERT INTO users (username,email,password_hash,total_spent) VALUES (?,?,?,?)", (u, e, pw_hash, spent))
    for t in THEMES:
        cur.execute("INSERT INTO themes (name) VALUES (?)", (t,))
    n_bots = 40 if not big else 400
    for i in range(1, n_bots + 1):
        name = f"{FIRST[i % len(FIRST)]} {LAST[(i * 3) % len(LAST)]} #{i:03d}"
        desc = f"Seed character {i}. A {random.choice(['brave', 'quiet', 'chaotic', 'gentle', 'mysterious'])} roleplay persona for QA."
        img = f"/anyn/uploads/avatars/avt_{(i % 10) + 1}.jpg"
        pinned = 1 if i in (7, 21, 33) else 0
        rating = round(random.uniform(0, 5), 2)
        cur.execute(
            "INSERT INTO bots (name,description,image_url,is_pinned,total_rating,created_at) VALUES (?,?,?,?,?,datetime('now', ?))",
            (name, desc, img, pinned, rating, f"-{n_bots - i} hours"))
        for th in random.sample(range(1, len(THEMES) + 1), random.randint(1, 3)):
            cur.execute("INSERT INTO bot_themes (bot_id, theme_id) VALUES (?,?)", (i, th))
    # ratings / comments on bot 1 and 2 (so detail pages have content)
    for bot in (1, 2):
        cur.execute("INSERT INTO ratings (user_id,bot_id,score) VALUES (2,?,5)", (bot,))
        cur.execute("INSERT INTO ratings (user_id,bot_id,score) VALUES (3,?,3)", (bot,))
        cur.execute("UPDATE bots SET total_rating = 4.0 WHERE id = ?", (bot,))
        cur.execute("INSERT INTO comments (user_id,bot_id,content) VALUES (2,?,?)", (bot, "Seed comment by alice."))
        cur.execute("INSERT INTO comments (user_id,bot_id,content) VALUES (3,?,?)", (bot, "Seed comment by bob."))
    cur.execute("INSERT INTO bot_groups (name) VALUES ('Starter Pack')")
    cur.execute("INSERT INTO bot_groups (name) VALUES ('Fantasy Realm')")
    for b in (1, 2, 3, 4):
        cur.execute("INSERT INTO bot_group_members (group_id,bot_id) VALUES (1,?)", (b,))
    for b in (5, 6):
        cur.execute("INSERT INTO bot_group_members (group_id,bot_id) VALUES (2,?)", (b,))


def phase2():
    # official gallery: 12 single images (group_id NULL) + a 3-image collection
    files = [r for r in [
        "z7858149990859_8b0bc87106d2a5cf7b56a4e9165a78ec.jpg", "z7858149994718_4f3aa62fb76c75f41fe1d8d9e225f9eb.jpg",
        "z7858154851860_df328b8396525c4dfeeb05c175833027.jpg", "z7858154854583_ea215410a84c7a2ed2d5e42b579dd8d1.jpg",
        "z7858154870126_cd5d0f00dff4827befeb333715dde6f0.jpg", "z7858154880093_406ad6e37556932a84ea1632648e6258.jpg",
        "z7861562112057_0b70c962e5ce54a4642326857f28094b.jpg", "z7861562124065_90252f533358fbbba9f505b08b19ca69.jpg",
        "z7861562125715_85f5e467559545be7cf6119c91990f5f.jpg", "z7861562138267_a7a70532b61af5cb8afeb568c9eb0662.jpg",
        "z7861562138847_61313581bf413f809be17622101c4583.jpg", "z7861562142215_8c204ff251e44bead231210032409299.jpg"]]
    cur.execute("INSERT INTO gallery_groups (title, bot_id) VALUES ('Seed collection', 1)")
    for i, f in enumerate(files, 1):
        gid = 1 if i <= 3 else None
        cur.execute("INSERT INTO gallery (title, group_id, image_url) VALUES (?,?,?)", (f"Seed art {i}", gid, f"/anyn/uploads/gallery/{f}"))
    # community posts: 2 approved by alice, 1 pending by bob, 1 rejected by bob
    img = "/anyn/uploads/avatars/avt_{}.jpg"
    rows = [(2, "Alice approved art", img.format(1), "approved"), (2, "Alice approved art 2", img.format(2), "approved"),
            (3, "Bob pending art", img.format(3), "pending"), (3, "Bob rejected art", img.format(4), "rejected")]
    for uid, title, url, st in rows:
        cur.execute("INSERT INTO community_posts (user_id,title,image_url,rating,status,reviewed_at,admin_note) VALUES (?,?,?,'sfw',?,?,?)",
                    (uid, title, url, st, None if st == "pending" else "2026-11-01 00:00:00", "Too dark" if st == "rejected" else None))
    # ideas: 1 open by alice (id 1), 1 in progress by bob (id 2)
    cur.execute("INSERT INTO ideas (user_id,title,appearance,context,upvotes,work_status) VALUES (2,'Seed idea: ice mage','Silver hair','Frozen kingdom',0,'open')")
    cur.execute("INSERT INTO ideas (user_id,title,appearance,context,upvotes,work_status) VALUES (3,'Seed idea: desert knight','Sun-scarred armor','Sand sea',3,'in_progress')")
    if big:   # volume data for the performance test
        for i in range(5000):
            cur.execute("INSERT INTO gallery (title, group_id, image_url) VALUES (?,?,?)",
                        (f"Bulk art {i}", None, f"/anyn/uploads/gallery/z7858149990859_8b0bc87106d2a5cf7b56a4e9165a78ec.jpg"))
        for i in range(2000):
            cur.execute("INSERT INTO community_posts (user_id,title,image_url,rating,status,reviewed_at) VALUES (2,?,?,'sfw','approved',datetime('now'))",
                        (f"Bulk post {i}", img.format(1 + i % 10)))
        for i in range(3000):
            cur.execute("INSERT INTO comments (user_id,bot_id,content) VALUES (?,?,?)", (2 + i % 3, 1 + i % 3, f"bulk comment {i}"))
        for i in range(500):
            cur.execute("INSERT INTO ideas (user_id,title,appearance,context,upvotes,work_status) VALUES (?,?,?,?,?, 'open')",
                        (2 + i % 3, f"Bulk idea {i}", "a", "b", i % 50))


{"1": phase1, "2": phase2}[phase]()
con.commit()
con.close()
print(f"seed phase {phase} done (big={big})")
