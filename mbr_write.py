#! /usr/bin/env python3

"""Пример использования библиотеки."""

import h5py
import numpy as np
from lcomp.device import e140
from lcomp.ioctl import (L_ASYNC, L_DEVICE, L_EVENT, L_PARAM, L_STREAM, L_USER_BASE,
                         WASYNC_PAR, WDAQ_PAR)
from lcomp.lcomp import LCOMP
import time as tm
import datetime
from multiprocessing import Process
import ctypes

def create_pressure_dataset(h5_filename, dataset_name='pressure_series'):
    """
    Создаёт HDF5-файл с dataset для временной серии давления.
    """
    with h5py.File(h5_filename, 'w') as h5file:
        h5file.create_dataset(
            dataset_name,
            shape=(0, 2),
            maxshape=(None, 2),
            dtype=np.float64,
            chunks=(600*20,2), #True,
            compression='gzip'
        )
        h5file[dataset_name].attrs['units'] = 'seconds, Pa'
        h5file[dataset_name].attrs['columns'] = ['timestamp', 'pressure']
        h5file[dataset_name].attrs['created'] = datetime.datetime.now().isoformat()
    print(h5_filename, ' created')

def add_pressure_array(h5_filename, time=None, p=None, dataset_name='pressure_series'):
    """
    Добавляет массив данных (N, 2) в HDF5-файл.
    
    Параметры:
    - h5_filename: имя файла
    - dataset_name: имя dataset
    - data_array: numpy.array формы (N, 2), где
      столбец 0 — timestamp (сек с эпохи),
      столбец 1 — давление (Па)
    """
    p=p-2**16*(p>=2**13)
    p=p*100*2.5/2**13
    data_array=np.column_stack((time,p))
    if data_array is None or data_array.size == 0:
        print("Нет данных для записи.")
        return

    with h5py.File(h5_filename, 'a') as h5file:
        dataset = h5file[dataset_name]
        
        # Текущий размер
        current_size = dataset.shape[0]
        new_size = current_size + data_array.shape[0]
        
        # Расширяем dataset
        dataset.resize(new_size, axis=0)
        
        # Записываем массив сразу
        dataset[current_size:new_size] = data_array
        print('записано в ', h5_filename, 'массив ',data_array.shape)


def read_lcard(asp):
        if ldev.IoAsync(asp):
            x=asp.Data[0]
            return tm.time(), x


if __name__ == "__main__":
    with LCOMP(slot=0) as ldev:     # либо ldev.OpenLDevice() в начале и ldev.CloseLDevice() в конце

        # Асинхронные операции ввода/вывода

        asp = WASYNC_PAR()
        asp.NCh = 1                                   # 1 - 16                    1 - 8
        asp.Chn[0] = e140.CH_0 | e140.V10000 | e140.CH_DIFF     # для дифференциального режима

        asp.s_Type = L_ASYNC.ADC_INP
        
        p = np.array([])
        time = np.array([])
        pref='data/mbZai_'
        tmpdate = tm.strftime('%y%m%d%H%M', tm.localtime())
        filename = pref+tmpdate+'.h5'
        create_pressure_dataset(filename)

        interval_ms = 50
        interval_s = interval_ms / 1000.0  # 0.05 сек

        # Синхронизация: ждём наступления ближайшего кратного интервала
        start_time = tm.time()
        next_tick = ((int(start_time * 1000) // interval_ms) + 1) * interval_ms / 1000.0

        while True:
            # Вычисляем время до следующего тика
            sleep_time = next_tick - tm.time()
            if sleep_time > 0:
                tm.sleep(sleep_time)
            t0,p0 = read_lcard(asp)
            time = np.append(time, t0)
            p = np.append(p, p0)

            next_tick += interval_s

            timestamp = datetime.datetime.fromtimestamp(next_tick).strftime('%y%m%d%H%M')
            if timestamp[:-4] != tmpdate[:-4]:
                tmpdate = timestamp
                proc = Process(target=add_pressure_array, args=(filename, time, p))
                proc.start()
                proc.join()
                p = np.array([])
                time = np.array([])
                
                filename = pref+tmpdate+'.h5'
                proc = Process(target=create_pressure_dataset, args=(filename,))
                proc.start()
                proc.join()

            elif time.size == 600*20:
                proc = Process(target=add_pressure_array, args=(filename, time, p))
                proc.start()
                proc.join()
                p = np.array([])
                time = np.array([])
            
