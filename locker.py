import fcntl
import os
import logging
import datetime
import settings

logger = logging.getLogger()


class LockConflictException(Exception):
    pass


def one_thread_restriction(key, raise_exception=False):
    def func_wrapper(func):
        def wrapper(*args, **kwargs):
            lockfile = None
            try:
                if callable(key):
                    key_str = key(*args, **kwargs)
                else:
                    key_str = key

                path_to_lockfile = os.path.join(settings.LOCKFILES_DIR, 'lockfile_%s'  % key_str)
                lockfile = open(path_to_lockfile, 'a+')
                fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                logger.warning('Attempt to start a second worker: (lockfile: %s) %s, %s, %s', path_to_lockfile, func, args, kwargs)
                result = None
                has_conflict = True
            else:
                lockfile.write('\n===================\n%s %s %s %s\n' % (datetime.datetime.now(), func, args, kwargs))
                result = func(*args, **kwargs)
                has_conflict = False
            finally:
                lockfile and lockfile.close()

            if raise_exception and has_conflict:
                raise LockConflictException(error_msg='Cannot run command because another process acquire lock. Please wait and restart command.')

            return result
        return wrapper
    return func_wrapper
