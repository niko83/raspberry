import fcntl
import os
import logging
import datetime
import settings
import time

logger = logging.getLogger()


class LockConflictException(Exception):
    pass


def one_thread_restriction(key_str):
    def func_wrapper(func):
        def wrapper(*args, **kwargs):
            lockfile = None
            cnt = 10
            while cnt > 0:
                try:
                    path_to_lockfile = os.path.join(settings.LOCKFILES_DIR, 'lockfile_%s'  % key_str)
                    lockfile = open(path_to_lockfile, 'a+')
                    fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except IOError:
                    logger.warning('Attempt to start a second worker: (lockfile: %s) %s, %s, %s', path_to_lockfile, func, args, kwargs)
                    result = None
                    has_conflict = True
                    cnt -= 1
                    time.sleep(0.1)
                else:
                    lockfile.write('\n===================\n%s %s %s %s\n' % (datetime.datetime.now(), func, args, kwargs))
                    result = func(*args, **kwargs)
                    has_conflict = False
                    break
                finally:
                    lockfile and lockfile.close()

            if has_conflict:
                raise LockConflictException('Cannot run command because another process acquire lock. Please wait and restart command.')

            return result
        return wrapper
    return func_wrapper
