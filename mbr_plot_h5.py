#! /usr/bin/env python3

import h5py
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timezone, timedelta
import argparse
import sys
from scipy.signal import decimate

def decimate_signal(timestamps, pressures, q=10):
    """
    Децимирует сигнал (снижает частоту дискретизации в q раз).
    
    Параметры:
    - timestamps: массив времён (Unix-время)
    - pressures: массив значений давления
    - q: коэффициент децимации (целое > 1)
    
    Возвращает:
    - dec_timestamps: децимированные времена
    - dec_pressures: децимированные значения давления
    """
    if q <= 1:
        return timestamps, pressures  # без изменений
    
    # Децимируем давление
    dec_pressures = decimate(pressures, q, zero_phase=True)
    
    # Выбираем соответствующие временные метки (каждую q‑ю)
    dec_indices = np.arange(0, len(timestamps), q)
    dec_timestamps = timestamps[dec_indices]
    
    # Если длины не совпали (из‑за особенностей decimate), обрезаем
    if len(dec_timestamps) > len(dec_pressures):
        dec_timestamps = dec_timestamps[:len(dec_pressures)]
    elif len(dec_timestamps) < len(dec_pressures):
        dec_pressures = dec_pressures[:len(dec_timestamps)]
    
    return dec_timestamps, dec_pressures

def load_pressure_data(h5_filename, dataset_name='pressure_series'):
    """Читает данные давления из HDF5-файла."""
    with h5py.File(h5_filename, 'r') as h5file:
        dataset = h5file[dataset_name]
        data = dataset[:]
        timestamps = data[:, 0]
        pressures = data[:, 1]
    return timestamps, pressures

def plot_pressure_time_series(timestamps, pressures, title="Временной ряд давления", figsize=(10, 6)):
    """Строит график давления во времени."""
    dt_times = [datetime.fromtimestamp(ts, tz=timezone.utc).astimezone() for ts in timestamps]
    
    # Определяем полночь дня первой точки
    first_date = dt_times[0].date()
    midnight = datetime.combine(first_date, datetime.min.time()).replace(tzinfo=dt_times[0].tzinfo)

    plt.figure(figsize=figsize)
    plt.plot(dt_times, pressures, marker='.', linestyle='-', color='tab:blue', alpha=0.7)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel("Время", fontsize=12)
    plt.ylabel("Давление, Па", fontsize=12)
    plt.grid(True, alpha=0.3)

     # Фиксируем масштаб оси X: 0–24 часа
    plt.xlim(midnight, midnight+timedelta(days=1))


    plt.tight_layout()
    plt.show()

def main():
    # Настройка парсера аргументов
    parser = argparse.ArgumentParser(
        description="Визуализация временного ряда давления из HDF5-файла."
    )
    parser.add_argument(
        'filename',
        type=str,
        help='Путь к HDF5-файлу (например, pressure_data.h5)'
    )
    parser.add_argument(
        '-d', '--dataset',
        type=str,
        default='pressure_series',
        help='Имя dataset в файле (по умолчанию: pressure_series)'
    )
    parser.add_argument(
        '-t', '--title',
        type=str,
        default='Временной ряд давления',
        help='Заголовок графика (по умолчанию: "Временной ряд давления")'
    )
    parser.add_argument(
        '-q', '--decimation',
        type=int,
        default=10,
        help='Коэффициент децимации (q > 1; по умолчанию: 10)'
    )

    # Разбор аргументов
    args = parser.parse_args()

    h5_filename = args.filename
    dataset_name = args.dataset
    title = args.title
    q = args.decimation

    if q < 1:
        print("Ошибка: коэффициент децимации q должен быть ≥ 1.", file=sys.stderr)
        sys.exit(1)

    # 1. Загружаем данные
    try:
        timestamps, pressures = load_pressure_data(h5_filename, dataset_name)
        print(f"Загружено {len(timestamps)} точек данных из '{h5_filename}'.")
    except FileNotFoundError:
        print(f"Ошибка: файл '{h5_filename}' не найден.", file=sys.stderr)
        sys.exit(1)
    except KeyError:
        print(f"Ошибка: dataset '{dataset_name}' не найден в файле '{h5_filename}'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Децимация с коэффициентом q={q}...")
    timestamps, pressures = decimate_signal(timestamps, pressures, q)
    print(f"После децимации: {len(timestamps)} точек.") 

    # 2. Выводим статистику
    print(f"Период: {datetime.fromtimestamp(timestamps[0], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} "
          f"— {datetime.fromtimestamp(timestamps[-1], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Мин. давление: {pressures.min():.1f} Па")
    print(f"Макс. давление: {pressures.max():.1f} Па")
    print(f"Ср. давление: {pressures.mean():.1f} Па")

    # 3. Строим график
    plot_pressure_time_series(
        timestamps,
        pressures,
        title=f"{title}\nФайл: {h5_filename}",
        figsize=(12, 7)
    )

if __name__ == '__main__':
    main()
