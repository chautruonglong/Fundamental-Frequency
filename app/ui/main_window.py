"""Main Tk window and its view helpers."""

from tkinter import Frame, Label, Tk
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Combobox, Progressbar, Style

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as Canvas
from matplotlib.pyplot import Figure

from app.ui.preview_panel import PreviewPanel


class MainWindow:
    """Own all Tk widgets and expose high-level view operations to the controller."""

    def __init__(self, config):
        """Create the window shell, sidebar controls, plots, loader, and preview panel."""

        self.config = config
        self.root = Tk()
        self.figure = Figure()
        self.figure.patch.set_facecolor(config.theme.canvas_bg)
        self.canvas = Canvas(self.figure, self.root)
        self.sidebar = None
        self.loader_frame = None
        self.file_button = None
        self.pitch_button = None
        self.window_box = None
        self.kernel_box = None
        self.threshold_box = None
        self.scatter_after = None
        self.scatter_before = None
        self.wave_plot = None
        self.graph_after = None
        self.graph_before = None
        self.graph_wave = None
        self.preview = PreviewPanel(self.root, config)
        self._configure_root()
        self._configure_styles()
        self._build_sidebar()
        self._build_graphs()

    def _configure_root(self):
        """Apply the window title, sizing rules, and shared light palette."""

        theme = self.config.theme
        text = self.config.text
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.title(text.app_title)
        self.root.wm_minsize(theme.min_window_width, theme.min_window_height)
        self.root.geometry(
            "%dx%d+%d+%d"
            % (
                theme.window_width,
                theme.window_height,
                (screen_width - theme.window_width) // 2,
                (screen_height - theme.window_height) // 2,
            )
        )
        self.root.configure(bg=theme.sidebar_bg)
        self.root.tk_setPalette(
            background=theme.sidebar_bg,
            foreground=theme.label_fg,
            activeBackground=theme.button_active_bg,
            activeForeground=theme.button_fg,
            highlightBackground=theme.sidebar_bg,
            selectBackground=theme.selected_bg,
            selectForeground=theme.label_fg,
        )

    def _configure_styles(self):
        """Centralize ttk styling so all comboboxes and progress bars match."""

        style = Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Sidebar.TCombobox",
            padding=2,
            fieldbackground=self.config.theme.input_bg,
            background=self.config.theme.input_bg,
            foreground=self.config.theme.input_fg,
            arrowcolor=self.config.theme.input_fg,
            bordercolor=self.config.theme.combo_border,
            lightcolor=self.config.theme.input_bg,
            darkcolor=self.config.theme.input_bg,
        )
        style.map(
            "Sidebar.TCombobox",
            fieldbackground=[("readonly", self.config.theme.input_bg)],
            background=[("readonly", self.config.theme.input_bg)],
            foreground=[("readonly", self.config.theme.input_fg)],
            arrowcolor=[("readonly", self.config.theme.input_fg)],
        )
        style.configure(
            "Loader.Horizontal.TProgressbar",
            troughcolor=self.config.theme.sidebar_bg,
            background=self.config.theme.button_bg,
            bordercolor=self.config.theme.sidebar_bg,
            lightcolor=self.config.theme.button_bg,
            darkcolor=self.config.theme.button_bg,
        )

    def _build_sidebar(self):
        """Create the left sidebar controls and labels."""

        layout = self.config.layout
        text = self.config.text
        theme = self.config.theme
        analysis = self.config.analysis

        self.sidebar = Frame(self.root, bg=theme.sidebar_bg)
        self.sidebar.place(x=0, y=0, width=theme.sidebar_width, height=theme.window_height)

        self.file_button = self._make_sidebar_button(text.open_file_button, layout.file_button_x, layout.file_button_y)
        self._make_label(text.sidebar_window_length, layout.window_label_y)
        self.window_box = self._make_combobox(analysis.window_length_options, analysis.default_window_index, layout.window_box_y)
        self._make_label(text.sidebar_kernel_size, layout.kernel_label_y)
        self.kernel_box = self._make_combobox(analysis.kernel_size_options, analysis.default_kernel_index, layout.kernel_box_y)
        self._make_label(text.sidebar_threshold, layout.threshold_label_y)
        self.threshold_box = self._make_combobox(analysis.threshold_options, analysis.default_threshold_index, layout.threshold_box_y)
        self.pitch_button = self._make_sidebar_button(text.pitch_button, layout.file_button_x, layout.pitch_button_y)

    def _make_sidebar_button(self, text, x, y):
        """Create a simple label-based button to avoid platform-specific native styling."""

        button = Label(
            self.sidebar,
            text=text,
            font=("segoe ui", 10),
            bg=self.config.theme.button_bg,
            fg=self.config.theme.button_fg,
            relief="solid",
            bd=1,
            highlightthickness=0,
            cursor="hand2",
            anchor="center",
        )
        button.place(x=x, y=y, width=self.config.layout.button_width, height=self.config.layout.button_height)
        button.bind("<Enter>", lambda event, widget=button: widget.configure(bg=self.config.theme.button_active_bg))
        button.bind("<Leave>", lambda event, widget=button: widget.configure(bg=self.config.theme.button_bg))
        return button

    def _make_label(self, text, y):
        """Create a sidebar field label."""

        label = Label(
            self.sidebar,
            text=text,
            font=("segoe ui", 10),
            bg=self.config.theme.sidebar_bg,
            fg=self.config.theme.label_fg,
        )
        label.place(x=self.config.layout.file_button_x, y=y, width=self.config.layout.label_width)
        return label

    def _make_combobox(self, values, current_index, y):
        """Create a readonly combobox in the sidebar."""

        box = Combobox(self.sidebar, style="Sidebar.TCombobox")
        box.configure(value=list(values), state="readonly")
        box.current(current_index)
        box.place(x=self.config.layout.file_button_x, y=y, width=self.config.layout.control_width)
        return box

    def _build_graphs(self):
        """Create the three main plots shown in the legacy interface."""

        self.graph_after = self.figure.add_subplot(311)
        self.graph_after.set_ylabel(self.config.text.graph_frequency_label)
        self.graph_after.set_xlabel(self.config.text.graph_time_label)
        self.graph_after.set_ylim(0, self.config.analysis.frequency_plot_limit)
        self.figure.tight_layout()

        self.graph_before = self.figure.add_subplot(312)
        self.graph_before.set_ylabel(self.config.text.graph_frequency_label)
        self.graph_before.set_xlabel(self.config.text.graph_time_label)
        self.graph_before.set_ylim(0, self.config.analysis.frequency_plot_limit)
        self.figure.tight_layout()

        self.graph_wave = self.figure.add_subplot(313)
        self.graph_wave.set_title(self.config.text.no_wave_file)
        self.graph_wave.set_ylabel(self.config.text.graph_amplitude_label)
        self.graph_wave.set_xlabel(self.config.text.graph_time_label)
        self.figure.tight_layout()

        self.canvas.get_tk_widget().place(
            x=self.config.theme.sidebar_width,
            y=0,
            width=self.config.theme.window_width - self.config.theme.sidebar_width,
            height=self.config.theme.window_height,
        )

    def bind_resize(self, callback):
        """Bind the root resize event."""

        self.root.bind("<Configure>", callback)

    def bind_file_open(self, callback):
        """Bind the Open file button."""

        self.file_button.bind("<Button-1>", callback)

    def bind_pitch_compute(self, callback):
        """Bind the Pitch contour button."""

        self.pitch_button.bind("<Button-1>", callback)

    def bind_canvas_motion(self, on_motion, on_leave):
        """Bind hover handlers for the waveform canvas widget."""

        self.canvas.get_tk_widget().bind("<Motion>", on_motion)
        self.canvas.get_tk_widget().bind("<Leave>", on_leave)

    def request_wave_file(self):
        """Open the native file picker for a `.wav` file."""

        return askopenfilename(filetypes=[("Wave file", ".wav")])

    def resize(self):
        """Keep the sidebar and canvas stretched to the current root size."""

        self.sidebar.place(x=0, y=0, width=self.config.theme.sidebar_width, height=self.root.winfo_height())
        self.canvas.get_tk_widget().place(
            x=self.config.theme.sidebar_width,
            y=0,
            width=self.root.winfo_width() - self.config.theme.sidebar_width,
            height=self.root.winfo_height(),
        )

    def read_controls(self):
        """Parse the three sidebar controls into primitive values."""

        return (
            int(self.window_box.get()[0:2]),
            int(self.kernel_box.get()),
            int(self.threshold_box.get()[0:2]) / 100,
        )

    def show_loader(self, message):
        """Render the inline loader in the sidebar."""

        if self.loader_frame is not None and self.loader_frame.winfo_exists():
            self.loader_frame.destroy()

        self.loader_frame = Frame(self.sidebar, bg=self.config.theme.sidebar_bg)
        self.loader_frame.place(
            x=self.config.layout.loader_x,
            y=self.config.layout.loader_y,
            width=self.config.layout.loader_width,
            height=self.config.layout.loader_height,
        )

        label = Label(
            self.loader_frame,
            text=message,
            font=("segoe ui", 10),
            bg=self.config.theme.sidebar_bg,
            fg=self.config.theme.label_fg,
            anchor="w",
        )
        label.place(x=0, y=0, width=self.config.layout.loader_width, height=20)

        progress_bar = Progressbar(self.loader_frame, mode="indeterminate", style="Loader.Horizontal.TProgressbar")
        progress_bar.place(x=0, y=self.config.layout.loader_bar_y, width=self.config.layout.loader_bar_width, height=10)
        progress_bar.start(10)
        self.loader_frame.progress_bar = progress_bar
        self.root.update_idletasks()

    def hide_loader(self):
        """Destroy the loader frame so it disappears completely."""

        if self.loader_frame is not None and self.loader_frame.winfo_exists():
            self.loader_frame.progress_bar.stop()
            self.loader_frame.destroy()
        self.loader_frame = None
        self.root.update_idletasks()

    def render_wave(self, audio_path, audio_data, audio_time, duration):
        """Redraw the waveform and reset contour plots after loading a file."""

        if self.scatter_after is not None:
            self.scatter_after.remove()
            self.scatter_after = None
        if self.scatter_before is not None:
            self.scatter_before.remove()
            self.scatter_before = None
        if self.wave_plot is not None:
            self.wave_plot.pop(0).remove()
            self.wave_plot = None

        self.graph_after.clear()
        self.graph_after.set_ylabel(self.config.text.graph_frequency_label)
        self.graph_after.set_xlabel(self.config.text.graph_time_label)
        self.graph_after.set_ylim(0, self.config.analysis.frequency_plot_limit)
        self.graph_after.set_xlim(0, duration)

        self.graph_before.clear()
        self.graph_before.set_ylabel(self.config.text.graph_frequency_label)
        self.graph_before.set_xlabel(self.config.text.graph_time_label)
        self.graph_before.set_ylim(0, self.config.analysis.frequency_plot_limit)
        self.graph_before.set_xlim(0, duration)

        self.graph_wave.clear()
        self.graph_wave.set_ylabel(self.config.text.graph_amplitude_label)
        self.graph_wave.set_xlabel(self.config.text.graph_time_label)
        self.graph_wave.set_xlim(0, duration)
        self.wave_plot = self.graph_wave.plot(audio_time, audio_data)
        self.graph_wave.set_title(
            self.config.text.waveform_title_template.format(
                name=audio_path,
                duration=duration,
            )
        )

    def render_pitch_contours(self, time_indexes, raw_frequencies, filtered_frequencies):
        """Redraw the before/after contour scatter plots."""

        if self.scatter_after is not None:
            self.scatter_after.remove()
            self.scatter_after = None
        if self.scatter_before is not None:
            self.scatter_before.remove()
            self.scatter_before = None

        if len(raw_frequencies) == 0:
            self.graph_before.set_title(self.config.text.nan_title.format(label="Before median filter"))
            self.graph_after.set_title(self.config.text.nan_title.format(label="After median filter"))
            return

        before_average = round(sum(raw_frequencies) / len(raw_frequencies), 3)
        after_average = round(sum(filtered_frequencies) / len(filtered_frequencies), 3)
        self.graph_before.set_title(self.config.text.before_filter_title.format(f0=before_average))
        self.graph_after.set_title(self.config.text.after_filter_title.format(f0=after_average))
        self.scatter_before = self.graph_before.scatter(time_indexes, raw_frequencies, color="black", marker="*", s=15)
        self.scatter_after = self.graph_after.scatter(time_indexes, filtered_frequencies, color="black", marker="*", s=15)

    def redraw_main_figure(self):
        """Flush the main Matplotlib figure to the Tk canvas."""

        self.figure.canvas.draw()

    def default_preview_position(self):
        """Compute the fixed preview location at the top-center of the content area."""

        top_gap = self.config.layout.preview_top_gap
        width = self.config.theme.preview_width
        height = self.config.theme.preview_height
        x = self.config.theme.sidebar_width + (self.root.winfo_width() - self.config.theme.sidebar_width - width) // 2
        y = top_gap
        if x < self.config.theme.sidebar_width:
            x = self.config.theme.sidebar_width
        if y + height > self.root.winfo_height():
            y = max(0, self.root.winfo_height() - height - top_gap)
        return width, height, x, y

    def pointer_inside_wave_graph(self):
        """Return `True` only while the real pointer is over the waveform subplot."""

        canvas_widget = self.canvas.get_tk_widget()
        pointer_root_x = self.root.winfo_pointerx()
        pointer_root_y = self.root.winfo_pointery()
        hovered_widget = self.root.winfo_containing(pointer_root_x, pointer_root_y)
        if hovered_widget is None:
            return False

        current_widget = hovered_widget
        while current_widget is not None and current_widget is not canvas_widget:
            current_widget = current_widget.master
        if current_widget is not canvas_widget:
            return False

        pointer_x = pointer_root_x - canvas_widget.winfo_rootx()
        pointer_y = pointer_root_y - canvas_widget.winfo_rooty()
        if pointer_x < 0 or pointer_y < 0:
            return False
        if pointer_x > canvas_widget.winfo_width() or pointer_y > canvas_widget.winfo_height():
            return False

        plot_y = canvas_widget.winfo_height() - pointer_y
        return self._point_inside_wave_axes(pointer_x, plot_y)

    def waveform_xdata_from_event(self, event):
        """Convert a raw Tk motion event into waveform-axis data coordinates."""

        canvas_widget = self.canvas.get_tk_widget()
        plot_x = event.x
        plot_y = canvas_widget.winfo_height() - event.y
        if self._point_inside_wave_axes(plot_x, plot_y) is False:
            return None
        xdata, _ = self.graph_wave.transData.inverted().transform((plot_x, plot_y))
        return xdata

    def waveform_xdata_from_pointer(self):
        """Convert the current pointer position into waveform-axis data coordinates."""

        if self.pointer_inside_wave_graph() is False:
            return None

        canvas_widget = self.canvas.get_tk_widget()
        pointer_root_x = self.root.winfo_pointerx()
        pointer_root_y = self.root.winfo_pointery()
        plot_x = pointer_root_x - canvas_widget.winfo_rootx()
        plot_y = canvas_widget.winfo_height() - (pointer_root_y - canvas_widget.winfo_rooty())
        xdata, _ = self.graph_wave.transData.inverted().transform((plot_x, plot_y))
        return xdata

    def _point_inside_wave_axes(self, plot_x, plot_y):
        """Return `True` only when the pointer is inside the actual waveform axes patch."""

        return self.graph_wave.patch.contains_point((plot_x, plot_y), radius=0)
