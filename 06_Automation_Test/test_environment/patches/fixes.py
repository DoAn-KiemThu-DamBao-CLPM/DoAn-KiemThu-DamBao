#!/usr/bin/env python3
"""Fixes for the defects found in cycle 1 (one entry per BUG id).  Used to build the 'fixed' System Under Test for the
regression cycle and to export one unified diff per bug.

  python3 fixes.py apply <pristine_anyn_dir> <dst_dir> [BUG-001,BUG-003,...]   -> copy + apply (all fixes by default)
  python3 fixes.py diffs <pristine_anyn_dir> <out_dir>                           -> one .patch per bug

Every replacement must match EXACTLY ONE place of the pristine source (checked) so the patches are reproducible.
Deferred (not fixed in this cycle):  BUG-013 (Unicode look-alikes in the theme filter — needs a product decision / allow-list)
                                     BUG-019 (pagination of galleries / comments — larger UI change).
"""
import os
import shutil
import subprocess
import sys

R = "\x00"  # placeholder, never used

FIXES = {
    "BUG-001": ("reset-link-exposure", [
        ("config/database.php",
         "    define('APP_ENV', 'development');",
         "    // Safe default: reset links are only shown on screen when the developer explicitly opts in (ANYN_ENV=development).\n"
         "    define('APP_ENV', getenv('ANYN_ENV') ?: 'production');"),
    ]),
    "BUG-002": ("login-lockout-abuse", [
        ("includes/auth.php",
         "const LOGIN_MAX_PER_IP    = 20;",
         "const LOGIN_MAX_PER_IP    = 20;\nconst LOGIN_MAX_PER_EMAIL_GLOBAL = 50;   // distributed guessing against ONE account (all IPs together)"),
        ("includes/auth.php",
         "    $r = $st->fetch();\n    // Count per-email across all IPs too (distributed guessing)\n",
         "    $r = $st->fetch();\n"
         "    // 5 failures from the SAME address for the SAME e-mail lock that pair only: another person can no longer lock the victim out.\n"
         "    if ((int)($r['by_email'] ?? 0) >= LOGIN_MAX_PER_EMAIL || (int)($r['by_ip'] ?? 0) >= LOGIN_MAX_PER_IP) {\n"
         "        return true;\n    }\n"),
        ("includes/auth.php",
         "    return (int)$st2->fetchColumn() >= LOGIN_MAX_PER_EMAIL\n        || (int)($r['by_ip'] ?? 0) >= LOGIN_MAX_PER_IP;",
         "    return (int)$st2->fetchColumn() >= LOGIN_MAX_PER_EMAIL_GLOBAL;"),
    ]),
    "BUG-003": ("bot-detail-soft-404", [
        ("pages/bot_detail.php",
         "if (!$bot) {\n    require_once '../includes/header.php';",
         "if (!$bot) {\n    http_response_code(404);\n    require_once '../includes/header.php';"),
    ]),
    "BUG-004": ("rating-validation", [
        ("pages/bot_detail.php",
         "    $score   = max(1, min(5, (int)$_POST['score']));\n",
         "    $score_raw = trim((string)($_POST['score'] ?? ''));\n"
         "    if (filter_var($score_raw, FILTER_VALIDATE_INT) === false) {   // missing / non-numeric input is rejected (was silently saved as 1 star)\n"
         "        header('Location: bot_detail.php?id=' . $bot_id);\n        exit;\n    }\n"
         "    $score   = max(1, min(5, (int)$score_raw));                    // numeric out-of-range values keep the designed clamping to 1..5\n"),
    ]),
    "BUG-005": ("unlisted-link-scheme", [
        ("pages/ideas.php",
         "            $link = trim($_POST['unlisted_link'] ?? '');\n            if ($link === '') {",
         "            $link = safe_http_url(trim($_POST['unlisted_link'] ?? '')) ?? '';   // only http(s) links are accepted\n            if ($link === '') {"),
    ]),
    "BUG-006": ("zero-amount-commission", [
        ("pages/commission.php",
         "            if ($amount < 5) {\n                $is_private = 1;\n            }\n",
         "            if ($amount < 5) {\n                $is_private = 1;\n            }\n"
         "            if ($amount <= 0) {\n                $error_msg = 'Please enter an amount greater than 0, or pay with a voucher.';\n            }\n"),
    ]),
    "BUG-007": ("voucher-consumed-before-validation", [
        ("includes/gems_lib.php",
         "function getMonthlyCommissionCount(PDO $pdo, string $commissionType): int",
         "function hasInventoryCoupon(PDO $pdo, int $userId, string $itemType): bool\n{\n"
         "    $s = $pdo->prepare('SELECT COUNT(*) FROM user_inventory WHERE user_id = ? AND item_type = ? AND used_at IS NULL');\n"
         "    $s->execute([$userId, $itemType]);\n    return (int)$s->fetchColumn() > 0;\n}\n\n"
         "function getMonthlyCommissionCount(PDO $pdo, string $commissionType): int"),
        ("pages/commission.php",
         "            if (!consumeInventoryCoupon($pdo, $user_id, 'commission_publish')) {",
         "            if (!hasInventoryCoupon($pdo, $user_id, 'commission_publish')) {"),
        ("pages/commission.php",
         "                $is_private = 0;\n                $amount = 5;\n                $used_voucher = true;",
         "                $is_private = 0;\n                $amount = 5;\n                $used_voucher = true;\n                $voucher_type = 'commission_publish';"),
        ("pages/commission.php",
         "            if (!consumeInventoryCoupon($pdo, $user_id, 'commission_unlisted')) {",
         "            if (!hasInventoryCoupon($pdo, $user_id, 'commission_unlisted')) {"),
        ("pages/commission.php",
         "                $is_private = 1;\n                $amount = 5;\n                $used_voucher = true;",
         "                $is_private = 1;\n                $amount = 5;\n                $used_voucher = true;\n                $voucher_type = 'commission_unlisted';"),
        ("pages/commission.php",
         "        if ($error_msg == '') {\n            $admin_note = $used_voucher",
         "        // the voucher is spent only when every other validation has passed\n"
         "        if ($error_msg == '' && $used_voucher && !consumeInventoryCoupon($pdo, $user_id, $voucher_type)) {\n"
         "            $error_msg = 'This voucher is no longer available.';\n        }\n\n"
         "        if ($error_msg == '') {\n            $admin_note = $used_voucher"),
    ]),
    "BUG-008": ("equip-key-undefined", [
        ("pages/shop.php",
         "$_POST['equip_type'], $_POST['equip_key'] ?: null);",
         "$_POST['equip_type'], ($_POST['equip_key'] ?? '') ?: null);"),
    ]),
    "BUG-009": ("image-set-long-url-gem-loss", [
        ("includes/gems_lib.php",
         "    if (!spendGems($pdo, $userId, (int)$item['cost_gems'])) {\n        return ['ok' => false, 'message' => 'Not enough gems.'];\n    }\n\n"
         "    $stmt = $pdo->prepare('INSERT INTO image_set_requests (user_id, item_key, image_url, status) VALUES (?, ?, ?, ?)');\n"
         "    $stmt->execute([$userId, $itemKey, $imageUrl, 'pending']);\n",
         "    if (mb_strlen($imageUrl) > 255) {   // image_url is VARCHAR(255): refuse BEFORE any gem is spent\n"
         "        return ['ok' => false, 'message' => 'Image link is too long (max 255 characters).'];\n    }\n\n"
         "    $pdo->beginTransaction();             // spend + request are one unit: a failing INSERT must not cost gems\n"
         "    try {\n"
         "        if (!spendGems($pdo, $userId, (int)$item['cost_gems'])) {\n            $pdo->rollBack();\n            return ['ok' => false, 'message' => 'Not enough gems.'];\n        }\n"
         "        $stmt = $pdo->prepare('INSERT INTO image_set_requests (user_id, item_key, image_url, status) VALUES (?, ?, ?, ?)');\n"
         "        $stmt->execute([$userId, $itemKey, $imageUrl, 'pending']);\n"
         "        $pdo->commit();\n"
         "    } catch (Throwable $e) {\n        if ($pdo->inTransaction()) {\n            $pdo->rollBack();\n        }\n"
         "        return ['ok' => false, 'message' => 'Could not create the request. No gems were spent.'];\n    }\n"),
    ]),
    "BUG-010": ("spend-gems-race", [
        ("includes/gems_lib.php",
         "    if ($amount <= 0 || getUserGems($pdo, $userId) < $amount) {\n        return false;\n    }\n"
         "    $pdo->prepare('UPDATE users SET gems = gems - ? WHERE id = ?')->execute([$amount, $userId]);\n    return true;",
         "    if ($amount <= 0) {\n        return false;\n    }\n"
         "    // atomic check-and-debit: the balance test and the update are ONE statement (no read-then-write race)\n"
         "    $st = $pdo->prepare('UPDATE users SET gems = gems - ? WHERE id = ? AND gems >= ?');\n"
         "    $st->execute([$amount, $userId, $amount]);\n    return $st->rowCount() === 1;"),
    ]),
    "BUG-011": ("gallery-reaction-type", [
        ("pages/gallery.php",
         "    $r_type = $_POST['reaction_type'];\n    $u_id = $_SESSION['user_id'];\n",
         "    $r_type = (string)($_POST['reaction_type'] ?? '');\n    $u_id = $_SESSION['user_id'];\n"
         "    if (!in_array($r_type, ['like', 'love', 'fire'], true)) {   // same allow-list as the community gallery\n"
         "        header('Location: gallery.php');\n        exit;\n    }\n"),
    ]),
    "BUG-012": ("reaction-target-validation", [
        ("pages/gallery.php",
         "    $stmt = $pdo->prepare('SELECT reaction_type FROM gallery_reactions WHERE user_id = ? AND gallery_id = ?');\n    $stmt->execute([$u_id, $g_id]);\n    $existing = $stmt->fetch();\n",
         "    $ex = $pdo->prepare('SELECT 1 FROM gallery WHERE id = ?');\n    $ex->execute([$g_id]);\n"
         "    if (!$ex->fetch()) {                // reactions (and gem rewards) only for artworks that exist\n        header('Location: gallery.php');\n        exit;\n    }\n\n"
         "    $stmt = $pdo->prepare('SELECT reaction_type FROM gallery_reactions WHERE user_id = ? AND gallery_id = ?');\n    $stmt->execute([$u_id, $g_id]);\n    $existing = $stmt->fetch();\n"),
        ("includes/community_gallery_lib.php",
         "    $check = $pdo->prepare('SELECT reaction_type FROM community_reactions WHERE user_id = ? AND post_id = ?');",
         "    $ex = $pdo->prepare(\"SELECT 1 FROM community_posts WHERE id = ? AND status = 'approved'\");\n    $ex->execute([$post_id]);\n"
         "    if (!$ex->fetch()) {                // only approved posts can receive reactions\n        header('Location: community_gallery.php');\n        exit;\n    }\n\n"
         "    $check = $pdo->prepare('SELECT reaction_type FROM community_reactions WHERE user_id = ? AND post_id = ?');"),
    ]),
    "BUG-014": ("stats-gem-transactions", [
        ("pages/admin_stats.php",
         "$gem_txns          = safeQ($pdo, 'SELECT COUNT(*) FROM gem_transactions');",
         "$gem_txns          = safeQ($pdo, 'SELECT COALESCE((SELECT SUM(`count`) FROM gem_mission_log), 0) + (SELECT COUNT(*) FROM user_inventory) + (SELECT COUNT(*) FROM image_set_requests)');"),
    ]),
    "BUG-015": ("delete-bot-orphans", [
        ("pages/admin_bots.php",
         "    $pdo->prepare(\"DELETE FROM bot_themes WHERE bot_id=?\")->execute([$did]);\n    $pdo->prepare(\"DELETE FROM bots WHERE id=?\")->execute([$did]);",
         "    $pdo->prepare(\"DELETE FROM bot_themes WHERE bot_id=?\")->execute([$did]);\n"
         "    $pdo->prepare(\"DELETE FROM ratings WHERE bot_id=?\")->execute([$did]);\n"
         "    $pdo->prepare(\"DELETE FROM comments WHERE bot_id=?\")->execute([$did]);\n"
         "    $pdo->prepare(\"DELETE FROM bot_group_members WHERE bot_id=?\")->execute([$did]);\n"
         "    $pdo->prepare(\"DELETE FROM bots WHERE id=?\")->execute([$did]);"),
    ]),
    "BUG-016": ("admin-add-bot-button-markup", [
        ("pages/admin_add_bot.php",
         "        <button <?= csrf_field() ?>\n                    <button type=\"submit\"",
         "        <?= csrf_field() ?>\n        <button type=\"submit\""),
    ]),
    "BUG-017": ("admin-denied-http-403", [
        ("pages/admin_bots.php", "    die(\"<h3 style='color: #ef4444; text-align: center; margin-top: 50px;'>Access Denied!",
         "    http_response_code(403);\n    die(\"<h3 style='color: #ef4444; text-align: center; margin-top: 50px;'>Access Denied!"),
        ("pages/admin_community.php", "    die(\"<h3 style='color:#ef4444;text-align:center;margin-top:50px;'>Access Denied!",
         "    http_response_code(403);\n    die(\"<h3 style='color:#ef4444;text-align:center;margin-top:50px;'>Access Denied!"),
        ("pages/admin_groups.php", "    die(\"<h3 style='color: #ef4444; text-align: center; margin-top: 50px;'>Access Denied!",
         "    http_response_code(403);\n    die(\"<h3 style='color: #ef4444; text-align: center; margin-top: 50px;'>Access Denied!"),
        ("pages/admin_stats.php", "    die(\"<div style='color:#ef4444;text-align:center;padding:60px;font-family:sans-serif;'><h3>Access Denied",
         "    http_response_code(403);\n    die(\"<div style='color:#ef4444;text-align:center;padding:60px;font-family:sans-serif;'><h3>Access Denied"),
    ]),
    "BUG-018": ("deny-internal-files", [
        # file creation: (path, None, content)
        (".htaccess", None,
         "# Internal files must never be downloadable (Apache). Not interpreted by PHP's built-in server.\n"
         "Options -Indexes\n"
         "<FilesMatch \"\\.(sql|code-workspace|md|log|bak|ini|json|lock)$\">\n    Require all denied\n</FilesMatch>\n"
         "RedirectMatch 403 ^/anyn/(sql|includes|config)/\n"),
        ("sql/.htaccess", None, "Require all denied\n"),
    ]),
}


