const catContainer = document.getElementById('cat-container');
const messageBubble = document.getElementById('message-bubble');
const steamContainer = document.getElementById('steam-container');
const pupils = document.querySelectorAll('.pupil');

// States
let isThinking = false;
let wpm = 0;
let keyPresses = [];
let isHovering = false;
let dragTimeout = null;

// Add base idle state
catContainer.classList.add('state-idle');

// Mouse tracking for eyes
window.electronAPI.onGlobalMouseMove((e) => {
  if (isThinking) return;
  // e has x, y of the mouse on the screen
  // Get window screen position
  const winX = window.screenX;
  const winY = window.screenY;
  
  // Calculate cat center in screen coordinates
  const rect = catContainer.getBoundingClientRect();
  const centerX = winX + rect.left + rect.width / 2;
  const centerY = winY + rect.top + rect.height / 2;
  
  // Calculate angle and distance
  const angle = Math.atan2(e.y - centerY, e.x - centerX);
  const distance = Math.min(3, Math.hypot(e.x - centerX, e.y - centerY) / 100);
  
  const moveX = Math.cos(angle) * distance;
  const moveY = Math.sin(angle) * distance;

  pupils.forEach(pupil => {
    pupil.style.transform = `translate(${moveX + 1}px, ${moveY - 1}px)`;
  });
});

// We need a local mousemove for the "hunting" and eye tracking when mouse is over the window
document.addEventListener('mousemove', (e) => {
  const rect = catContainer.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  
  const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
  const distance = Math.min(3, Math.hypot(e.clientX - centerX, e.clientY - centerY) / 10);
  
  const moveX = Math.cos(angle) * distance;
  const moveY = Math.sin(angle) * distance;

  pupils.forEach(pupil => {
    pupil.style.transform = `translate(${moveX}px, ${moveY}px)`;
  });
});

// Hover for purring and click-through management
catContainer.addEventListener('mouseenter', () => {
  isHovering = true;
  catContainer.classList.add('state-purr');
  window.electronAPI.setIgnoreMouseEvents(false);
});

catContainer.addEventListener('mouseleave', () => {
  isHovering = false;
  catContainer.classList.remove('state-purr');
  window.electronAPI.setIgnoreMouseEvents(true, { forward: true });
  pupils.forEach(pupil => pupil.style.transform = `translate(1px, -1px)`);
});

// Dragging / Mochi Stretch
catContainer.addEventListener('mousedown', () => {
  catContainer.classList.add('state-stretch');
});

catContainer.addEventListener('mouseup', () => {
  catContainer.classList.remove('state-stretch');
});

// Global Keyboard tracking (Kneading & Overheat)
let kneadLeft = true;
window.electronAPI.onGlobalKeyDown((e) => {
  if (isThinking) return;

  // Kneading animation alternating paws
  catContainer.classList.remove('state-idle');
  if (kneadLeft) {
    catContainer.classList.add('state-knead-left');
    catContainer.classList.remove('state-knead-right');
  } else {
    catContainer.classList.add('state-knead-right');
    catContainer.classList.remove('state-knead-left');
  }
  kneadLeft = !kneadLeft;

  setTimeout(() => {
    catContainer.classList.remove('state-knead-left', 'state-knead-right');
    if (!catContainer.className.includes('state-')) {
      catContainer.classList.add('state-idle');
    }
  }, 100);

  // WPM tracking for Overheat
  const now = Date.now();
  keyPresses.push(now);
  // Keep only presses in the last 10 seconds
  keyPresses = keyPresses.filter(time => now - time < 10000);
  
  // WPM = (presses / 5 characters per word) * (60 / 10 seconds) = presses * 1.2
  wpm = keyPresses.length * 1.2;

  if (wpm > 80) { // arbitrary fast typing threshold
    catContainer.classList.add('state-overheat');
    steamContainer.classList.remove('hidden');
  } else {
    catContainer.classList.remove('state-overheat');
    steamContainer.classList.add('hidden');
  }
});

// AI Agent Webhooks
window.electronAPI.onAiStatus((status) => {
  if (status === 'thinking') {
    isThinking = true;
    catContainer.className = 'cat-container state-thinking';
    steamContainer.classList.add('hidden');
  } else if (status === 'done') {
    isThinking = false;
    catContainer.className = 'cat-container state-jump';
    setTimeout(() => {
      catContainer.className = 'cat-container state-idle';
    }, 600);
  }
});

window.electronAPI.onAiMessage((message) => {
  showMessage(message, 5000);
});

function showMessage(text, duration) {
  messageBubble.innerText = text;
  messageBubble.classList.remove('hidden');
  
  // Meow animation/sound could go here
  catContainer.classList.add('state-purr');

  setTimeout(() => {
    messageBubble.classList.add('hidden');
    catContainer.classList.remove('state-purr');
  }, duration);
}

// Stretch timer (every 20 minutes)
setInterval(() => {
  if (isThinking) return;
  showMessage("Time to stretch!", 4000);
  catContainer.classList.add('state-stretch');
  setTimeout(() => {
    catContainer.classList.remove('state-stretch');
  }, 4000);
}, 20 * 60 * 1000);

// Initialize interaction toggle
window.electronAPI.setIgnoreMouseEvents(true, { forward: true });
