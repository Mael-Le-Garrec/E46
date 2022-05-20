# Maths

Here will be listed some useful formulas when tuning an engine.

## Injector Duty Cycle

A duty cycle is the fraction of one period during which a signal is active.
The easiest way to understand it: it is the percentage of time the injector is
active during a cycle of the engine.
[Wikipedia](https://en.wikipedia.org/wiki/Duty_cycle) has a great article,
especially the gif on the side.  

Usually you'd want to stay around 80% maximum duty cycle. Above that threhsold
the injectors might not be working as expected by design.

$$D = \frac{IPW}{T} \cdot 100%$$

where $D$ is the duty cycle, $IPW$ the Injector Pulse Width and $T$ the period.
$IPW$ and $T$ are both units of time, they need to be in the same order of
magnitude, usually here milliseconds ($ms$) are used.

An easy calculation based on RPM is given by:

$$\begin{aligned}
D &= \frac{IPW \cdot RPM}{1000} \cdot \frac{1}{60 \cdot 2} \cdot 100
  &= \frac{IPW \cdot RPM}{1200}
\end{aligned}$$

When tuning an engine for more fuel without changing injectors (e.g. E85), it is
useful to know what's the maximum RPM achievable. This is given by:

$$RPM = D \cdot \frac{1000 \cdot 60 \cdot 2}{IPW \cdot 100}$$


### Example 

An engine at 7000 RPM does 117 revolutions per second (7000 / 60).  
By inverting, we get the seconds per revolution: 0.0086 (1 / 117), which is
8.6 ms.

A four stroke engine has 4 cycles spanning on 2 revolutions of the crankshaft.
Instead of having seconds per revolution, we'll use seconds per _cycle_, which
is the double of our previous value: 17.14ms.

Now, let's say we want our injectors to be on for 13 ms, this gets us to the
duty cycle $D$ below:

$$D = \frac{13}{17.14} \cdot 100 = 75.8 \%$$

Using the formula from above relating the duty cycle and the RPM:

$$\begin{aligned}
  D &= \frac{13 \cdot 7000}{1000} \cdot \frac{1}{120} \cdot 100 \\
    &= 75.83 \%
\end{aligned}$$

This maximum duty cycle is considered safe. If the $IPW$ were to be higher than
$17.14$ in this case, the duty cycle would be higher than 100%. An injector
can't be opened longer than all the time, the mixture would then be lean.  
To fix that, either lower the maximum RPM or get higher injectors (to reduce
the $IPW$).

Now let's say we're tuning our engine for E85. We need 30% more fuel and we
want to stay at 80% duty cycle without changing the injectors.  
The maximum injector pulse width given by the fuel map of my engine is 16.11ms.
This is at maximum load (throttle open at maximum).  
Adding 30% more fuel gives us 21ms (16.11 * 1.3).

The safe RPM achievable with this IPW is then:

$$\begin{aligned}
RPM &= 80 \cdot \frac{1000 \cdot 60 \cdot 2}{21 \cdot 100} \\
    &= 4570
\end{aligned}$$
