from tkinter import Tk, Frame, Label
from tkinter.ttk import Combobox, Style, Progressbar
from tkinter.filedialog import askopenfilename
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as Canvas
from matplotlib.pyplot import Figure
from scipy.io.wavfile import read
from function import get_fine_name, pitch_contour, median_filter, fftautocorr, find_peaks, get_index_of_max_local
from warnings import filterwarnings
from numpy import linspace, hamming
from threading import Thread

# ignore warnings
filterwarnings('ignore')

path = ''  # path of wave file
data = []  # amplitudes of wave file
duration = 0.0  # duration of wave file (second)
time = []  # vector time
win_len = 0  # duration of window (millisecond)
ker_size = 0  # size of median filter
ratio = 0.0  # percent of global maximum
window = 0  # number of samples per window (samples)
ham = []  # hamming window function
min_frame = 0  # frame at F0 = 75 Hz of window
max_frame = 0  # frame at F0 = 350 Hz of window
loader_frame = None
worker_thread = None
worker_kind = ''
worker_result = None
child_has_custom_position = False
pending_hover_frame = None
hover_render_job = None
child_visible = False
child_drag_offset_x = 0
child_drag_offset_y = 0
hover_hide_job = None
child_shadow = None
child_panel = None
child_canvas = None

SIDEBAR_WIDTH = 150
SIDEBAR_BG = '#efefef'
BUTTON_BG = '#0052cc'
BUTTON_ACTIVE_BG = '#0d66e5'
BUTTON_FG = '#ffffff'
LABEL_FG = '#222222'
INPUT_BG = '#ffffff'
INPUT_FG = '#222222'
CANVAS_BG = '#ffffff'
PANEL_BG = '#ffffff'
PANEL_HEADER_BG = '#1f2937'
PANEL_HEADER_FG = '#ffffff'
PANEL_BORDER = '#cbd5e1'
PANEL_SHADOW = '#d7dde7'
PANEL_SHADOW_PAD = 10


# handle event root resize
def root_resize(event):
    sidebar.place(x=0, y=0, width=SIDEBAR_WIDTH, height=root.winfo_height())
    canvas.get_tk_widget().place(x=SIDEBAR_WIDTH, y=0, width=root.winfo_width() - SIDEBAR_WIDTH, height=root.winfo_height())
    if child_visible is True and child_has_custom_position is False:
        place_child_panel_default()


