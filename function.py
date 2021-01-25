from numpy import round, real, array
from numpy.fft import fft, ifft


def autocorr(x):  # O(n^2)
    n = len(x)  # get length x
    auto_corr = [0] * n  # for save auto correlation
    delay = range(0, n)  # delay arr
    for i in delay:
        for j in range(n - delay[i]):
            auto_corr[i] += x[j] * x[j + delay[i]]  # auto correlation at delay[i]
    return round(auto_corr, 8)


def fftautocorr(x):  # O(n * log(n))
    # length of y[n] = x[n] * h[n] calc: N * M - 1
    # in N is length x, M is length h
    n = 2 * len(x) - 1
    a = fft(x, n)  # Fast fourier transform x[n]
    b = fft(x[::-1], n)  # Fast fourier transform x[-n]
    c = ifft(a * b)  # Inverse fast fourier transform
    return real(c[n // 2:])  # return the last half of arr, only get real


def find_peaks(arr, min_frame, max_frame):
    index_peaks = []  # for save all index of maximum local
    index_tmp = 0  # for check case [1, 2, 5, 5, 5, 1]
    is_tmp = False  # for check case [2, 2, 2, 1]

    # idea: browse arr from min_frame to max_frame
    # at the element being compared with two adjacent elements
    for i in range(min_frame, max_frame):
        if arr[i] > arr[i - 1] and arr[i] > arr[i + 1]:
            index_peaks.append(i)
        elif arr[i] > arr[i - 1] and arr[i] == arr[i + 1]:
            index_tmp = i
            is_tmp = True
        elif arr[i] == arr[i - 1] and arr[i] > arr[i + 1] and is_tmp is True:
            index_peaks.append(i)
            is_tmp = False
    return index_peaks  # return all index of maximum local


# get file name from path
def get_fine_name(path):
    index = path.rfind('/')
    return path[index + 1:]


# median filter
def median_filter(arr, kernel_size):
    if type(arr) is not list:
        arr = arr.tolist()  # check data type "list"

    length = len(arr)  # get length of input array
    part = (kernel_size - 1) // 2  # calc number of elements at (left, right) side
    med_arr = []  # array after median filter

    for i in range(length):
        left = i - part
        right = i + part
        if left < 0:  # out of index at left side
            tmp = [0] * (0 - left) + arr[0:right + 1]  # add 0 element to left side
        elif right >= length:  # out of index at right side
            tmp = arr[left:length] + [0] * (right - length + 1)  # add 0 element to right side
        else:
            tmp = arr[left: right + 1]
        tmp.sort()  # sort up ascending
        med_arr.append(tmp[part])  # add element after filter
    return array(med_arr)


# calc all F0
def pitch_contour(data, win_len, window, ham, ratio, min_frame, max_frame):
    F0s = []  # for save valid F0
    indexes = []  # for save index of window have valid F0
    index = 0  # for counter
    while index + window <= len(data):
        w = data[index:index + window]  # get current window
        w = w * ham  # smoothing window
        index += window // 2  # next window
        a_corr = fftautocorr(w)  # calc auto correlation
        threshold = a_corr[0] * ratio  # calc threshold = n% maximum global

        # find top peaks, bottom peaks and check it
        max_indexes = find_peaks(a_corr, min_frame, max_frame)  # find top peaks
        min_indexes = find_peaks(-1 * a_corr, 0, len(a_corr) - 1)  # find bottom peaks
        if len(max_indexes) == 0 or len(min_indexes) == 0:
            continue

        # calc max_local, min_local and check it
        max_index = get_index_of_max_local(a_corr, max_indexes)  # get index of max_indexes
        max_local = a_corr[max_indexes[max_index]]
        min_local = a_corr[min_indexes[max_index]]
        if max_local < threshold or max_local - min_local < 0.02:
            continue

        # calc basic frequency and check it
        T0 = max_indexes[max_index] * win_len / window
        F0 = 1000 / T0

        # append F0 and index
        F0s.append(F0)
        indexes.append(index - window)

    # return tuple
    return F0s, indexes


def get_index_of_max_local(auto_corr, max_indexes):
    index = 0
    for i in range(1, len(max_indexes)):
        if auto_corr[max_indexes[i]] > auto_corr[max_indexes[index]]:
            index = i
    return index
