# E46 323i Related Code

This is the git repository related to my 2000 BMW E46 323i.
I'm using this repository to keep track of coding and ECU data.

# Table of Content

1. [Introduction](#introduction)
2. [Directories](#directories)
   1. [Tree](#tree)
   2. [ECU](#ecu)
      1. [Tests](#tests)
      1. [E85](#e85)
3. [Maths](#maths)

# Introduction

This E46 comes from Germany and has been made for the French market.
It thus has the european options by default.

Being a 323i with a M52TUB25 engine, the ECU is a MS42, with the version `0110C6`.  
The version of each module gotten via NCS Expert is written in the file name.

The stock injectors are _Siemens VDO 13537546244_, with a flow rate of 215cc/min (~20.5lb/h).

# Directories

## Tree

* E46_323i_backup
  * `/` contains the 32 and 512kb ROM files from the ECU. Extracted with 
    `Ms4x Flasher`
  * `/CODING` contains the stock module data. Extracted with `NCS Expert`
* ECU
  * `/` contains tuned maps
  * `/tests` contains maps only used for testing purposes
  * `/E85` maps relative to E85
* logs
  * `/RomRaider_logs` contains logs acquired by `RomRaider`

## ECU

This directory contains the tuned maps.
Currently, only maps for E85 are being developed.


### Tests

```
ECU/tests/
 - MS42_0110C6_32KB_hatrix_test_1.bin
```

This directory contains test bins. They are mostly used to try out some options
and see if everything, from tuning, flashing to operation, if working properly.

* MS42_0110C6_32KB_hatrix_test_1.bin
  * Engine Speed Soft Limiter (AT & MT): 4000 RPM
  * Engine Speed Hard Limiter (AT & MT): 4100 RPM
  * Throttle Body Speed: 60, instead of 44


### E85

```
ECU/E85/
 - MS42_0110C6_32KB_hatrix_E85_V0.1.bin
```

Each iteration is a modification upon the previous bin. The first one being
a difference to the stock bin.

* MS42_0110C6_32KB_hatrix_E85_V0.1.bin
  * Fuel Maps -> Multiplying by 1.3
    * Fuel Injection before Cranking: +30%
    * Cranking Fuel at Cold Engine Start: from +130% to +50%
    * Full Load Enrichment: +30%
    * Fuel Injection Base: +30%
    * Fuel Injection Idle Speed Warm Engine: +30%
    * Fuel Injection Idle Speed Cold Engine: +30%
    * Fuel Injection Part Load Bank 1 Warm Engine: +30%
    * Fuel Injection Part Load Bank 2 Warm Engine: +30%
  * Limiting the engine RPM -> Max duty cycle of 80%
    * Engine Speed Soft Limiter (AT & MT): 5000 RPM
    * Engine Speed Hard Limiter (AT & MT): 5100 RPM
    * Engine Speed Limiter (VSS Error): 5000 RPM
  * Full Load Recognition -> Turning off full load by putting max value
    * Full Load Basic: 120%
    * Full Load DISA Active: 120%
    * Full Load VANOS Active: 120%
  * Lambda Adaptation for flex fuel:
    * Multiplicative Fuel Learning - Min Limit: -30%
    * Multiplicative Fuel Learning - Min Limit: 30%
    * Multiplicative Fuel Learning - Min RPM: 600
  * MPG Gauge Correction -> divided by 1.3
* Further -> What to add next?
  * Multiplicative Fuel Learning - Min Load: ?
  * Additive Fuel Learning - Max RPM: ?
  * Idle Speed
    * Drive Engaged
    * Without Extra Load
    * With Drive + AC
    * With AC
  * Afterstart Enrichment
  * Fuel Injection Warmup Enrichment
  * Correct Full Load Enrichment to match E85 Max Power Rich AFR


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

$$D = \frac{IPW \cdot RPM}{1000} \cdot \frac{1}{60 \cdot 2} \cdot 100$$

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
