"""
XIRR Calculation Example in Python
http://www.mftransparency.org/pages/2010/10/09/calculating-interest-rates-using-cashflow-discounting/

This script originally required the scipy and numpy libraries,
but these dependencies have been internalized to simplify deployment

How to Run:
    rename file to: xirr_example.py (remove txt extension)
    if python is installed, type:
        python xirr_example.py

    if python is not installed, you will need to install python:
        http://wiki.python.org/moin/BeginnersGuide/Download

To reduce debug output, change 'debug_each_guess' to False

Compiled by: Tim Langeman, MicroFinance Transparency <tim@mftransparency.org>

Credit: Skipper Seabold <jsseabold@gmail.com>
http://mail.scipy.org/pipermail/numpy-discussion/2009-May/042736.html
"""

from datetime import date
import time

debug_each_guess = True
guess = .30
guess_num = 1
guesses = []
discounted_cashflows = []


def newton(func, x0, fprime=None, args=(), tol=1.48e-8, maxiter=50):
    """Given a function of a single variable and a starting point,
    find a nearby zero using Newton-Raphson.

    fprime is the derivative of the function.  If not given, the
    Secant method is used.

    # Source: http://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.newton.html
    # File:   scipy.optimize.minpack.py
    # License: BSD: http://www.scipy.org/License_Compatibility
    """

    if fprime is not None:
        p0 = x0
        for iter in range(maxiter):
            myargs = (p0,) + args
            fval = func(*myargs)
            fpval = fprime(*myargs)
            if fpval == 0:
                print
                "Warning: zero-derivative encountered."
                return p0
            p = p0 - func(*myargs) / fprime(*myargs)
            if abs(p - p0) < tol:
                return p
            p0 = p
    else:  # Secant method
        p0 = x0
        p1 = x0 * (1 + 1e-4)
        q0 = func(*((p0,) + args))
        q1 = func(*((p1,) + args))
        for iter in range(maxiter):
            if q1 == q0:
                if p1 != p0:
                    print("Tolerance of %s reached" % (p1 - p0))
                return (p1 + p0) / 2.0
            else:
                p = p1 - q1 * (p1 - p0) / (q1 - q0)
            if abs(p - p1) < tol:
                return p
            p0 = p1
            q0 = q1
            p1 = p
            q1 = func(*((p1,) + args))
    raise RuntimeError("Failed to converge after %d iterations, value is %s" % (maxiter, p))


def eir_func(rate, pmts, dates):
    """Loop through the dates and calculate a discounted cashflow total

    This is a simple process, but the debug messages clutter it up to
    make it seem more complex than it is.  With the debug messages removed,
    it is very similar to eir_derivative_func, but with the EIR formula,
    rather than f'rate.

    Credit: http://mail.scipy.org/pipermail/numpy-discussion/2009-May/042736.html
    """

    print_debug_messages = False

    # Globals used for debug printing
    global guess_num
    global debug_each_guess
    global guesses

    if rate not in guesses:
        print_debug_messages = debug_each_guess
        guesses.append(rate)
        if print_debug_messages:
            print("-----------------------------------------------------------------------------------------------")
            print("Guess #%s:  %s" % (guess_num, rate))
            print("")
            print("   # DATE          # DAYS  CASHFLOW      DISCOUNTED    Formula: cf * (rate + 1)^(-days/365)")
            print("--------------------------------------------------------------------------------------------")
        guess_num += 1

    dcf = []
    for i, cf in enumerate(pmts):
        d = dates[i] - dates[0]
        discounted_period = cf * (rate + 1) ** (-d.days / 365.)
        dcf.append(discounted_period)

        if print_debug_messages:
            cf = "%.2f" % cf
            cf = cf.rjust(9, " ")
            discounted_period = '%.8f' % discounted_period
            formula = '%s * ((%0.10f + 1)^(-%d /365)) ' % (cf, rate, d.days)
            discounted_period = discounted_period.rjust(15, " ")
            print("  %2i %s  %3.0d days %s %s =%s" % (i, dates[i], d.days, cf, discounted_period, formula))

    discounted_cashflow = sum(dcf)

    if print_debug_messages:
        discounted_cashflow = "%.8f" % discounted_cashflow
        total = "total:".rjust(35, " ")
        print("%s %s" % (total, discounted_cashflow.rjust(15, " ")))
        print("")

    return discounted_cashflow


def eir_derivative_func(rate, pmts, dates):
    """Find the derivative or the EIR function, used for calculating
    Newton's method:

    http://en.wikipedia.org/wiki/Newton's_method

    EIR = cf*(1+rate)^d
    f'rate = cf*d*(rate+1)^(d-1)

    Credit: http://mail.scipy.org/pipermail/numpy-discussion/2009-May/042736.html
    """

    dcf = []
    for i, cf in enumerate(pmts):
        d = dates[i] - dates[0]
        n = (-d.days / 365.)
        dcf.append(cf * n * (rate + 1) ** (n - 1))
    return sum(dcf)


if __name__ == "__main__":
    ############################### MAIN CODE #############################
    rate = None
    dates = {}

    # Example: my/products/502/2062/
    payment_dates = [
        [2010, 6, 28],
        [2010, 7, 16],
        [2010, 8, 16],
        [2010, 9, 16],
        [2010, 10, 16],
        [2010, 11, 16],
        [2010, 12, 16],
        [2011, 1, 16],
        [2011, 2, 16],
        [2011, 3, 16],
        [2011, 4, 16],
        [2011, 5, 16],
        [2011, 6, 16],
        [2011, 7, 16],
    ]

    payments = [
        -4825,
        48,
        492,
        492,
        492,
        492,
        492,
        492,
        492,
        492,
        492,
        492,
        492,
        488,
    ]

    # Convert our list of dates into date types
    for i, dt in enumerate(payment_dates):
        dates[i] = date(*dt)

    # Begin Main Calculation
    timer_start = time.clock()
    if len(dates) > 1:
        f = lambda x: eir_func(x, payments, dates)
        derivative = lambda x: eir_derivative_func(x, payments, dates)
        try:
            print("*****************************************argv********************************")
            print(f)
            print(guess)
            print(derivative)
            print("*****************************************argv********************************")
            rate = newton(f, guess, fprime=derivative, args=(),
                          tol=0.00000000001, maxiter=100)
        except RuntimeError:
            pass  # failed to converge after maxiterations

    timer_end = time.clock()
    # End Main Calculation

    elapsed_time = timer_end - timer_start
    final_rate = rate * 100

    if not debug_each_guess:
        print("")
        print("Cashflow Dates: ")
        print("-------------------------")
        for i, dte in enumerate(payment_dates):
            print("%s %s " % (date(*dte), str(payments[i]).rjust(5, " ")))

    print("""Guesses Summary------------------""")

    for i, guess in enumerate(guesses):
        print(i + 1, "%0.10f" % guess)

    print("""Final Rate: %.5f %%""" % final_rate)
    print("""Calculation time: %s seconds""" % elapsed_time)
