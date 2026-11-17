export function accessToken(){
 const sid=location.pathname.startsWith('/participant/')?location.pathname.split('/')[2]:null;
 if(sid){sessionStorage.removeItem('researcher-access');const fragment=new URLSearchParams(location.hash.slice(1));if(fragment.has('access')){sessionStorage.setItem('participant:'+sid,fragment.get('access'));history.replaceState(null,'',location.pathname+location.search)}return sessionStorage.getItem('participant:'+sid)||''}
 return sessionStorage.getItem('researcher-access')||'';
}
export const clientId = crypto.randomUUID();
export async function api(path, body, method) {
  const response = await fetch('/api' + path, {
    method: method || (body === undefined ? 'GET' : 'POST'),
    headers: {'Content-Type': 'application/json', 'X-Participant-Client': clientId, 'Authorization':'Bearer '+accessToken()},
    ...(body !== undefined ? {body: JSON.stringify(body)} : {})
  });
  if (!response.ok) {
    let data; try { data = await response.json(); } catch { data = {}; }
    throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || response.statusText));
  }
  return response.json();
}
export function viewport() {
  return {width: innerWidth, height: innerHeight, screen_width: screen.width, screen_height: screen.height,
    device_pixel_ratio: devicePixelRatio, screen_x: window.screenX, screen_y: window.screenY,
    scroll_x: scrollX, scroll_y: scrollY, fullscreen: !!document.fullscreenElement,
    time_origin_ms: performance.timeOrigin, scale: visualViewport?.scale || 1};
}
export async function syncClocks() {
  const samples = [];
  for (let i = 0; i < 7; i++) {
    const before = performance.now(), clock = await api('/clock'), after = performance.now();
    samples.push({browser_before_ms: before, browser_after_ms: after, backend_us: clock.backend_us,
      offset_us: clock.backend_us - (before + after) * 500, uncertainty_us: (after - before) * 500,
      browser_time_origin_ms: performance.timeOrigin, clock_segment_id: clock.clock_segment_id});
  }
  return samples.sort((a,b) => a.uncertainty_us - b.uncertainty_us);
}
export async function download(path, name) {
  const response = await fetch('/api' + path,{headers:{Authorization:'Bearer '+accessToken()}});
  if (!response.ok) { const data = await response.json(); throw new Error(data.detail || 'Export failed'); }
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}

