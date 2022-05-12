# E46 323i Related Code

This is the git repository related to my 2000 BMW E46 323i.
I'm using this repository to keep track of coding and ECU data.

## Information

This E46 comes from Germany and has been made for the French market.
It thus has the european options by default.

Being a 323i with a M52TUB25 engine, the ECU is a MS42, with the version `0110C6`.  
The version of each module gotten via NCS Expert is written in the file name.

The stock injectors are _Siemens VDO 13537546244_, with a flow rate of 215cc/min (~20.5lb/h).

## Directories

* E46_323i_backup
  * `/` contains the 32 and 512kb ROM files from the ECU. Extracted with 
    `Ms4x Flasher`
  * `/CODING` contains the stock module data. Extracted with `NCS Expert`


## Maths

Here will be listed some useful formulas when tuning an engine.

### Injector Duty Cycle

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

$$D = \frac{IPW \cdot RPM}{1000} \cdot \frac{1}{60 \cdot 2} \cdot 100$$

#### Example 

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
