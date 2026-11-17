"""Windows mouse events only during a consented hardware trial; no keyboard hooks."""
import ctypes
import os
import queue
import time
import threading

class NativeMouse:
    def __init__(self):
        self.events=queue.Queue(maxsize=18000);self.overflow=False;self.listener=None
    def start(self):
        if os.name!='nt':raise RuntimeError("Native mouse capture requires Windows")
        try:ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except OSError:pass
        from pynput import mouse
        from ctypes import wintypes
        user32=ctypes.windll.user32
        user32.GetForegroundWindow.restype=wintypes.HWND
        user32.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
        user32.GetWindowTextW.restype=ctypes.c_int
        self.events=queue.Queue(maxsize=18000);self.overflow=False
        def emit(kind,x,y,button='',pressed='',dx='',dy=''):
            window=ctypes.windll.user32.GetForegroundWindow()
            text=ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.GetWindowTextW(window,text,512)
            title=text.value
            if not any(word in title.lower() for word in ('figma','leb2')):return
            value={'event_type':kind,'backend_us':time.perf_counter_ns()//1000,'screen_x':x,'screen_y':y,
                   'button':button,'pressed':pressed,'scroll_dx':dx,'scroll_dy':dy,
                   'foreground_title':title,'coordinate_space':'windows_virtual_screen_physical_pixels',
                   'source':'native_mouse','page_url':'unavailable','target_element_id':'unavailable'}
            try:self.events.put_nowait(value)
            except queue.Full:self.overflow=True
        self.listener=mouse.Listener(on_move=lambda x,y:emit('move',x,y),
            on_click=lambda x,y,b,p:emit('button',x,y,str(b),p),
            on_scroll=lambda x,y,dx,dy:emit('scroll',x,y,dx=dx,dy=dy))
        self.listener.start()
        ready=threading.Event()
        def wait_ready():
            self.listener.wait();ready.set()
        threading.Thread(target=wait_ready,daemon=True).start()
        if not ready.wait(3) or not self.listener.is_alive():
            self.listener.stop()
            raise RuntimeError("Native mouse listener did not become ready")
    def stop(self):
        if self.listener is not None:self.listener.stop()
    def drain(self, limit=240):
        for _ in range(limit):
            try:yield self.events.get_nowait()
            except queue.Empty:return
    def healthy(self):return self.listener is not None and self.listener.is_alive()
