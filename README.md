Установка драйвера на репку:
$ sudo dpkg-reconfigure locales
$ git clone --recurse-submodules https://gitlab.com/l-card/acq/devices/emodules/shared/lcomp/drivers/lcomp_driver_linux.git
$ cd lcomp_driver_linux/
$ cmake .
$ sudo make lcomp-dkms-install

Установка питоновских библиотек (скомпилированные библиотеки для репки включены в репозиторий)
$ git clone https://github.com/red-wat-shod/mbr_lcard.git
$ sudo apt-get install python3-setuptools python3-numpy python3-h5py
$ python3 setup.py build
$ sudo python3 setup.py install
