<?php
/**
 * CLI: create a fresh SQLite database from the reconstructed MySQL base schema,
 * going through the same translation layer the web app uses.
 * Usage: php init_db.php /path/to/anyn.sqlite /path/to/base_schema_mysql.sql
 */
require __DIR__ . '/../shim/MysqlOnSqlitePDO.php';

[$_, $dbFile, $schemaFile] = $argv + [null, null, null];
if (!$dbFile || !$schemaFile) {
    fwrite(STDERR, "usage: php init_db.php <sqlite-file> <schema.sql>\n");
    exit(2);
}
foreach ([$dbFile, $dbFile . '-wal', $dbFile . '-shm'] as $f) {
    if (is_file($f)) {
        unlink($f);
    }
}
$pdo = new MysqlOnSqlitePDO('sqlite:' . $dbFile, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$sql = preg_replace('/^\s*--.*$/m', '', file_get_contents($schemaFile));
$n = 0;
foreach (array_filter(array_map('trim', explode(';', $sql))) as $stmt) {
    $pdo->exec($stmt);
    $n++;
}
echo "created $n tables in $dbFile\n";