# create window
root = Tk()
# screen size
WIDTH_SCREEN = root.winfo_screenwidth()
HEIGHT_SCREEN = root.winfo_screenheight()
# set title for window
root.title('Fundamental Frequency')
# window size
WIDTH = 1200
HEIGHT = 800
# set minimum size
root.wm_minsize(WIDTH, HEIGHT)
# set size and location for window
root.geometry("%dx%d+%d+%d" % (WIDTH, HEIGHT, (WIDTH_SCREEN - WIDTH) // 2, (HEIGHT_SCREEN - HEIGHT) // 2))
# add event resize
root.bind('<Configure>', root_resize)
root.configure(bg=SIDEBAR_BG)
root.tk_setPalette(
    background=SIDEBAR_BG,
    foreground=LABEL_FG,
    activeBackground=BUTTON_ACTIVE_BG,
    activeForeground=BUTTON_FG,
    highlightBackground=SIDEBAR_BG,
    selectBackground='#cfe3ff',
    selectForeground=LABEL_FG
)

style = Style(root)
style.theme_use('clam')
style.configure(
    'Sidebar.TCombobox',
    padding=2,
    fieldbackground=INPUT_BG,
    background=INPUT_BG,
    foreground=INPUT_FG,
    arrowcolor=INPUT_FG,
    bordercolor='#b8b8b8',
    lightcolor=INPUT_BG,
    darkcolor=INPUT_BG
)
style.map(
    'Sidebar.TCombobox',
    fieldbackground=[('readonly', INPUT_BG)],
    background=[('readonly', INPUT_BG)],
    foreground=[('readonly', INPUT_FG)],
    arrowcolor=[('readonly', INPUT_FG)]
)
style.configure(
    'Loader.Horizontal.TProgressbar',
    troughcolor=SIDEBAR_BG,
    background=BUTTON_BG,
    bordercolor=SIDEBAR_BG,
    lightcolor=BUTTON_BG,
    darkcolor=BUTTON_BG
)

sidebar = Frame(root, bg=SIDEBAR_BG)
sidebar.place(x=0, y=0, width=SIDEBAR_WIDTH, height=HEIGHT)


def make_sidebar_button(text, callback, x, y, width=100, height=28):
    button = Label(
        sidebar,
        text=text,
        font=('segoe ui', 10),
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        relief='solid',
        bd=1,
        highlightthickness=0,
        cursor='hand2',
        anchor='center'
    )
    button.place(x=x, y=y, width=width, height=height)
    button.bind('<Button-1>', callback)
    button.bind('<Enter>', lambda event, widget=button: widget.configure(bg=BUTTON_ACTIVE_BG))
    button.bind('<Leave>', lambda event, widget=button: widget.configure(bg=BUTTON_BG))
    return button


def show_wave():
    selected_path = askopenfilename(filetypes=[('Wave file', '.wav')])  # show open file dialog
    if selected_path == '':
        return

    start_loader('Loading file...')
    start_worker('wave', load_wave_data, selected_path)


def load_wave_data(selected_path):
    try:
        fs, loaded_data = read(selected_path)  # read wave file
        if len(loaded_data.shape) > 1:
            loaded_data = loaded_data.mean(axis=1)

        max_value = abs(loaded_data).max()
        if max_value != 0:
            loaded_data = loaded_data / max_value  # convert amplitude to [-1, 1]

        loaded_duration = len(loaded_data) / fs  # calc duration of wave file
        loaded_time = linspace(0, loaded_duration, len(loaded_data))
        set_worker_result(('success', selected_path, loaded_data, loaded_duration, loaded_time))
    except Exception:
        set_worker_result(('error',))


def apply_wave_data(selected_path, loaded_data, loaded_duration, loaded_time):
    global data, duration, time, path, scatter_1, scatter_2, plot_3, is_redraw
    path = selected_path
    data = loaded_data
    duration = loaded_duration
    time = loaded_time

    if scatter_1 is not None:
        scatter_1.remove()
        scatter_1 = None
    if scatter_2 is not None:
        scatter_2.remove()
        scatter_2 = None
    if plot_3 is not None:
        plot_3.pop(0).remove()
        plot_3 = None

    graph_1.clear()
    graph_1.set_ylabel('Frequency (Hz)')
    graph_1.set_xlabel('Time')
    graph_1.set_ylim(0, 400)
    graph_1.set_xlim(0, duration)

    graph_2.clear()
    graph_2.set_ylabel('Frequency (Hz)')
    graph_2.set_xlabel('Time')
    graph_2.set_ylim(0, 400)
    graph_2.set_xlim(0, duration)

    graph_3.clear()
    graph_3.set_ylabel('Amplitude')
    graph_3.set_xlabel('Time')
    graph_3.set_xlim(0, duration)
    plot_3 = graph_3.plot(time, data)
    graph_3.set_title(get_fine_name(path) + ', ' + str(round(duration, 2)) + '(s)')

    hide_child_window()
    is_redraw = True


# handle event file button
def file_btn_clicked(event):
    if is_loader is False:
        show_wave()


# add file button
file_btn = make_sidebar_button('Open file', file_btn_clicked, 10, 250)

# add window length label
win_len_label = Label(sidebar)
win_len_label.configure(text='Window length:', font=('segoe ui', 10), bg=SIDEBAR_BG, fg=LABEL_FG)
win_len_label.place(x=10, y=300, width=100)

# add window combobox
win_box = Combobox(sidebar, style='Sidebar.TCombobox')
win_box.configure(value=['10 ms', '20 ms', '30 ms', '40 ms', '50 ms', '60 ms'], state='readonly')
win_box.current(3)
win_box.place(x=10, y=320, width=100)

# add kernel size label
ker_size_label = Label(sidebar)
ker_size_label.configure(text='Kernel size:', font=('segoe ui', 10), bg=SIDEBAR_BG, fg=LABEL_FG)
ker_size_label.place(x=10, y=370, width=100)

# add kernel size combobox
ker_box = Combobox(sidebar, style='Sidebar.TCombobox')
ker_box.configure(value=[3, 5, 7, 9, 11, 13], state='readonly')
ker_box.current(1)
ker_box.place(x=10, y=390, width=100)

# add threshold label
hold_label = Label(sidebar)
hold_label.configure(text='Threshold:', font=('segoe ui', 10), bg=SIDEBAR_BG, fg=LABEL_FG)
hold_label.place(x=10, y=440, width=100)

# add threshold combobox
hold_box = Combobox(sidebar, style='Sidebar.TCombobox')
hold_box.configure(value=['30%', '50%', '70%'], state='readonly')
hold_box.current(0)
hold_box.place(x=10, y=460, width=100)


def show_pitch_contour():
    selected_win_len = int(win_box.get()[0:2])
    selected_ker_size = int(ker_box.get())
    selected_ratio = int(hold_box.get()[0:2]) / 100
    start_worker('pitch', compute_pitch_contour, selected_win_len, selected_ker_size, selected_ratio)


def compute_pitch_contour(selected_win_len, selected_ker_size, selected_ratio):
    try:
        computed_window = max(1, int(selected_win_len * len(data) / (duration * 1000)))
        computed_ham = hamming(computed_window)
        min_delay = 1000 / 350  # ms
        max_delay = 1000 / 75  # ms
        computed_min_frame = int(min_delay * computed_window / selected_win_len)
        computed_max_frame = int(max_delay * computed_window / selected_win_len)

        F0s, indexes = pitch_contour(
            data,
            selected_win_len,
            computed_window,
            computed_ham,
            selected_ratio,
            computed_min_frame,
            computed_max_frame
        )

        indexes = [index * duration / len(data) for index in indexes]
        set_worker_result(
            (
                'success',
                selected_win_len,
                selected_ker_size,
                selected_ratio,
                computed_window,
                computed_ham,
                computed_min_frame,
                computed_max_frame,
                F0s,
                indexes
            )
        )
    except Exception:
        set_worker_result(('error',))


def apply_pitch_contour(selected_win_len, selected_ker_size, selected_ratio, computed_window, computed_ham,
                        computed_min_frame, computed_max_frame, F0s, indexes):
    global scatter_1, scatter_2, is_redraw, win_len, ker_size, ratio, window, ham, min_frame, max_frame

    if scatter_1 is not None:
        scatter_1.remove()
        scatter_1 = None
    if scatter_2 is not None:
        scatter_2.remove()
        scatter_2 = None

    win_len = selected_win_len
    ker_size = selected_ker_size
    ratio = selected_ratio
    window = computed_window
    ham = computed_ham
    min_frame = computed_min_frame
    max_frame = computed_max_frame

    if len(F0s) == 0:
        graph_2.set_title('Before median filter, F0 = NaN')
        graph_1.set_title('After median filter, F0 = NaN')
        hide_child_window()
        is_redraw = True
        return

    avg_before = round(sum(F0s) / len(F0s), 3)
    graph_2.set_title('Before median filter, F0 = ' + str(avg_before))
    scatter_2 = graph_2.scatter(indexes, F0s, color='black', marker='*', s=15)

    filtered_F0s = median_filter(F0s, ker_size)
    avg_after = round(sum(filtered_F0s) / len(filtered_F0s), 3)
    graph_1.set_title('After median filter, F0 = ' + str(avg_after))
    scatter_1 = graph_1.scatter(indexes, filtered_F0s, color='black', marker='*', s=15)

    is_redraw = True


# handle event pitch button
def pitch_btn_clicked(event):
    if is_loader is False and duration != 0:
        start_loader('Processing...')
        show_pitch_contour()


# add pitch button
pitch_btn = make_sidebar_button('Pitch contour', pitch_btn_clicked, 10, 510)

is_loader = False


def start_loader(message):
    global is_loader, loader_frame
    is_loader = True
    if loader_frame is not None and loader_frame.winfo_exists():
        loader_frame.destroy()

    loader_frame = Frame(sidebar, bg=SIDEBAR_BG)
    loader_frame.place(x=10, y=548, width=130, height=34)

    loader_label = Label(loader_frame, text=message, font=('segoe ui', 10), bg=SIDEBAR_BG, fg=LABEL_FG, anchor='w')
    loader_label.place(x=0, y=0, width=130, height=20)

    loader_bar = Progressbar(loader_frame, mode='indeterminate', style='Loader.Horizontal.TProgressbar')
    loader_bar.place(x=0, y=24, width=80, height=10)
    loader_bar.start(10)

    loader_frame.loader_bar = loader_bar
    root.update_idletasks()


def stop_loader():
    global is_loader, loader_frame
    is_loader = False
    if loader_frame is not None and loader_frame.winfo_exists():
        loader_frame.loader_bar.stop()
        loader_frame.destroy()
    loader_frame = None
    root.update_idletasks()


def set_worker_result(result):
    global worker_result
    worker_result = result


def start_worker(kind, target, *args):
    global worker_thread, worker_kind, worker_result
    worker_kind = kind
    worker_result = None
    worker_thread = Thread(target=target, args=args, daemon=True)
    worker_thread.start()
    root.after(30, finish_worker_if_ready)


def finish_worker_if_ready():
    global worker_thread, worker_kind, worker_result
    if worker_thread is None:
        stop_loader()
        return

    if worker_thread.is_alive():
        root.after(30, finish_worker_if_ready)
        return

    result = worker_result
    completed_kind = worker_kind
    worker_thread = None
    worker_kind = ''
    worker_result = None

    try:
        if result is not None and result[0] == 'success':
            if completed_kind == 'wave':
                apply_wave_data(*result[1:])
            elif completed_kind == 'pitch':
                apply_pitch_contour(*result[1:])
    finally:
        stop_loader()

# create new figure
figure = Figure()
figure.patch.set_facecolor(CANVAS_BG)
is_redraw = False

# for before median filter
graph_1 = figure.add_subplot(311)
graph_1.set_ylabel('Frequency (Hz)')
graph_1.set_xlabel('Time')
graph_1.set_ylim(0, 400)
scatter_1 = None
figure.tight_layout()

# for after median filter
graph_2 = figure.add_subplot(312)
graph_2.set_ylabel('Frequency (Hz)')
graph_2.set_xlabel('Time')
graph_2.set_ylim(0, 400)
scatter_2 = None
figure.tight_layout()

# for wave file
graph_3 = figure.add_subplot(313)
graph_3.set_title('No wave file')
graph_3.set_ylabel('Amplitude')
graph_3.set_xlabel('Time')
plot_3 = None
figure.tight_layout()


# handle mouse events canvas
def hide_child_window(event=None):
    global pending_hover_frame, child_visible, hover_hide_job, child_shadow, child_panel, child_canvas
    pending_hover_frame = None
    if hover_render_job is not None:
        root.after_cancel(hover_render_job)
    clear_hover_job()
    if hover_hide_job is not None:
        root.after_cancel(hover_hide_job)
        hover_hide_job = None
    if child_canvas is not None and child_canvas.get_tk_widget().winfo_exists():
        child_canvas.get_tk_widget().destroy()
    if child_panel is not None and child_panel.winfo_exists():
        child_panel.destroy()
    if child_shadow is not None and child_shadow.winfo_exists():
        child_shadow.destroy()
    child_shadow = None
    child_panel = None
    child_canvas = None
    child_visible = False


def canvas_motion(event):
    global pending_hover_frame

    if window == 0 or duration == 0:
        return

    canvas_widget = canvas.get_tk_widget()
    mpl_x = event.x
    mpl_y = canvas_widget.winfo_height() - event.y

    if not graph_3.bbox.contains(mpl_x, mpl_y):
        hide_child_window()
        return

    xdata, _ = graph_3.transData.inverted().transform((mpl_x, mpl_y))
    if xdata < 0 or xdata > duration:
        hide_child_window()
        return

    show_child_window()

    center_frame = int(xdata * len(data) / duration)
    frame = center_frame - window // 2
    if frame < 0:
        frame = 0
    elif frame > len(data) - window:
        frame = len(data) - window

    pending_hover_frame = frame
    refresh_hover_hide_timer()
    schedule_child_render()


def schedule_child_render():
    global hover_render_job
    if hover_render_job is None:
        hover_render_job = root.after_idle(render_pending_child_fig)


def clear_hover_job():
    global hover_render_job
    hover_render_job = None


def pointer_inside_graph_3():
    if window == 0 or duration == 0:
        return False

    canvas_widget = canvas.get_tk_widget()
    pointer_root_x = root.winfo_pointerx()
    pointer_root_y = root.winfo_pointery()
    hovered_widget = root.winfo_containing(pointer_root_x, pointer_root_y)

    if hovered_widget is None:
        return False

    current = hovered_widget
    while current is not None and current is not canvas_widget:
        current = current.master
    if current is not canvas_widget:
        return False

    pointer_x = pointer_root_x - canvas_widget.winfo_rootx()
    pointer_y = pointer_root_y - canvas_widget.winfo_rooty()

    if pointer_x < 0 or pointer_y < 0:
        return False
    if pointer_x > canvas_widget.winfo_width() or pointer_y > canvas_widget.winfo_height():
        return False

    mpl_y = canvas_widget.winfo_height() - pointer_y
    return graph_3.bbox.contains(pointer_x, mpl_y)


def refresh_hover_hide_timer():
    global hover_hide_job
    if hover_hide_job is not None:
        root.after_cancel(hover_hide_job)
    hover_hide_job = root.after(120, hide_child_window)


# add figure
canvas = Canvas(figure, root)
canvas.get_tk_widget().place(x=SIDEBAR_WIDTH, y=0, width=WIDTH - SIDEBAR_WIDTH, height=HEIGHT)
canvas.get_tk_widget().bind('<Motion>', canvas_motion)
canvas.get_tk_widget().bind('<Leave>', hide_child_window)


def child_resize():
    if child_canvas is None or child_panel is None:
        return
    child_canvas.get_tk_widget().place(x=0, y=34, width=child_panel.winfo_width(), height=child_panel.winfo_height() - 34)


def start_child_drag(event):
    global child_drag_offset_x, child_drag_offset_y, child_has_custom_position
    child_drag_offset_x = event.x
    child_drag_offset_y = event.y
    child_has_custom_position = True


def drag_child_panel(event):
    if child_panel is None or child_shadow is None:
        return
    panel_width = child_panel.winfo_width()
    panel_height = child_panel.winfo_height()
    x = child_panel.winfo_x() + event.x - child_drag_offset_x
    y = child_panel.winfo_y() + event.y - child_drag_offset_y
    x = max(SIDEBAR_WIDTH, min(x, root.winfo_width() - panel_width))
    y = max(0, min(y, root.winfo_height() - panel_height))
    child_shadow.place(
        x=x - PANEL_SHADOW_PAD,
        y=y - PANEL_SHADOW_PAD,
        width=panel_width + PANEL_SHADOW_PAD * 2,
        height=panel_height + PANEL_SHADOW_PAD * 2
    )
    child_panel.place(x=x, y=y, width=panel_width, height=panel_height)


def create_child_panel():
    global child_shadow, child_panel, child_canvas
    child_shadow = Frame(root, bg=PANEL_SHADOW, bd=0, highlightthickness=0)
    child_panel = Frame(root, bg=PANEL_BG, highlightbackground=PANEL_BORDER, highlightthickness=1, bd=0)
    child_header = Frame(child_panel, bg=PANEL_HEADER_BG, height=34)
    child_header.place(x=0, y=0, relwidth=1)
    child_title = Label(child_header, text='Window Details', font=('segoe ui', 11, 'bold'),
                        bg=PANEL_HEADER_BG, fg=PANEL_HEADER_FG)
    child_title.place(relx=0.5, x=-90, y=6, width=180, height=22)
    child_canvas = Canvas(child_figure, child_panel)
    child_header.bind('<ButtonPress-1>', start_child_drag)
    child_header.bind('<B1-Motion>', drag_child_panel)
    child_title.bind('<ButtonPress-1>', start_child_drag)
    child_title.bind('<B1-Motion>', drag_child_panel)

# child figure
child_figure = Figure(constrained_layout=True)
child_figure.patch.set_facecolor(CANVAS_BG)

child_graph_1 = child_figure.add_subplot(211)
child_graph_2 = child_figure.add_subplot(212)


def get_default_child_position():
    child_width = 500
    child_height = 500
    top_gap = 0
    x = SIDEBAR_WIDTH + (root.winfo_width() - SIDEBAR_WIDTH - child_width) // 2
    y = top_gap
    if x < SIDEBAR_WIDTH:
        x = SIDEBAR_WIDTH
    if y + child_height > root.winfo_height():
        y = max(0, root.winfo_height() - child_height - top_gap)
    return child_width, child_height, x, y


def place_child_panel_default():
    if child_panel is None or child_shadow is None:
        create_child_panel()
    child_width, child_height, x, y = get_default_child_position()
    child_shadow.place(
        x=x - PANEL_SHADOW_PAD,
        y=y - PANEL_SHADOW_PAD,
        width=child_width + PANEL_SHADOW_PAD * 2,
        height=child_height + PANEL_SHADOW_PAD * 2
    )
    child_panel.place(x=x, y=y, width=child_width, height=child_height)
    child_resize()


def show_child_window():
    global child_visible
    if child_panel is None or child_shadow is None or child_canvas is None:
        create_child_panel()
    if child_visible is False:
        if child_has_custom_position is False:
            place_child_panel_default()
        else:
            child_shadow.place(
                x=child_panel.winfo_x() - PANEL_SHADOW_PAD,
                y=child_panel.winfo_y() - PANEL_SHADOW_PAD,
                width=child_panel.winfo_width() + PANEL_SHADOW_PAD * 2,
                height=child_panel.winfo_height() + PANEL_SHADOW_PAD * 2
            )
            child_panel.place(x=child_panel.winfo_x(), y=child_panel.winfo_y(),
                              width=child_panel.winfo_width(), height=child_panel.winfo_height())
            child_resize()
        child_visible = True
    child_shadow.lift()
    child_panel.lift()
    child_panel.update_idletasks()


def render_pending_child_fig():
    global hover_render_job, pending_hover_frame
    hover_render_job = None
    if pending_hover_frame is None or child_visible is False:
        return
    update_child_fig(pending_hover_frame)


def update_child_fig(frame):
    global child_graph_1, child_graph_2
    w = data[frame:frame + window] * ham
    a = fftautocorr(w)
    threshold = a[0] * ratio
    is_periodicity = True
    hover_time = frame * duration / len(data)

    child_figure.clear()
    child_graph_1 = child_figure.add_subplot(211)
    child_graph_2 = child_figure.add_subplot(212)
    child_graph_1.set_title('Window at %.3f s' % hover_time)
    child_graph_1.set_xlabel('Sample')
    child_graph_1.set_ylabel('Amplitude')
    child_graph_2.set_xlabel('Delay')
    child_graph_2.set_ylabel('Auto correlation')

    # plot original window
    child_graph_1.set_xlim(-20, window)
    child_graph_1.set_ylim(w.min(), w.max())
    child_plot_1 = child_graph_1.plot(w, color='blue')

    # plot auto correlation window
    child_graph_2.set_xlim(-20, window)
    child_graph_2.set_ylim(a.min(), a.max())
    child_graph_2.set_title('Not periodicity, F0 = NaN')
    child_plot_2 = child_graph_2.plot(a, color='blue')  # plot autocorr
    child_h_line_2 = child_graph_2.hlines(threshold, -20, window, color='orange', linestyles='--')  # draw threshold line
    # draw limit delay window
    child_left_v_line_2 = child_graph_2.vlines(min_frame, a.min(), a.max(), color='green')
    child_right_v_line_2 = child_graph_2.vlines(max_frame, a.min(), a.max(), color='green')

    max_indexes = find_peaks(a, min_frame, max_frame)
    min_indexes = find_peaks(-1 * a, min_frame, max_frame)
    if len(max_indexes) == 0 or len(min_indexes) == 0:
        is_periodicity = False

    if is_periodicity is True:
        max_index = get_index_of_max_local(a, max_indexes)
        max_local = a[max_indexes[max_index]]
        min_local = a[min_indexes[max_index]]
        if max_local < threshold or max_local - min_local < 0.01:
            is_periodicity = False

    if is_periodicity is True:
        T0 = max_indexes[max_index] * win_len / window
        F0 = 1000 / T0
        if F0 > 350 or F0 < 75:
            child_graph_2.set_title('Periodicity, out F0 = ' + str(round(F0, 3)))
            is_periodicity = False

    if is_periodicity is True:
        child_graph_2.set_title('Periodicity, F0 = ' + str(round(F0, 3)))
        child_graph_2.scatter(max_indexes[max_index], max_local, color='red')

    child_canvas.draw()
    child_panel.update_idletasks()


# handle root update
def root_update(index):
    global is_redraw

    if index == 8:
        index = 0

    if child_visible is True and pointer_inside_graph_3() is False:
        hide_child_window()

    if is_redraw is True:
        figure.canvas.draw()
        is_redraw = False

    root.after(60, root_update, index + 1)


root.after(0, root_update, 0)  # start update root
root.mainloop()  # start show window
