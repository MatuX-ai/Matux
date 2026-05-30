const { execSync } = require('child_process');
try {
  console.log(execSync('npx ng build', { encoding: 'utf-8', stdio: 'pipe' }));
} catch(e) {
  console.log(e.stdout);
  console.log(e.stderr);
}
