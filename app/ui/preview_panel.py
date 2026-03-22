"""Floating in-app preview panel used by the waveform hover interaction."""

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as Canvas
from matplotlib.pyplot import Figure
from tkinter import Frame, Label


class PreviewPanel:
    """Render the hover preview inside the main window instead of a separate OS window."""

    def __init__(self, root, config):
        """Build the preview panel shell and its Matplotlib figure."""

        self.root = root
        self.config = config
        self.shadow = None
        self.panel = None
        self.header = None
        self.title = None
        self.canvas = None
        self.figure = Figure(constrained_layout=True)
        self.figure.patch.set_facecolor(config.theme.canvas_bg)
        self.wave_axis = self.figure.add_subplot(211)
        self.autocorr_axis = self.figure.add_subplot(212)

    def ensure_exists(self, on_drag_start, on_drag_move):
        """Create the panel lazily so hiding can fully destroy it later."""

        if self.panel is not None:
            return

        self.shadow = Frame(self.root, bg=self.config.theme.preview_shadow, bd=0, highlightthickness=0)
        self.panel = Frame(
            self.root,
            bg=self.config.theme.preview_bg,
            highlightbackground=self.config.theme.preview_border,
            highlightthickness=1,
            bd=0,
        )
        self.header = Frame(self.panel, bg=self.config.theme.preview_header_bg, height=34)
        self.header.place(x=0, y=0, relwidth=1)
        self.title = Label(
            self.header,
            text=self.config.text.preview_title,
            font=("segoe ui", 11, "bold"),
            bg=self.config.theme.preview_header_bg,
            fg=self.config.theme.preview_header_fg,
        )
        self.title.place(relx=0.5, x=-90, y=6, width=180, height=22)
        self.canvas = Canvas(self.figure, self.panel)
        self.header.bind("<ButtonPress-1>", on_drag_start)
        self.header.bind("<B1-Motion>", on_drag_move)
        self.title.bind("<ButtonPress-1>", on_drag_start)
        self.title.bind("<B1-Motion>", on_drag_move)

    def destroy(self):
        """Destroy the panel completely so hide is always definitive."""

        if self.canvas is not None and self.canvas.get_tk_widget().winfo_exists():
            self.canvas.get_tk_widget().destroy()
        if self.panel is not None and self.panel.winfo_exists():
            self.panel.destroy()
        if self.shadow is not None and self.shadow.winfo_exists():
            self.shadow.destroy()
        self.shadow = None
        self.panel = None
        self.header = None
        self.title = None
        self.canvas = None

    def place(self, x, y, width, height):
        """Place the panel and its shadow together."""

        shadow_pad = self.config.theme.preview_shadow_pad
        self.shadow.place(
            x=x - shadow_pad,
            y=y - shadow_pad,
            width=width + shadow_pad * 2,
            height=height + shadow_pad * 2,
        )
        self.panel.place(x=x, y=y, width=width, height=height)
        self.resize_canvas()

    def resize_canvas(self):
        """Stretch the embedded Matplotlib canvas to the panel body."""

        if self.panel is None or self.canvas is None:
            return
        self.canvas.get_tk_widget().place(
            x=0,
            y=34,
            width=self.panel.winfo_width(),
            height=self.panel.winfo_height() - 34,
        )

    def lift(self):
        """Keep the preview panel above the main application content."""

        self.shadow.lift()
        self.panel.lift()
        self.panel.update_idletasks()

    def draw(self):
        """Redraw the embedded Matplotlib figure."""

        if self.canvas is not None:
            self.canvas.draw()
            self.panel.update_idletasks()