def apply_edits(root, edits, bug):
    for rel, old, new in edits:
        path = os.path.join(root, rel)
        if old is None:                                   # create file
            os.makedirs(os.path.dirname(path) or root, exist_ok=True)
            open(path, "w", encoding="utf-8", newline="").write(new)
            continue
        s = open(path, encoding="utf-8", newline="").read()   # newline="" keeps the file's own CRLF / LF endings
        crlf = "\r\n" in s
        if crlf:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if s.count(old) != 1:
            raise SystemExit(f"[{bug}] anchor matches {s.count(old)}x in {rel}:\n{old[:120]!r}")
        open(path, "w", encoding="utf-8", newline="").write(s.replace(old, new))


def build(src, dst, only=None):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    n = 0
    for bug, (slug, edits) in FIXES.items():
        if only and bug not in only:
            continue
        apply_edits(dst, edits, bug)
        n += 1
    return n


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "apply":
        only = set(sys.argv[4].split(",")) if len(sys.argv) > 4 else None
        print(f"applied {build(sys.argv[2], sys.argv[3], only)} fixes -> {sys.argv[3]}")
    elif cmd == "diffs":
        src, out = os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
        os.makedirs(out, exist_ok=True)
        for bug, (slug, edits) in FIXES.items():
            work = os.path.join(out, "_tmp_" + bug)
            os.makedirs(work)
            os.symlink(src, os.path.join(work, "a"))
            build(src, os.path.join(work, "b"), {bug})
            d = subprocess.run(["diff", "-ruN", "a", "b"], cwd=work, capture_output=True).stdout
            lines = [ln for ln in d.split(b"\n") if not ln.startswith(b"diff ")]
            lines = [ln.split(b"\t")[0] if ln.startswith((b"--- ", b"+++ ")) else ln for ln in lines]
            open(os.path.join(out, f"{bug}_{slug}.patch"), "wb").write(b"\n".join(lines))
            shutil.rmtree(work)
        print("patches ->", out)
