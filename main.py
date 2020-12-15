from tkinter import Tk, Button, PhotoImage, Toplevel
from tkinter.ttk import Combobox, Label
from tkinter.filedialog import askopenfilename
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as Canvas
from matplotlib.pyplot import Figure
from scipy.io.wavfile import read
from function import get_fine_name, pitch_contour, median_filter, fftautocorr, autocorr, find_peaks, get_index_of_max_local
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


# handle event root resize
def root_resize(event):
    canvas.get_tk_widget().place(x=150, y=0, width=root.winfo_width() - 150, height=root.winfo_height())
    child.geometry('%ix%i+%i+%i' % (500, 500, root.winfo_x() + (root.winfo_width() - 500) // 2, root.winfo_y()))


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


def show_wave():
    global data, duration, time, path, scatter_1, scatter_2, plot_3, is_loader, is_redraw  # set global vars
    path = askopenfilename(filetypes=[('Wave file', '.wav')])  # show open file dialog
    if path == '':
        loader.place_forget()
        is_loader = False
        return

    fs, data = read(path)  # read wave file
    data = data / data.max()  # convert amplitude to [-1, 1]
    duration = len(data) / fs  # calc duration of wave file
    time = linspace(0, duration, len(data))

    # update figure
    if scatter_1 is not None:
        scatter_1.remove()
        scatter_1 = None
    if scatter_2 is not None:
        scatter_2.remove()
        scatter_2 = None
    if plot_3 is not None:
        plot_3.pop(0).remove()
        plot_3 = None

    # set x
    graph_1.set_xlim(0, duration)
    graph_2.set_xlim(0, duration)
    graph_3.set_xlim(0, duration)

    plot_3 = graph_3.plot(time, data)  # new plot
    graph_3.set_title(get_fine_name(path) + ', ' + str(round(duration, 2)) + '(s)')  # set name wave file

    loader.place_forget()
    is_loader = False
    is_redraw = True


# handle event file button
def file_btn_clicked(event):
    global is_loader
    if is_loader is False:
        loader.place(x=120, y=445)
        is_loader = True
        Thread(target=show_wave).start()


# add file button
file_btn = Button(root)
file_btn.configure(text='Open file', font=('segoe ui', 10), bg='#0052cc', fg='#ffffff')
file_btn.bind('<Button-1>', file_btn_clicked)
file_btn.place(x=10, y=250, width=100)

# add window length label
win_len_label = Label(root)
win_len_label.configure(text='Window length:', font=('segoe ui', 10))
win_len_label.place(x=10, y=300, width=100)

# add window combobox
win_box = Combobox(root)
win_box.configure(value=['10 ms', '20 ms', '30 ms', '40 ms', '50 ms', '60 ms'], state='readonly')
win_box.current(3)
win_box.place(x=10, y=320, width=100)

# add kernel size label
ker_size_label = Label(root)
ker_size_label.configure(text='Kernel size:', font=('segoe ui', 10))
ker_size_label.place(x=10, y=370, width=100)

# add kernel size combobox
ker_box = Combobox(root)
ker_box.configure(value=[3, 5, 7, 9, 11, 13], state='readonly')
ker_box.current(1)
ker_box.place(x=10, y=390, width=100)

# add threshold label
hold_label = Label(root)
hold_label.configure(text='Threshold:', font=('segoe ui', 10))
hold_label.place(x=10, y=440, width=100)

# add threshold combobox
hold_box = Combobox(root)
hold_box.configure(value=['30%', '50%', '70%'], state='readonly')
hold_box.current(0)
hold_box.place(x=10, y=460, width=100)


def show_pitch_contour():
    global scatter_1, scatter_2, is_loader, is_redraw, win_len, ker_size, ratio, window, ham, min_frame, max_frame
    # update figure
    if scatter_1 is not None:
        scatter_1.remove()
        scatter_1 = None
    if scatter_2 is not None:
        scatter_2.remove()
        scatter_2 = None

    # get data from user
    win_len = int(win_box.get()[0:2])
    ker_size = int(ker_box.get())
    ratio = int(hold_box.get()[0:2]) / 100

    # calc params
    window = int((win_len * len(data) / (duration * 1000)))
    ham = hamming(window)
    min_delay = 1000 / 350  # ms
    max_delay = 1000 / 75  # ms
    min_frame = int(min_delay * window / win_len)
    max_frame = int(max_delay * window / win_len)

    # pitch contour to find basic frequency
    F0s, indexes = pitch_contour(data, win_len, window, ham, ratio, min_frame, max_frame)

    # convert samples to time
    for i in range(len(indexes)):
        indexes[i] *= duration / len(data)

    # scatter before median filter
    graph_2.set_title('Before median filter, F0 = ' + str(round(sum(F0s) / len(F0s), 3)))
    scatter_2 = graph_2.scatter(indexes, F0s, color='black', marker='*', s=15)

    # scatter after median filter
    F0s = median_filter(F0s, ker_size)
    graph_1.set_title('After median filter, F0 = ' + str(round(sum(F0s) / len(F0s), 3)))
    scatter_1 = graph_1.scatter(indexes, F0s, color='black', marker='*', s=15)

    loader.place_forget()
    is_loader = False
    is_redraw = True


# handle event pitch button
def pitch_btn_clicked(event):
    global is_loader
    if is_loader is False and duration != 0:
        loader.place(x=120, y=515)
        is_loader = True
        Thread(target=show_pitch_contour).start()


# add pitch button
pitch_btn = Button(root)
pitch_btn.configure(text='Pitch contour', font=('segoe ui', 10), bg='#0052cc', fg='#ffffff')
pitch_btn.bind('<Button-1>', pitch_btn_clicked)
pitch_btn.place(x=10, y=510, width=100)

# add loader icon
frames = [PhotoImage(file='./image/loader.gif', format='gif -index %i' % i) for i in range(8)]
loader = Label(root)
is_loader = False

# create new figure
figure = Figure()
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
def axes_moved(event):
    if window != 0 and duration != 0 and event.inaxes == graph_3:
        child.deiconify()

        bbox = graph_3.get_window_extent().transformed(figure.dpi_scale_trans.inverted())
        width = int(bbox.width * figure.dpi)
        x0 = bbox.x0 * figure.dpi + 1

        frame = (event.x - x0) * len(data) // width
        if frame < 0:
            frame = 0
        elif frame > len(data) - window:
            frame = len(data) - window

        update_child_fig(int(frame))


# add figure
canvas = Canvas(figure, root)
canvas.mpl_connect('motion_notify_event', axes_moved)
canvas.get_tk_widget().place(x=150, y=0, width=WIDTH - 150, height=HEIGHT)


# handle child resize
def child_resize(event):
    child_canvas.get_tk_widget().place(x=0, y=0, width=child.winfo_width(), height=child.winfo_height())


# child tk for show window
child = Toplevel(root)
child.protocol('WM_DELETE_WINDOW', lambda: child.withdraw())
child.bind('<Configure>', child_resize)
child.withdraw()

# child figure
child_figure = Figure()

child_graph_1 = child_figure.add_subplot(211)
child_plot_1 = None
child_figure.tight_layout()

child_graph_2 = child_figure.add_subplot(212)
child_plot_2 = None
child_v_line_2 = None
child_left_line_2 = None
child_right_line_2 = None
child_scatter_2 = None
child_figure.tight_layout()


def update_child_fig(frame):
    global child_plot_1, child_plot_2, child_h_line_2, child_scatter_2, child_left_v_line_2, child_right_v_line_2
    w = data[frame:frame + window] * ham
    a = fftautocorr(w)
    threshold = a[0] * ratio
    is_periodicity = True

    # remove all old plot
    if child_plot_1 is not None:
        child_plot_1.pop(0).remove()
        child_plot_1 = None
        child_plot_2.pop(0).remove()
        child_plot_2 = None
        child_h_line_2.remove()
        child_h_line_2 = None
        child_left_v_line_2.remove()
        child_left_v_line_2 = None
        child_right_v_line_2.remove()
        child_right_v_line_2 = None
    if child_scatter_2 is not None:
        child_scatter_2.remove()
        child_scatter_2 = None

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
        child_scatter_2 = child_graph_2.scatter(max_indexes[max_index], max_local, color='red')

    child_figure.canvas.draw()


# child canvas
child_canvas = Canvas(child_figure, child)


# handle root update
def root_update(index):
    global is_redraw

    if index == 8:
        index = 0
    loader.configure(image=frames[index])

    if is_redraw is True:
        figure.canvas.draw()
        is_redraw = False

    root.after(60, root_update, index + 1)


root.after(0, root_update, 0)  # start update root
root.mainloop()  # start show window
