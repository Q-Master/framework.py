# -*- coding:utf-8 -*-

import fcntl
import os

__all__ = ['PidFile', 'PidFileException']


class PidFileException(Exception):
    """Exception if can't lock pid file"""
    pass


class PidFile():
    """Working with pid file.
    Class might be used as a simple lock/unlock mechanism and as a context.
    e.x.
    with PidFile('/run/myapp.pid'):
        #do something
    or
    pid = PidFile('/run/myapp.pid')
    pid.lock()
    #do something
    pid.unlock()
    """
    pid_filename: str

    @property
    def is_locked(self):
        return self.fp is not None
    
    def __init__(self, filename: str):
        """Constructor

        Args:
            filename (str): pid-file name.
        """        
        super().__init__()
        self.pid_filename: str = filename
        self.fp = None
    
    def lock(self):
        """Exclusively lock the pid-file

        Raises:
            PidFileException: pid-file can't be opened exclusively
        """        
        fp = open(self.pid_filename, 'ab', 0)
        try:
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fp.truncate(0)
            fp.write(f'{os.getpid()}\n'.encode())
        except Exception as e:
            fp.close()
            raise PidFileException(*e.args)
        self.fp = fp
    
    def unlock(self, unlink: bool=True):
        """Unlock the file if locked.

        Args:
            unlink (bool, optional): remove the pid file after unlock. Defaults to True.
        """        
        if self.fp is not None:
            if unlink:
                self.__unlink()
            self.fp.close()
            self.fp = None
    
    def __unlink(self):
        try:
            os.unlink(self.pid_filename)
        except:
            pass

    def __enter__(self):
        self.lock()
        return self
    
    def __exit__(self, *args, **kwargs):
        self.unlock()
