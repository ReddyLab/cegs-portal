const { spawn } = require('child_process');
const tailwind = spawn('npx', ['tailwindcss', '-w', '-i', 'cegs_portal/static/css/project.css.tw', '-o', 'cegs_portal/static/css/project.css']);
tailwind.stdout.on('data', (data) => {
  console.log(`[tailwind]: ${data}`.trim());
});
tailwind.stderr.on('data', (data) => {
  console.error(`[tailwind] stderr: ${data}`.trim());
});
tailwind.on('close', (code) => {
  console.log(`TailwindCSS exited with code ${code}`);
});

const django = spawn('make', ['run']);
django.stdout.on('data', (data) => {
  console.log(`[django]: ${data}`.trim());
});
django.stderr.on('data', (data) => {
  console.error(`[django] stderr: ${data}`.trim());
});
django.on('close', (code) => {
  console.log(`Django exited with code ${code}`);
});
