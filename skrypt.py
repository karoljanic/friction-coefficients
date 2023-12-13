# Script for finding force impulses in datastream
# Karol Janic
# December 2023

import matplotlib.pyplot as plt
import os


def calculate_std_dev(_data):
    """Calculates standard deviation"""

    if len(_data) == 0:
        return float('inf')

    mean = sum(_data) / len(_data)
    sum_squared_diff = sum((x - mean) ** 2 for x in _data)
    std_dev = (sum_squared_diff / len(_data)) ** 0.5

    return std_dev


def remove_outliers(_impulses, _max_std_dev):
    """Removes outliers from impulses"""

    if len(_impulses) < 2:
        return _impulses

    _std_dev = calculate_std_dev([_impulse[1] for _impulse in _impulses])
    while _std_dev > _max_std_dev and len(_impulses) > 2:
        _impulses = _impulses[1:-1]
        _std_dev = calculate_std_dev([_impulse[1] for _impulse in _impulses])

    return _impulses


def read_data(_filename):
    """Reads data from file"""

    with open(_filename) as f:
        _lines = [line.replace(',', '.') for line in f.readlines()[2:]]
        _times = [float(line.split()[0]) for line in _lines]
        _forces = [float(line.split()[1]) for line in _lines]

    return _times, _forces


def divide_into_components(_times, _forces, _baseline, _min_meantime):
    """Divides forces into components"""

    _sign_changes = [0]
    for _force_index in range(len(_forces) - 1):
        if _forces[_force_index] < baseline < _forces[_force_index + 1]:
            if (_times[_force_index] - _sign_changes[-1]) > _min_meantime:
                _sign_changes.append((_times[_force_index] + _times[_force_index + 1]) / 2)
        elif _forces[_force_index] > baseline > _forces[_force_index + 1]:
            if (_times[_force_index] - _sign_changes[-1]) > _min_meantime:
                _sign_changes.append((_times[_force_index] + _times[_force_index + 1]) / 2)
        else:
            pass

    _sign_changes = _sign_changes[1:]

    _components = []
    for _sign_change_index in range(len(_sign_changes) - 1):
        _begin, _end = _sign_changes[_sign_change_index], _sign_changes[_sign_change_index + 1]
        _component = [index for index in range(len(_times)) if _begin <= _times[index] <= _end]
        _components.append([[_times[index], _forces[index], index] for index in _component])

    return _sign_changes, _components


def find_extremes(_components):
    """Finds extremes in components"""

    _minimums, _maximums = [], []
    for _component in _components:
        _min = min(_component, key=lambda x: x[1])
        _max = max(_component, key=lambda x: x[1])

        if _min[1] < 0 and abs(_min[1]) > abs(_max[1]):
            _minimums.append(_min)
        if _max[1] > 0 and abs(_max[1]) > abs(_min[1]):
            _maximums.append(_max)

    return _minimums, _maximums


def find_impulses(_times, _forces, _minimums, _maximums, _max_std_dev):
    """Finds impulses"""

    _positive_impulses = []
    for _time, _force, _index in _maximums:
        _decline_index = _index + 1
        while (_forces[_decline_index + 1] < _forces[_decline_index] or
               abs(_forces[_decline_index + 1] - _forces[_decline_index]) < 0.01):
            _decline_index += 1

        _increase_index = _decline_index + 1
        _impulses = []
        while _forces[_increase_index] > _forces[_decline_index]:
            _impulses.append([_times[_increase_index], _forces[_increase_index]])
            _increase_index += 1

        _impulses = remove_outliers(_impulses, _max_std_dev)
        _positive_impulses.append(_impulses)

    return _positive_impulses


def plot_data(_times, _forces, _plot_interval_size, _baseline, _impulses,
              _minimums, _maximums, _positive_impulses):
    """Plots data"""

    for index in range((len(_times) // _plot_interval_size) + 1):
        plt.clf()
        begin = index * _plot_interval_size
        end = min((index + 1) * _plot_interval_size, len(_times) - 1)
        plt.plot(_times[begin:end], _forces[begin:end])

        for x in _impulses:
            if _times[begin] <= x <= _times[end]:
                plt.axvline(x=x, color='g', linestyle='--')

        plt.scatter([minimum[0] for minimum in _minimums if _times[begin] <= minimum[0] <= _times[end]],
                    [minimum[1] for minimum in _minimums if _times[begin] <= minimum[0] <= _times[end]],
                    color='r', s=20)

        plt.scatter([maximum[0] for maximum in _maximums if _times[begin] <= maximum[0] <= _times[end]],
                    [maximum[1] for maximum in _maximums if _times[begin] <= maximum[0] <= _times[end]],
                    color='r', s=20)

        _fpi = [element for sublist in _positive_impulses for element in sublist]    # _flatten_positive_impulses

        plt.scatter([_fpi[0] for _fpi in _fpi if _times[begin] <= _fpi[0] <= _times[end]],
                    [_fpi[1] for _fpi in _fpi if _times[begin] <= _fpi[0] <= _times[end]],
                    color='cyan', s=20)

        plt.axhline(y=_baseline, color='r')

        plt.xlabel('Time [s]')
        plt.ylabel('Force [N]')
        plt.savefig(f'plots/plot{index}.png')


if __name__ == '__main__':
    times, forces = read_data('dane.txt')
    baseline = 0.0
    plot_interval_size = 200
    min_meantime = 0.300
    max_std_dev = 0.05

    sign_changes, components = divide_into_components(times, forces, baseline, min_meantime)
    minimums, maximums = find_extremes(components)
    positive_impulses = find_impulses(times, forces, minimums, maximums, max_std_dev)

    if not os.path.exists('plots'):
        os.makedirs('plots')

    plot_data(times, forces, plot_interval_size, baseline, sign_changes,
              minimums, maximums, positive_impulses)
