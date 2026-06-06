const { ESLint } = require('eslint');
const fs = require('fs');

async function main() {
  const eslint = new ESLint({
    useEslintrc: true,
    cwd: 'g:\\iMato',
  });

  const results = await eslint.lintFiles(['src/']);

  const formatter = await eslint.loadFormatter('json');
  const resultText = await formatter.format(results);

  fs.writeFileSync('eslint-report.json', resultText, 'utf8');

  // Also count errors per file
  console.log('=== Errors per file ===');
  const fileErrors = {};
  const fileWarnings = {};
  const errorTypes = {};
  const fileErrorTypes = {};

  for (const entry of results) {
    const filePath = entry.filePath.replace(/\\/g, '/').split('/src/')[1] || entry.filePath;
    const errors = entry.messages.filter(m => m.severity === 2);
    const warnings = entry.messages.filter(m => m.severity === 1);
    if (errors.length > 0) {
      fileErrors[filePath] = errors.length;
    }
    if (warnings.length > 0) {
      fileWarnings[filePath] = warnings.length;
    }
    for (const m of entry.messages) {
      if (m.severity === 2) {
        const rule = m.ruleId || 'parsing-error';
        errorTypes[rule] = (errorTypes[rule] || 0) + 1;
        if (!fileErrorTypes[filePath]) fileErrorTypes[filePath] = {};
        fileErrorTypes[filePath][rule] = (fileErrorTypes[filePath][rule] || 0) + 1;
      }
    }
  }

  const sorted = Object.entries(fileErrors).sort((a, b) => b[1] - a[1]);
  for (const [fp, count] of sorted) {
    const w = fileWarnings[fp] || 0;
    const rules = Object.entries(fileErrorTypes[fp] || {}).map(([r, c]) => `${r}(${c})`).join(', ');
    console.log(`${String(count).padStart(3)} errors, ${String(w).padStart(3)} warnings: ${fp} [${rules}]`);
  }

  console.log(`\nTotal files with errors: ${sorted.length}`);
  const totalErrors = Object.values(fileErrors).reduce((a, b) => a + b, 0);
  const totalWarnings = Object.values(fileWarnings).reduce((a, b) => a + b, 0);
  console.log(`Total errors: ${totalErrors}`);
  console.log(`Total warnings: ${totalWarnings}`);

  console.log('\n=== Error types breakdown ===');
  const sortedTypes = Object.entries(errorTypes).sort((a, b) => b[1] - a[1]);
  for (const [rule, count] of sortedTypes) {
    console.log(`${String(count).padStart(3)}: ${rule}`);
  }
}

main().catch(console.error);
