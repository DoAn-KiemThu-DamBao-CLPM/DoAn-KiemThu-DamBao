<?php
/**
 * MysqlOnSqlitePDO — QA test-harness compatibility layer.
 *
 * WHY: the Anyn web app talks to MySQL/MariaDB through PDO, but the cloud sandbox used to
 * run the test campaign has no MySQL server. This class lets the UNMODIFIED application code
 * run on top of SQLite by translating the (small) subset of MySQL dialect the app uses.
 *
 * It only replaces the DB connection. No business logic of the application is changed.
 * It also emulates two MySQL behaviours that matter for testing:
 *   - strict mode:   VARCHAR(n) length limits and ENUM(...) value lists are enforced (CHECK constraints)
 *   - ci collation:  VARCHAR/ENUM columns compare case-insensitively (COLLATE NOCASE)
 * and it records "queries per request" metrics (ANYN_QLOG) used by the performance report.
 *
 * Limits (documented in the Test Plan, risk R-07): SQLite is not MySQL. Row locking, real
 * concurrency, information_schema speed and optimizer behaviour are NOT reproduced.
 */
final class MysqlOnSqlitePDO extends PDO
{
    public static int $nQueries = 0;
    public static float $sqlSeconds = 0.0;
    private static bool $shutdownRegistered = false;

    /** conflict target per table for "ON DUPLICATE KEY UPDATE" -> "ON CONFLICT(...) DO UPDATE" */
    private const UPSERT_TARGETS = [
        'shop_items'               => 'item_key',
        'commission_monthly_limit' => 'user_id, month_year, commission_type',
        'gem_mission_log'          => 'user_id, mission_key, log_date',
    ];

