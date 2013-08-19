import time
import sys


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2,
          sleep_func=time.sleep, max_delay=sys.maxint):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    Args:
        ExceptionToCheck: exception to check. May be a tuple of
            exceptions to check.
        tries: an integer, number of times to try (not retry) before
            giving up.
        delay: an integer, initial delay between retries in seconds.
        backoff: an integer, backoff multiplier e.g. value of 2 will
            double the delay each retry
        sleep_func: the sleep function to be used for waiting between
            retries. By default, it is ``time.sleep``,
            but it could also be gevent.sleep if we are using this with
            gevent.
        max_delay: the max number of seconds to wait between retries.

    Returns:
        Decorator function.

    """
    def deco_retry(f):

        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    sleep_func(mdelay)
                    mtries -= 1
                    mdelay *= backoff
                    # Don't wait more than max_delay allowed
                    if mdelay > max_delay:
                        mdelay = max_delay
            return f(*args, **kwargs)

        return f_retry

    return deco_retry