import numpy as np
from matplotlib import scale as mscale
from matplotlib import transforms as mtransforms
from matplotlib.ticker import FixedLocator, FuncFormatter, LogFormatterSciNotation, LogLocator
from matplotlib.ticker import FuncFormatter, MaxNLocator

class CustomScale(mscale.ScaleBase):
    """
    Scales data in a custom way: linear for y < threshold, log for y >= threshold.
    """
    name = 'custom'

    def __init__(self, axis, *, threshold=50, **kwargs):
        super().__init__(axis)
        self.threshold = threshold
        self.large_fontsize = 10
        self.small_fontsize = 8
        self.his_fomatter = []
        self.minimum_log_tick = None
        self.maximum_log_tick = None

    def get_transform(self):
        return self.CustomTransform(self.threshold)

    def set_default_locators_and_formatters(self, axis):
        import matplotlib.ticker as ticker
        # Setting up custom tickers for both linear and log parts
        linear_ticks, log_ticks = self._calculate_major_ticks(axis.get_view_interval()[1])
        major_ticks = np.concatenate([linear_ticks, log_ticks])
        # Round major tickers to 1 decimal place (but in every case, show 1 decimal place)
        major_ticks = [round(tick, 3) if tick != 0 else 0.0 for tick in major_ticks]
        print(major_ticks)
        axis.set_major_locator(FixedLocator(major_ticks))
        # axis.set_minor_locator(ticker.AutoLocator())
        axis.set_major_formatter(FuncFormatter(self._custom_formatter))
        # axis.set_minor_formatter(FuncFormatter(self._custom_formatter))
        if len(log_ticks) > 0:
            self.minimum_log_tick = min(log_ticks)
            self.maximum_log_tick = max(log_ticks)
        
    def limit_range_for_scale(self, vmin, vmax, minpos):
        return max(vmin, 0), vmax

    def _custom_formatter(self, val, pos):
        if val < self.threshold:
            return f'{val}'
        elif val == self.minimum_log_tick or val == self.maximum_log_tick:
            return f'{val:.0e}'
        else:
            return ''
    
    def _calculate_major_ticks(self, ymax):
        if ymax < self.threshold:
            return np.linspace(0, ymax, 6), []
        else:
            linear_ticks = np.linspace(0, self.threshold, 5)
            log_ticks = np.logspace(np.log10(self.threshold + 1), np.log10(ymax), 5)
            return linear_ticks, log_ticks

    class CustomTransform(mtransforms.Transform):
        input_dims = output_dims = 1

        def __init__(self, threshold):
            mtransforms.Transform.__init__(self)
            self.threshold = threshold

        def transform_non_affine(self, a):
            linear_part = a < self.threshold
            log_part = a >= self.threshold
            result = np.empty_like(a)
            result[linear_part] = a[linear_part]
            result[log_part] = self.threshold + np.log(a[log_part] - self.threshold + 1)
            return result

        def inverted(self):
            return CustomScale.InvertedCustomTransform(self.threshold)

    class InvertedCustomTransform(mtransforms.Transform):
        input_dims = output_dims = 1

        def __init__(self, threshold):
            mtransforms.Transform.__init__(self)
            self.threshold = threshold

        def transform_non_affine(self, a):
            linear_part = a < self.threshold
            log_part = a >= self.threshold
            result = np.empty_like(a)
            result[linear_part] = a[linear_part]
            result[log_part] = np.exp(a[log_part] - self.threshold) + self.threshold - 1
            return result

        def inverted(self):
            return CustomScale.CustomTransform(self.threshold)

# Register the custom scale

# Register the custom scale
mscale.register_scale(CustomScale)