from numpy import round, real, array
from numpy.fft import fft, ifft


def autocorr(x):  # O(n^2)
    n = len(x)  # Lấy độ dài của tín hiệu x
    auto_corr = [0] * n  # Khởi tạo mảng để lưu kết quả và trả về
    delay = range(0, n)  # Sinh mảng delay
    for i in range(n):
        for j in range(n - delay[i]):
            auto_corr[i] += x[j] * x[j + delay[i]]  # Tự tương quan tại độ trễ delay[i]
    return round(auto_corr, 8)  # Trả về kết quả và làm tròn 8 chữ số thập phân


def fftautocorr(x):  # O(n * log(n))
    # Độ dài của y[n] = x[n] * h[n] theo công thức N * M - 1
    # Trong đó N, M lần lượt là độ dài của x và h
    n = 2 * len(x) - 1
    a = fft(x, n)  # Fast fourier tranform x[n]
    b = fft(x[::-1], n)  # Fast fourier tranform x[-n]
    c = ifft(a * b)  # Inverse fast fourier tranform
    return real(c[n // 2:])  # Trả về nữa cuối của mảng, chỉ lấy phần thực, bỏ đi phần ảo


def get_index_of_max_local(auto_corr, max_indexes):
    index = 0
    for i in range(1, len(max_indexes)):
        if auto_corr[max_indexes[i]] > auto_corr[max_indexes[index]]:
            index = i
    return index


def find_peaks(arr):
    size = len(arr)  # Lấy độ dài của mảng đầu vào
    index_peaks = []  # Lưu các index của các đỉnh
    index_tmp = 0  # Biến tạm để kiểm tra trường hợp đỉnh nằm ngang(có các giá trị liên tiếp bằng nhau) [1, 2, 5, 5, 5, 1]
    is_tmp = False  # Biến để kiểm tra trường hợp này [2, 2, 2, 1]
    
    # Ý tưởng: duyệt mảng từ 1 đến n-2
    # Tại phần tử đang xét so sánh với hai phần tử bên cạnh
    for i in range(1, size - 1, 1):
        if arr[i] > arr[i - 1] and arr[i] > arr[i + 1]:
            index_peaks.append(i)
        elif arr[i] > arr[i - 1] and arr[i] == arr[i + 1]:
            index_tmp = i
            is_tmp = True
        elif arr[i] == arr[i - 1] and arr[i] > arr[i + 1] and is_tmp is True:
            index_peaks.append(i)
            is_tmp = False
    return index_peaks  # Trả về index của các đỉnh trong mảng đầu vào


# get file name from path
def get_fine_name(path):
    index = path.rfind('/')
    return path[index + 1:]


# median filter
def median_filter(arr, kernel_size):
    if type(arr) is not list:
        arr = arr.tolist()  # Kiểm tra có phải kiểu dữ liệu "list" không

    length = len(arr)  # Lấy độ dài của mảng đầu vào
    part = (kernel_size - 1) // 2  # Tính số phần tử ở mỗi bên (trái, phải)
    med_arr = []  # Khởi tạo mảng mới để trả về kết quả

    for i in range(length):
        left = i - part
        right = i + part
        if left < 0:  # Trường hợp bên trái không đủ phần tử
            tmp = [0] * (0 - left) + arr[0:right + 1]  # Thêm phần tử 0 vào bên trái
        elif right >= length:  # Trường hợp bên phải không đủ phần tử
            tmp = arr[left:length] + [0] * (right - length + 1)  # Thêm phần tử 0 vào bên phải
        else:  # Trường hợp hai bên đều đủ
            tmp = arr[left: right + 1]
        tmp.sort()  # Sắp xếp tăng dần
        med_arr.append(tmp[part])  # Thêm vào mảng
    return array(med_arr)  # Trả về kết quả sau khi lọc


# calc all F0
def pitch_contour(data, duration, win_len, window, ham, ratio):
    F0s = []  # for save valid F0
    indexes = []  # for save index of window have valid F0
    index = 0  # for counter
    while index + window <= len(data):
        x = data[index:index + window]  # get current window
        x = x * ham  # smoothing window
        index += window // 2  # next window
        a_corr = fftautocorr(x)  # calc auto correlation
        threshold = a_corr[0] * ratio  # calc threshold = 30% maximum global

        # find top peaks, bottom peaks and check it
        max_indexes = find_peaks(a_corr)  # find top peaks
        min_indexes = find_peaks(-1 * a_corr)  # find bottom peaks
        if len(max_indexes) == 0 or len(min_indexes) == 0:
            continue

        # calc max_local, min_local and check it
        max_index = get_index_of_max_local(a_corr, max_indexes)  # get index of max_indexes
        max_local = a_corr[max_indexes[max_index]]
        min_local = a_corr[min_indexes[max_index]]
        if max_local < threshold or max_local - min_local < 0.01:
            continue

        # calc basic frequency and check it
        T0 = max_indexes[max_index] * win_len / window
        F0 = 1000 / T0
        if F0 > 350 or F0 < 75:
            continue

        # append F0 and index
        F0s.append(F0)
        indexes.append(index - window)

    # return tuple
    return F0s, indexes
