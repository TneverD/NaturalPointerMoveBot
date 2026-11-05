import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import random
import math
import time
import threading
import queue
from PIL import Image, ImageTk, ImageGrab

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


class NaturalMouse:

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("natural pointer move bot")

        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()

        self.running = False
        self.window_rect = None
        self.target = None
        self.action = "none"
        self.repeat_count = 0

        # delay between repetitions (seconds)
        self.repeat_delay = 0.0
        # reference to the 5-second countdown before destination pick
        self.countdown_window = None
        # reference to the countdown before window selection
        self.start_countdown_window = None

        # NEW: delay before showing "select window" screen (seconds)
        self.start_delay = 5

        self.root.after(40, self.poll_events)
        self.root.after(300, self.show_start_countdown)

    # -----------------------------------------
    # COUNTDOWN BEFORE WINDOW SELECTION
    # -----------------------------------------

    def show_start_countdown(self):
        self.start_countdown_window = tk.Toplevel(self.root)
        self.start_countdown_window.title("natural pointer move bot - Starting")
        self.start_countdown_window.geometry("380x160")
        self.start_countdown_window.resizable(False, False)
        self.start_countdown_window.attributes("-topmost", True)

        tk.Label(
            self.start_countdown_window,
            text="GET READY",
            font=("Arial", 14, "bold"),
            pady=10
        ).pack()

        tk.Label(
            self.start_countdown_window,
            text="Select window screen opens in:",
            font=("Arial", 10),
            fg="#0077cc"
        ).pack(pady=2)

        self.start_countdown_number = tk.Label(
            self.start_countdown_window,
            text=str(self.start_delay),
            font=("Arial", 28, "bold"),
            fg="#00aa55"
        )
        self.start_countdown_number.pack(pady=6)

        tk.Label(
            self.start_countdown_window,
            text="ESC to cancel",
            fg="gray"
        ).pack(pady=4)

        self._start_remaining = self.start_delay

        self.start_countdown_window.bind(
            "<Escape>",
            lambda e: self.cancel_start_countdown()
        )
        self.start_countdown_window.protocol(
            "WM_DELETE_WINDOW",
            self.cancel_start_countdown
        )

        self._start_tick()

    def _start_tick(self):
        if not self.start_countdown_window or not self.start_countdown_window.winfo_exists():
            return

        if self._start_remaining <= 0:
            try:
                self.start_countdown_window.destroy()
            except tk.TclError:
                pass
            self.start_countdown_window = None
            self.start_window_selection()
            return

        self.start_countdown_number.config(text=str(self._start_remaining))
        self._start_remaining -= 1
        self.start_countdown_window.after(1000, self._start_tick)

    def cancel_start_countdown(self):
        if self.start_countdown_window:
            try:
                self.start_countdown_window.destroy()
            except tk.TclError:
                pass
            self.start_countdown_window = None
        self.root.after(200, self.show_start_countdown)

    # -----------------------------------------
    # 1. SELECT WINDOW
    # -----------------------------------------

    def start_window_selection(self):
        try:
            self.screen = ImageGrab.grab()
        except Exception as e:
            messagebox.showerror("Screenshot Error", str(e))
            return

        self.screen_width, self.screen_height = self.screen.size

        self.selector = tk.Toplevel(self.root)
        self.selector.title("natural pointer move bot - Select Window")
        self.selector.attributes("-fullscreen", True)
        self.selector.attributes("-topmost", True)

        self.canvas = tk.Canvas(
            self.selector,
            width=self.screen_width,
            height=self.screen_height,
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(fill="both", expand=True)

        self.screen_photo = ImageTk.PhotoImage(self.screen)

        self.canvas.create_image(
            0, 0,
            image=self.screen_photo,
            anchor="nw"
        )

        self.canvas.create_rectangle(
            0, 0, self.screen_width, 85,
            fill="#101827",
            stipple="gray50",
            outline=""
        )

        self.canvas.create_text(
            self.screen_width // 2, 27,
            text="natural pointer move bot - SELECT YOUR WINDOW",
            fill="white",
            font=("Arial", 16, "bold")
        )

        self.canvas.create_text(
            self.screen_width // 2, 55,
            text="Draw a rectangle around the window, then press ENTER | ESC to exit",
            fill="#00ff99",
            font=("Arial", 11, "bold")
        )

        self.canvas.bind("<ButtonPress-1>", self.selection_start)
        self.canvas.bind("<B1-Motion>", self.selection_drag)
        self.canvas.bind("<ButtonRelease-1>", self.selection_end)

        self.selector.bind("<Return>", self.confirm_window)
        self.selector.bind("<Escape>", lambda e: self.root.destroy())

        self.selector.after(100, self.selector.focus_force)

        self.rect = None
        self.selection = None

    def selection_start(self, event):
        self.x1, self.y1 = event.x, event.y

        if self.rect:
            self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(
            self.x1, self.y1,
            event.x, event.y,
            outline="#00ff99",
            width=3
        )

    def selection_drag(self, event):
        if self.rect:
            self.canvas.coords(
                self.rect,
                self.x1, self.y1,
                event.x, event.y
            )

    def selection_end(self, event):
        x2, y2 = event.x, event.y

        self.selection = (
            max(0, min(self.x1, x2)),
            max(0, min(self.y1, y2)),
            min(self.screen_width, max(self.x1, x2)),
            min(self.screen_height, max(self.y1, y2))
        )

    def confirm_window(self, event=None):
        if not self.selection:
            return

        x1, y1, x2, y2 = self.selection

        if x2 - x1 < 30 or y2 - y1 < 30:
            messagebox.showwarning(
                "Invalid Selection",
                "Please select a larger window."
            )
            return

        self.window_rect = self.selection
        self.selector.destroy()

        # wait 5 seconds before telling the user to pick a destination
        self.root.after(250, self.show_countdown_then_target)

    # -----------------------------------------
    # 5-SECOND COUNTDOWN BEFORE TARGET
    # -----------------------------------------

    def show_countdown_then_target(self):
        self.countdown_window = tk.Toplevel(self.root)
        self.countdown_window.title("natural pointer move bot - Get Ready")
        self.countdown_window.geometry("360x150")
        self.countdown_window.resizable(False, False)
        self.countdown_window.attributes("-topmost", True)

        tk.Label(
            self.countdown_window,
            text="GET READY",
            font=("Arial", 14, "bold"),
            pady=10
        ).pack()

        self.countdown_label = tk.Label(
            self.countdown_window,
            text="Selecting destination in 5 seconds...",
            font=("Arial", 11),
            fg="#0077cc"
        )
        self.countdown_label.pack(pady=5)

        self.countdown_number = tk.Label(
            self.countdown_window,
            text="5",
            font=("Arial", 28, "bold"),
            fg="#00aa55"
        )
        self.countdown_number.pack(pady=5)

        self.countdown_window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self.cancel_countdown()
        )

        self._countdown_remaining = 5
        self._countdown_tick()

    def _countdown_tick(self):
        if not self.countdown_window or not self.countdown_window.winfo_exists():
            return

        if self._countdown_remaining <= 0:
            self.cancel_countdown(destroy_only=True)
            self.show_target_selection()
            return

        self.countdown_number.config(text=str(self._countdown_remaining))
        self._countdown_remaining -= 1
        self.countdown_window.after(1000, self._countdown_tick)

    def cancel_countdown(self, destroy_only=False):
        if self.countdown_window:
            try:
                self.countdown_window.destroy()
            except tk.TclError:
                pass
            self.countdown_window = None
        if not destroy_only:
            self.root.after(200, self.show_start_countdown)

    # -----------------------------------------
    # 2. SELECT DESTINATION
    # -----------------------------------------

    def show_target_selection(self):
        crop = self.screen.crop(self.window_rect)

        self.scale = min(
            1,
            1000 / crop.width,
            650 / crop.height
        )

        self.display_width = max(1, int(crop.width * self.scale))
        self.display_height = max(1, int(crop.height * self.scale))

        crop = crop.resize(
            (self.display_width, self.display_height),
            Image.Resampling.LANCZOS
        )

        self.target_window = tk.Toplevel(self.root)
        self.target_window.title("natural pointer move bot - Select Destination")
        self.target_window.attributes("-topmost", True)
        self.target_window.resizable(False, False)

        tk.Label(
            self.target_window,
            text="WHERE SHOULD THE MOUSE GO?",
            font=("Arial", 14, "bold"),
            pady=12
        ).pack()

        self.target_photo = ImageTk.PhotoImage(crop)

        self.target_canvas = tk.Canvas(
            self.target_window,
            width=self.display_width,
            height=self.display_height,
            cursor="crosshair",
            highlightthickness=0
        )
        self.target_canvas.pack(padx=10)

        self.target_canvas.create_image(
            0, 0,
            image=self.target_photo,
            anchor="nw"
        )

        self.target_canvas.bind(
            "<Button-1>",
            self.choose_target
        )

        tk.Label(
            self.target_window,
            text="Click your destination | ESC to cancel",
            fg="gray",
            pady=10
        ).pack()

        self.target_window.bind(
            "<Escape>",
            lambda e: self.cancel_target()
        )

    def choose_target(self, event):
        x1, y1, _, _ = self.window_rect

        x = x1 + int(event.x / self.scale)
        y = y1 + int(event.y / self.scale)

        self.target = (
            max(x1, min(x, self.window_rect[2] - 1)),
            max(y1, min(y, self.window_rect[3] - 1))
        )

        self.target_window.destroy()

        self.root.after(200, self.ask_click_action)

    def cancel_target(self):
        self.target_window.destroy()
        self.root.after(200, self.show_start_countdown)

    # -----------------------------------------
    # 3. CHOOSE CLICK ACTION
    # -----------------------------------------

    def ask_click_action(self):
        self.action_window = tk.Toplevel(self.root)
        self.action_window.title("natural pointer move bot - Choose Click")
        self.action_window.geometry("340x310")
        self.action_window.resizable(False, False)
        self.action_window.attributes("-topmost", True)

        tk.Label(
            self.action_window,
            text="WHAT SHOULD I CLICK?",
            font=("Arial", 14, "bold"),
            pady=15
        ).pack()

        self.action_var = tk.StringVar(value="none")

        options = [
            ("No Click", "none"),
            ("Left Click", "left"),
            ("Right Click", "right"),
            ("Middle Click", "middle"),
            ("Double Left Click", "double")
        ]

        for label, value in options:
            ttk.Radiobutton(
                self.action_window,
                text=label,
                variable=self.action_var,
                value=value
            ).pack(anchor="w", padx=85, pady=4)

        ttk.Button(
            self.action_window,
            text="START",
            command=self.confirm_action
        ).pack(fill="x", padx=35, pady=18)

        self.action_window.bind(
            "<Escape>",
            lambda e: self.cancel_action()
        )

        self.action_window.protocol(
            "WM_DELETE_WINDOW",
            self.cancel_action
        )

        self.action_window.grab_set()

    def confirm_action(self):
        self.action = self.action_var.get()
        self.action_window.destroy()

        self.running = True
        self.stop_event.clear()
        self.pause_event.set()

        self.show_control_panel()

        threading.Thread(
            target=self.first_movement,
            daemon=True
        ).start()

    def cancel_action(self):
        self.action_window.destroy()
        self.root.after(200, self.show_start_countdown)

    # -----------------------------------------
    # 4. MOVEMENT ENGINE
    # -----------------------------------------

    def move_naturally(self, tx, ty):
        sx, sy = pyautogui.position()

        distance = math.hypot(tx - sx, ty - sy)

        if distance < 2:
            return not self.stop_event.is_set()

        duration = max(0.4, min(2.5, distance / 650))
        offset = min(110, distance * 0.18)

        cp1x = sx + (tx - sx) * 0.3 + random.uniform(-offset, offset)
        cp1y = sy + (ty - sy) * 0.3 + random.uniform(-offset, offset)

        cp2x = sx + (tx - sx) * 0.7 + random.uniform(-offset, offset)
        cp2y = sy + (ty - sy) * 0.7 + random.uniform(-offset, offset)

        steps = max(35, min(150, int(distance / 4)))

        for i in range(steps + 1):

            if self.stop_event.is_set():
                return False

            while not self.pause_event.is_set():

                if self.stop_event.is_set():
                    return False

                time.sleep(0.04)

            t = i / steps
            t = t * t * (3 - 2 * t)

            inv = 1 - t

            x = (
                inv**3 * sx
                + 3 * inv**2 * t * cp1x
                + 3 * inv * t**2 * cp2x
                + t**3 * tx
            )

            y = (
                inv**3 * sy
                + 3 * inv**2 * t * cp1y
                + 3 * inv * t**2 * cp2y
                + t**3 * ty
            )

            pyautogui.moveTo(int(x), int(y))

            time.sleep(duration / steps)

        pyautogui.moveTo(tx, ty, duration=0.08)

        return not self.stop_event.is_set()

    def perform_click(self):
        if self.stop_event.is_set():
            return

        x, y = self.target

        if self.action == "left":
            pyautogui.click(x, y, button="left")

        elif self.action == "right":
            pyautogui.click(x, y, button="right")

        elif self.action == "middle":
            pyautogui.click(x, y, button="middle")

        elif self.action == "double":
            pyautogui.doubleClick(x, y, button="left")

    # -----------------------------------------
    # 5. FIRST MOVEMENT
    # -----------------------------------------

    def first_movement(self):
        try:
            self.events.put(("status", "Moving to your destination..."))

            if self.move_naturally(*self.target):
                self.perform_click()

                if not self.stop_event.is_set():
                    self.events.put(("first_done", None))
            else:
                self.events.put(("done", None))

        except pyautogui.FailSafeException:
            self.events.put(("error", "Emergency stop activated."))

        except Exception as e:
            self.events.put(("error", str(e)))

    # -----------------------------------------
    # 6. ASK FOR REPETITION
    # -----------------------------------------

    def ask_repeat(self):
        if not self.running:
            return

        self.repeat_window = tk.Toplevel(self.root)
        self.repeat_window.title("natural pointer move bot - Repeat Movement?")
        self.repeat_window.geometry("380x200")
        self.repeat_window.resizable(False, False)
        self.repeat_window.attributes("-topmost", True)

        tk.Label(
            self.repeat_window,
            text="MOVEMENT COMPLETED!",
            font=("Arial", 14, "bold"),
            pady=12
        ).pack()

        tk.Label(
            self.repeat_window,
            text="Do you want to repeat the movement?"
        ).pack(pady=5)

        buttons = tk.Frame(self.repeat_window)
        buttons.pack(pady=18)

        ttk.Button(
            buttons,
            text="YES",
            command=self.ask_repeat_count
        ).pack(side="left", padx=10)

        ttk.Button(
            buttons,
            text="NO",
            command=self.finish
        ).pack(side="left", padx=10)

        self.repeat_window.bind(
            "<Escape>",
            lambda e: self.finish()
        )

        self.repeat_window.protocol(
            "WM_DELETE_WINDOW",
            self.finish
        )

        self.repeat_window.grab_set()

    def ask_repeat_count(self):
        self.repeat_window.destroy()

        self.count_window = tk.Toplevel(self.root)
        self.count_window.title("natural pointer move bot - Repeat Count")
        self.count_window.geometry("360x230")
        self.count_window.resizable(False, False)
        self.count_window.attributes("-topmost", True)

        tk.Label(
            self.count_window,
            text="HOW MANY MORE TIMES?",
            font=("Arial", 13, "bold"),
            pady=15
        ).pack()

        self.count_var = tk.IntVar(value=3)

        self.count_spin = tk.Spinbox(
            self.count_window,
            from_=1,
            to=100,
            textvariable=self.count_var,
            width=10,
            font=("Arial", 14),
            justify="center"
        )
        self.count_spin.pack(pady=10)

        tk.Label(
            self.count_window,
            text="Each repetition: random point → destination",
            fg="gray"
        ).pack()

        ttk.Button(
            self.count_window,
            text="NEXT",
            command=self.ask_repeat_delay
        ).pack(pady=15)

        self.count_window.bind(
            "<Escape>",
            lambda e: self.finish()
        )

        self.count_window.protocol(
            "WM_DELETE_WINDOW",
            self.finish
        )

        self.count_window.grab_set()

    # -----------------------------------------
    # ASK FOR DELAY BETWEEN REPETITIONS
    # -----------------------------------------

    def ask_repeat_delay(self):
        try:
            count = int(self.count_var.get())
            if not 1 <= count <= 100:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showwarning(
                "Invalid Number",
                "Enter a number between 1 and 100."
            )
            return

        self._validated_count = count
        self.count_window.destroy()

        self.delay_window = tk.Toplevel(self.root)
        self.delay_window.title("natural pointer move bot - Delay Between Repetitions")
        self.delay_window.geometry("400x240")
        self.delay_window.resizable(False, False)
        self.delay_window.attributes("-topmost", True)

        tk.Label(
            self.delay_window,
            text="WAIT BETWEEN REPETITIONS?",
            font=("Arial", 13, "bold"),
            pady=12
        ).pack()

        tk.Label(
            self.delay_window,
            text="Do you want a pause between each repetition?"
        ).pack(pady=4)

        self.delay_choice = tk.StringVar(value="no")

        row = tk.Frame(self.delay_window)
        row.pack(pady=8)

        ttk.Radiobutton(
            row, text="No", variable=self.delay_choice,
            value="no", command=self._delay_toggle
        ).pack(side="left", padx=12)

        ttk.Radiobutton(
            row, text="Yes", variable=self.delay_choice,
            value="yes", command=self._delay_toggle
        ).pack(side="left", padx=12)

        sec_frame = tk.Frame(self.delay_window)
        sec_frame.pack(pady=6)

        tk.Label(sec_frame, text="Seconds:").pack(side="left", padx=4)

        self.delay_seconds_var = tk.DoubleVar(value=2.0)
        self.delay_spin = tk.Spinbox(
            sec_frame,
            from_=0.5,
            to=600,
            increment=0.5,
            textvariable=self.delay_seconds_var,
            width=8,
            font=("Arial", 12),
            justify="center",
            state="disabled"
        )
        self.delay_spin.pack(side="left", padx=4)

        ttk.Button(
            self.delay_window,
            text="START REPEATING",
            command=self.start_repeating
        ).pack(pady=16)

        self.delay_window.bind(
            "<Escape>",
            lambda e: self.finish()
        )

        self.delay_window.protocol(
            "WM_DELETE_WINDOW",
            self.finish
        )

        self.delay_window.grab_set()

    def _delay_toggle(self):
        if self.delay_choice.get() == "yes":
            self.delay_spin.config(state="normal")
        else:
            self.delay_spin.config(state="disabled")

    def start_repeating(self):
        if self.delay_choice.get() == "yes":
            try:
                delay = float(self.delay_seconds_var.get())
                if not 0 <= delay <= 3600:
                    raise ValueError
            except (ValueError, tk.TclError):
                messagebox.showwarning(
                    "Invalid Delay",
                    "Enter a delay between 0 and 3600 seconds."
                )
                return
        else:
            delay = 0.0

        self.repeat_delay = delay
        self.repeat_count = self._validated_count

        if hasattr(self, "delay_window"):
            self.delay_window.destroy()
            self.delay_window = None

        self.stop_event.clear()
        self.pause_event.set()

        threading.Thread(
            target=self.repeat_worker,
            daemon=True
        ).start()

    # -----------------------------------------
    # 7. RANDOM MOVEMENT + TARGET
    # -----------------------------------------

    def repeat_worker(self):
        try:
            x1, y1, x2, y2 = self.window_rect
            tx, ty = self.target

            margin = 15

            min_x = x1 + margin
            max_x = max(min_x, x2 - margin)

            min_y = y1 + margin
            max_y = max(min_y, y2 - margin)

            for i in range(self.repeat_count):

                if self.stop_event.is_set():
                    break

                self.events.put((
                    "status",
                    f"Repetition {i + 1}/{self.repeat_count}: Random movement"
                ))

                random_x = random.randint(min_x, max_x)
                random_y = random.randint(min_y, max_y)

                if not self.move_naturally(random_x, random_y):
                    break

                if self.stop_event.is_set():
                    break

                self.events.put((
                    "status",
                    f"Repetition {i + 1}/{self.repeat_count}: Returning to target"
                ))

                if not self.move_naturally(tx, ty):
                    break

                self.perform_click()

                if self.repeat_delay > 0 and i < self.repeat_count - 1:
                    self.events.put((
                        "status",
                        f"Waiting {self.repeat_delay:g}s before next repetition..."
                    ))
                    waited = 0.0
                    while waited < self.repeat_delay:
                        if self.stop_event.is_set():
                            break
                        while not self.pause_event.is_set():
                            if self.stop_event.is_set():
                                break
                            time.sleep(0.04)
                        time.sleep(0.1)
                        waited += 0.1
                else:
                    time.sleep(0.25)

            self.events.put(("done", None))

        except pyautogui.FailSafeException:
            self.events.put(("error", "Emergency stop activated."))
            self.events.put(("done", None))

        except Exception as e:
            self.events.put(("error", str(e)))
            self.events.put(("done", None))

    # -----------------------------------------
    # 8. CONTROL PANEL
    # -----------------------------------------

    def show_control_panel(self):
        self.control = tk.Toplevel(self.root)
        self.control.title("natural pointer move bot - Control")
        self.control.geometry("320x230+20+100")
        self.control.resizable(False, False)
        self.control.attributes("-topmost", True)

        tk.Label(
            self.control,
            text="NATURAL POINTER MOVE BOT",
            font=("Arial", 13, "bold"),
            pady=10
        ).pack()

        self.status_label = tk.Label(
            self.control,
            text="Starting...",
            wraplength=280
        )
        self.status_label.pack(pady=10)

        self.pause_button = ttk.Button(
            self.control,
            text="PAUSE (F8)",
            command=self.toggle_pause
        )
        self.pause_button.pack(fill="x", padx=25, pady=5)

        ttk.Button(
            self.control,
            text="STOP (F9)",
            command=self.stop
        ).pack(fill="x", padx=25, pady=5)

        tk.Label(
            self.control,
            text="F8 Pause | F9 Stop | ESC Stop",
            fg="gray"
        ).pack(pady=8)

        self.control.bind_all("<F8>", lambda e: self.toggle_pause())
        self.control.bind_all("<F9>", lambda e: self.stop())
        self.control.bind_all("<Escape>", lambda e: self.stop())

        self.control.protocol("WM_DELETE_WINDOW", self.stop)

    def toggle_pause(self):
        if not self.running:
            return

        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.config(text="RESUME (F8)")
            self.status_label.config(text="Paused")

        else:
            self.pause_event.set()
            self.pause_button.config(text="PAUSE (F8)")
            self.status_label.config(text="Resuming...")

    def stop(self):
        if self.running:
            self.stop_event.set()
            self.pause_event.set()
            self.status_label.config(text="Stopping...")

    # -----------------------------------------
    # 9. EVENT HANDLER
    # -----------------------------------------

    def poll_events(self):
        try:
            while True:
                event, data = self.events.get_nowait()

                if event == "status":
                    if self.running:
                        self.status_label.config(text=data)

                elif event == "first_done":
                    self.status_label.config(text="First movement completed.")
                    self.ask_repeat()

                elif event == "done":
                    self.finish()

                elif event == "error":
                    messagebox.showerror("Error", data)
                    self.finish()

        except queue.Empty:
            pass

        self.root.after(40, self.poll_events)

    def finish(self):
        self.running = False
        self.stop_event.set()
        self.pause_event.set()

        for name in ("repeat_window", "count_window", "delay_window",
                     "countdown_window", "start_countdown_window"):
            window = getattr(self, name, None)
            if window:
                try:
                    window.destroy()
                except tk.TclError:
                    pass
                setattr(self, name, None)

        if hasattr(self, "control"):
            try:
                self.control.unbind_all("<F8>")
                self.control.unbind_all("<F9>")
                self.control.unbind_all("<Escape>")
                self.control.destroy()
            except tk.TclError:
                pass

        self.root.after(400, self.show_start_countdown)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    NaturalMouse().run()
