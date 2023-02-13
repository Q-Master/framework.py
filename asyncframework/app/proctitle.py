import setproctitle


__all__ = ['set_process_name']


def set_process_name(name: str):
    """Set process title.

    Args:
        name (str): name of the process
    """
    setproctitle.setproctitle(name)