def _wrap_with_color_code(code: str):
    def inner(self, text, bold=False):
        c = code
        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)

    return inner


class Logging(object):
    def __init__(self, level: int):
        self.log_level = level

    LOG_INFO = 1
    LOG_WARN = 2
    LOG_ERROR = 3

    red = _wrap_with_color_code('31')
    green = _wrap_with_color_code('32')
    yellow = _wrap_with_color_code('33')
    blue = _wrap_with_color_code('34')
    magenta = _wrap_with_color_code('35')
    cyan = _wrap_with_color_code('36')
    white = _wrap_with_color_code('37')

    def error(self, msg, *args, **kwargs):
        if self.log_level <= self.LOG_ERROR:
            print(self.red("[ERROR]"), msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        if self.log_level <= self.LOG_WARN:
            print(self.yellow("[WARN]"), msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if self.log_level <= self.LOG_INFO:
            print(self.green("[INFO]"), msg, *args, **kwargs)