    public function __construct(string $dsn, ?string $user = null, ?string $pass = null, ?array $options = null)
    {
        parent::__construct($dsn, $user, $pass, $options ?? []);
        $this->setAttribute(PDO::ATTR_STATEMENT_CLASS, [ShimStatement::class, [$this]]);
        parent::exec('PRAGMA journal_mode=WAL');
        parent::exec('PRAGMA busy_timeout=8000');
        parent::exec('PRAGMA synchronous=NORMAL');

        // MySQL scalar functions used by the app
        $this->sqliteCreateFunction('NOW', fn() => gmdate('Y-m-d H:i:s'), 0);
        $this->sqliteCreateFunction('DATABASE', fn() => 'anyn', 0);
        $this->sqliteCreateFunction('FIELD', function (...$a) {
            $needle = array_shift($a);
            foreach ($a as $i => $v) {
                if (strcasecmp((string)$needle, (string)$v) === 0) {
                    return $i + 1;
                }
            }
            return 0;
        }, -1);

        // information_schema emulation (schema.php asks it whether columns / tables / unique keys exist)
        parent::exec("CREATE TEMP VIEW IF NOT EXISTS _is_tables AS
            SELECT 'anyn' AS TABLE_SCHEMA, name AS TABLE_NAME FROM sqlite_master WHERE type='table'");
        parent::exec("CREATE TEMP VIEW IF NOT EXISTS _is_columns AS
            SELECT 'anyn' AS TABLE_SCHEMA, m.name AS TABLE_NAME, p.name AS COLUMN_NAME
            FROM sqlite_master m, pragma_table_info(m.name) p WHERE m.type='table'");
        parent::exec("CREATE TEMP VIEW IF NOT EXISTS _is_statistics AS
            SELECT 'anyn' AS TABLE_SCHEMA, m.name AS TABLE_NAME, ii.name AS COLUMN_NAME,
                   CASE il.\"unique\" WHEN 1 THEN 0 ELSE 1 END AS NON_UNIQUE
            FROM sqlite_master m, pragma_index_list(m.name) il, pragma_index_info(il.name) ii
            WHERE m.type='table'");

        if (!self::$shutdownRegistered && getenv('ANYN_QLOG')) {
            self::$shutdownRegistered = true;
            $t0 = microtime(true);
            register_shutdown_function(function () use ($t0) {
                $line = implode("\t", [
                    gmdate('c'),
                    $_SERVER['REQUEST_METHOD'] ?? 'CLI',
                    $_SERVER['REQUEST_URI'] ?? '-',
                    http_response_code() ?: 200,
                    self::$nQueries,
                    round(self::$sqlSeconds * 1000, 2),
                    round((microtime(true) - $t0) * 1000, 2),
                    !empty($_COOKIE[session_name()]) ? 'cookie' : 'nocookie',
                ]) . "\n";
                @file_put_contents(getenv('ANYN_QLOG'), $line, FILE_APPEND | LOCK_EX);
            });
        }
    }

    /* ------------------------------------------------------------------ PDO overrides */

    public function prepare(string $query, array $options = []): PDOStatement|false
    {
        return parent::prepare($this->translate($query)[0], $options);
    }

    public function rawPrepare(string $translated): PDOStatement|false
    {
        return parent::prepare($translated);
    }

    public function exec(string $statement): int|false
    {
        $t = microtime(true);
        $n = 0;
        foreach ($this->translate($statement) as $sql) {
            $r = parent::exec($sql);
            $n += ($r === false) ? 0 : $r;
        }
        self::tick(microtime(true) - $t);
        return $n;
    }

    public function query(string $query, ?int $fetchMode = null, mixed ...$fetchModeArgs): PDOStatement|false
    {
        $t = microtime(true);
        $sql = $this->translate($query)[0];
        $st = $fetchMode === null ? parent::query($sql) : parent::query($sql, $fetchMode, ...$fetchModeArgs);
        self::tick(microtime(true) - $t);
        return $st;
    }

    public static function tick(float $seconds): void
    {
        self::$nQueries++;
        self::$sqlSeconds += $seconds;
    }

    /* ------------------------------------------------------------------ translation */

    /** @return string[] one or more SQLite statements */
    public function translate(string $sql): array
    {
        $s = trim($sql);

        // SHOW COLUMNS FROM t LIKE 'c'
        if (preg_match("/^SHOW\\s+COLUMNS\\s+FROM\\s+`?(\\w+)`?\\s+LIKE\\s+'([^']+)'/i", $s, $m)) {
            return ["SELECT name AS Field FROM pragma_table_info('{$m[1]}') WHERE name = '{$m[2]}'"];
        }
        if (preg_match('/^CREATE\s+TABLE\b/i', $s)) {
            return $this->createTable($s);
        }
        if (preg_match('/^ALTER\s+TABLE\b/i', $s)) {
            return $this->alterTable($s);
        }

        // information_schema.*
        $s = preg_replace('/\binformation_schema\.COLUMNS\b/i', '_is_columns', $s);
        $s = preg_replace('/\binformation_schema\.TABLES\b/i', '_is_tables', $s);
        $s = preg_replace('/\binformation_schema\.STATISTICS\b/i', '_is_statistics', $s);

        // date arithmetic
        $s = preg_replace_callback('/\(?\s*NOW\(\)\s*-\s*INTERVAL\s+(\d+)\s+(SECOND|MINUTE|HOUR|DAY)S?\s*\)?/i',
            fn($m) => "datetime('now','-{$m[1]} " . strtolower($m[2]) . "s')", $s);
        $s = preg_replace_callback('/DATE_ADD\(\s*NOW\(\)\s*,\s*INTERVAL\s+(\d+)\s+(SECOND|MINUTE|HOUR|DAY)S?\s*\)/i',
            fn($m) => "datetime('now','+{$m[1]} " . strtolower($m[2]) . "s')", $s);
        $s = preg_replace('/\bNOW\(\)/i', "datetime('now')", $s);

        // GROUP_CONCAT(x SEPARATOR ',') -> GROUP_CONCAT(x, ',')
        $s = preg_replace("/GROUP_CONCAT\\(\\s*(.+?)\\s+SEPARATOR\\s+('[^']*')\\s*\\)/i", 'GROUP_CONCAT($1, $2)', $s);

        // INSERT IGNORE
        $s = preg_replace('/^INSERT\s+IGNORE\s+INTO/i', 'INSERT OR IGNORE INTO', $s);

        // ON DUPLICATE KEY UPDATE
        if (preg_match('/INSERT\s+INTO\s+`?(\w+)`?/i', $s, $tm) && stripos($s, 'ON DUPLICATE KEY UPDATE') !== false) {
            $target = self::UPSERT_TARGETS[strtolower($tm[1])] ?? null;
            if ($target === null) {
                throw new PDOException('shim: no upsert target configured for ' . $tm[1]);
            }
            $s = preg_replace('/ON\s+DUPLICATE\s+KEY\s+UPDATE/i', "ON CONFLICT($target) DO UPDATE SET", $s);
            $s = preg_replace('/VALUES\(\s*(\w+)\s*\)/i', 'excluded.$1', $s);
        }

        // LIKE ? needs an explicit ESCAPE clause in SQLite (MySQL's default escape char is backslash)
        if (stripos($s, 'ESCAPE') === false) {
            $s = preg_replace('/\bLIKE\s+\?/i', "LIKE ? ESCAPE '\\\\'", $s);
        }
        return [$s];
    }

    private function colDef(string $def): string
    {
        $def = trim($def);
        if (!preg_match('/^`?(\w+)`?\s+(.*)$/s', $def, $m)) {
            return $def;
        }
        [$all, $name, $rest] = $m;
        if (preg_match('/^(?:INT|INTEGER|BIGINT)(?:\(\d+\))?\s+(?:NOT\s+NULL\s+)?AUTO_INCREMENT\s+PRIMARY\s+KEY/i', $rest)) {
            return "$name INTEGER PRIMARY KEY AUTOINCREMENT";
        }
        $rest = preg_replace_callback('/^ENUM\s*\(([^)]*)\)/i',
            fn($e) => "TEXT COLLATE NOCASE CHECK($name IN ({$e[1]}))", $rest);
        $rest = preg_replace_callback('/^VARCHAR\s*\((\d+)\)/i',
            fn($e) => "TEXT COLLATE NOCASE CHECK(length($name) <= {$e[1]})", $rest);
        $rest = preg_replace('/^CHAR\s*\(\d+\)/i', 'TEXT COLLATE NOCASE', $rest);
        $rest = preg_replace('/\s+AFTER\s+`?\w+`?/i', '', $rest);
        $rest = preg_replace('/\s+UNSIGNED\b/i', '', $rest);
        return "$name $rest";
    }

    private function splitTop(string $body): array
    {
        $parts = [];
        $depth = 0;
        $buf = '';
        $q = null;
        for ($i = 0, $n = strlen($body); $i < $n; $i++) {
            $c = $body[$i];
            if ($q !== null) {
                $buf .= $c;
                if ($c === $q) {
                    $q = null;
                }
                continue;
            }
            if ($c === "'" || $c === '"') {
                $q = $c;
                $buf .= $c;
            } elseif ($c === '(') {
                $depth++;
                $buf .= $c;
            } elseif ($c === ')') {
                $depth--;
                $buf .= $c;
            } elseif ($c === ',' && $depth === 0) {
                $parts[] = $buf;
                $buf = '';
            } else {
                $buf .= $c;
            }
        }
        if (trim($buf) !== '') {
            $parts[] = $buf;
        }
        return $parts;
    }

    private function createTable(string $sql): array
    {
        if (!preg_match('/^CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?\s*\((.*)\)\s*(?:ENGINE[^)]*)?;?\s*$/is', $sql, $m)) {
            return [$sql];
        }
        $ine = $m[1] ? 'IF NOT EXISTS ' : '';
        $table = $m[2];
        $cols = [];
        $extra = [];
        foreach ($this->splitTop($m[3]) as $part) {
            $p = trim($part);
            if (preg_match('/^UNIQUE\s+(?:KEY|INDEX)\s+`?\w+`?\s*\((.*)\)$/is', $p, $u)) {
                $cols[] = 'UNIQUE (' . $u[1] . ')';
            } elseif (preg_match('/^(?:INDEX|KEY)\s+`?(\w+)`?\s*\((.*)\)$/is', $p, $u)) {
                $extra[] = "CREATE INDEX IF NOT EXISTS {$u[1]} ON $table({$u[2]})";
            } elseif (preg_match('/^PRIMARY\s+KEY\b/i', $p)) {
                $cols[] = $p;
            } else {
                $cols[] = $this->colDef($p);
            }
        }
        return array_merge(["CREATE TABLE {$ine}$table (" . implode(', ', $cols) . ')'], $extra);
    }

    private function alterTable(string $sql): array
    {
        if (preg_match('/^ALTER\s+TABLE\s+`?(\w+)`?\s+ADD\s+COLUMN\s+(.*)$/is', $sql, $m)) {
            return ["ALTER TABLE {$m[1]} ADD COLUMN " . $this->colDef($m[2])];
        }
        if (preg_match('/^ALTER\s+TABLE\s+`?(\w+)`?\s+ADD\s+UNIQUE\s+(?:KEY|INDEX)\s+`?(\w+)`?\s*\((.*)\)\s*$/is', $sql, $m)) {
            return ["CREATE UNIQUE INDEX {$m[2]} ON {$m[1]}({$m[3]})"];
        }
        if (preg_match('/^ALTER\s+TABLE\s+`?(\w+)`?\s+ADD\s+(?:INDEX|KEY)\s+`?(\w+)`?\s*\((.*)\)\s*$/is', $sql, $m)) {
            return ["CREATE INDEX IF NOT EXISTS {$m[2]} ON {$m[1]}({$m[3]})"];
        }
        if (preg_match('/^ALTER\s+TABLE\s+`?\w+`?\s+MODIFY\b/i', $sql)) {
            return ['SELECT 1'];   // enum widening/narrowing: nothing to do in the emulation
        }
        throw new PDOException('shim: unsupported ALTER TABLE: ' . $sql);
    }
}

final class ShimStatement extends PDOStatement
{
    private PDO $shimPdo;

    protected function __construct(PDO $pdo)
    {
        $this->shimPdo = $pdo;
    }

    public function execute(?array $params = null): bool
    {
        $t = microtime(true);
        $ok = parent::execute($params);
        MysqlOnSqlitePDO::tick(microtime(true) - $t);
        $this->lastParams = $params;
        return $ok;
    }

    private ?array $lastParams = null;

    /** MySQL reports the number of rows of a buffered SELECT; SQLite's PDO driver returns 0. */
    public function rowCount(): int
    {
        if (preg_match('/^\s*SELECT\b/i', $this->queryString)) {
            $c = $this->shimPdo->rawPrepare('SELECT COUNT(*) FROM (' . $this->queryString . ')');
            $c->execute($this->lastParams);
            return (int)$c->fetchColumn();
        }
        return parent::rowCount();
    }
}
