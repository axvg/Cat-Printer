const $ = (id) => document.getElementById(id);

const state = { source: null, quality: 1, printable: false };

function say(text, error = false) {
  $('status').textContent = text;
  $('status').classList.toggle('error', error);
}

async function api(path, body, type) {
  const headers = type ? { 'Content-Type': type } : {};
  const response = await fetch(path, { method: 'POST', body, headers });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response;
}

async function findPrinter() {
  const chip = $('device');
  try {
    const { devices } = await (await api('/devices', '{}')).json();
    if (!devices.length) {
      chip.className = 'chip off';
      chip.textContent = 'sin impresora';
      return;
    }
    const [printer] = devices;
    state.device = `${printer.name},${printer.address}`;
    await api('/connect', JSON.stringify({ device: state.device }));
    chip.className = 'chip on';
    chip.textContent = printer.name;
    chip.title = printer.address;
  } catch (error) {
    chip.className = 'chip off';
    chip.textContent = 'sin impresora';
    say(error.message, true);
  }
}

async function render() {
  if (!state.source) return;
  const options = new URLSearchParams({
    ascii: $('ascii').checked ? '1' : '0'
  });
  let body = null;
  if (state.source.url) {
    options.set('url', state.source.url);
  } else {
    options.set('name', state.source.file.name);
    body = state.source.file;
  }
  say('convirtiendo…');
  try {
    const response = await api(`/render?${options}`, body, 'application/octet-stream');
    const blob = await response.blob();
    $('preview-img').src = URL.createObjectURL(blob);
    $('preview-size').textContent = `${response.headers.get('X-Bitmap-Size')} px`;
    $('preview').hidden = false;
    state.printable = true;
    $('print').disabled = false;
    say('');
  } catch (error) {
    state.printable = false;
    $('print').disabled = true;
    say(error.message, true);
  }
}

async function print() {
  if (!state.printable) return;
  const button = $('print');
  button.classList.add('busy');
  button.disabled = true;
  say('imprimiendo…');
  try {
    await api('/set', JSON.stringify({
      energy: Number($('energy').value),      // server multiplies by 0x100
      quality: 4 * (state.quality + 5)        // same mapping as printer.py -q
    }));
    await api('/print', new Blob(), 'application/octet-stream');
    say('listo');
  } catch (error) {
    say(error.message, true);
  }
  button.classList.remove('busy');
  button.disabled = false;
}

function pick(file) {
  if (!file) return;
  state.source = { file };
  $('url').value = '';
  render();
}

$('file').addEventListener('change', (event) => pick(event.target.files[0]));

const drop = $('drop');
for (const name of ['dragenter', 'dragover']) {
  drop.addEventListener(name, (event) => {
    event.preventDefault();
    drop.classList.add('over');
  });
}
for (const name of ['dragleave', 'drop']) {
  drop.addEventListener(name, () => drop.classList.remove('over'));
}
drop.addEventListener('drop', (event) => {
  event.preventDefault();
  pick(event.dataTransfer.files[0]);
});
drop.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' || event.key === ' ') $('file').click();
});

$('url-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const url = $('url').value.trim();
  if (!url) return;
  state.source = { url };
  render();
});

$('energy').addEventListener('input', (event) => {
  $('energy-out').textContent = (event.target.value / 100).toFixed(2);
});

$('quality').addEventListener('click', (event) => {
  if (event.target.tagName !== 'BUTTON') return;
  for (const button of $('quality').children) button.classList.remove('on');
  event.target.classList.add('on');
  state.quality = Number(event.target.value);
});

$('ascii').addEventListener('change', render);
$('print').addEventListener('click', print);
$('device').addEventListener('click', findPrinter);

findPrinter();
