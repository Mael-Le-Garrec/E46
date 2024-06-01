# Notes

This document regroups some notes I've taken on diverse things. View it as a
personnal log regarding my tuning adventure.


## ECU Tuning

Some comments about the maps I've made.  
Refer to the [PDF](README.pdf) or [Markdown](README.md) README to find out what
maps have been changed.

### MS42_0110C6_32KB_hatrix_test_1.bin

This is my first map! Its intended purpose is to check that I can read and 
write maps from and to the ECU.

To keep things simple I decided to lower the hard and soft limiters to 4000
RPM. The _soft_ limiter cuts off some injectors whereas the _hard_ limiter cuts
off all injectors. After some warming up I decide to take the engine to higher
RPMs, and the cut does work! The car simply stops producing any power when it
reaches 4000 RPM.

I also changed the `Throttle Body Speed`, which is supposed to make the
throttle more responsive. I didn't see a big change, going from 44 to 60. The
maximum is 240 but I decided to play it safe, I will probably increase this
value for the next maps.  
The throttle is `drive by wire`, whatever the engine, M52TU or M54. Many people
on forums seem to think M52TU are only cable driven, and not electronic. The 
[MS42 Specs PDF](https://www.beisansystems.com/misc/SEIMENS_MS_420_ENGINE_CONTROL_SYSTEM.pdf)
by Siemens does though say that the cable is only a backup, and that the
system is indeed _drive by wire_. Look for `MDK`, page 51.

In summary, this map achieved what I wanted to do, full success!
After the test I reverted the car back to its original map.

### MS42_0110C6_32KB_hatrix_E85_V0.1.bin

This is my first E85 map! I only put 20 liters in the tank, on top of maybe 5
liters of E10, to be able to blend with E10 if something didn't work.

But turns out it does work! The engine cranks and starts smoothly. It must help
that the car was already warm when I did that.

I took a log of about 10 minutes with various loads. This log will not be used
to retune the map, but just to check some data.

The engine _does_ cut off at 5000 RPM, as intended, where the IPW is 9. This
seems low, it must be because of the remaining E10 in the tank. The load was
400mg/stroke, the IPW should then be ~11. In stock E10 map, the IPW would have
been around 9.16.
This is weird, as the IPW should be higher than that, even on stock map.

The max reached IPW is ~14.5 at 450 mg/stroke. This _does_ check out with the
map I made. There are probably some corrections being made.

The engine does crank correctly at cold start, the outside weather being +20°C
anyway.

The MPG Gauge is wrong, I'm using the same amount of fuel as before. I think
the ECU knows my injectors flow rate and knows how to calculate the appropriate
MPG. I probably shouldn't have divided that value, I will revert it.


----

After a drive of 1h30, the map seems actually good! The LTFT stay below 1% for
quite a long time and go to 2.5% at the end, probably because the load I was
using driving in the mountains wasn't too optimized.


### MS42_0110C6_32KB_hatrix_E85_V0.2.bin

This map only reverts the `MPG Fuel Gauge` table back to the original one.
The displayed fuel consumption seems to be ok now!

I though have some issues now: 
  * the car lacks some power
  * lambda values are higher (3% instead of 0.6%).
  * `68 - EVAP system, purge control valve circuit` DTC, probably related to
    the fuel cap being hard to close and open

After reverting to the first map I didn't notice any change in power. This map
isn't the problem.

I don't know if the code I got from the DME is related to the lack of power,
but I saw that it resets the lambda adaptations to 0 when it is created.

I couldn't test the fuel rail pressure, but I think my problem could come from
the fuel pump or the fuel filter. I ordered a fuel pump and we'll see if it's
better or not.


### MS42_0110C6_32KB_hatrix_E85_V0.3.bin

This map adds the Alpha/n map corrected for E85, I had forgotten it…
The MPG counter is correct, a bit less than 11L/100km for now.
The issue I felt with the v0.2 version was the fuel pump, everything seems OK
now!


### MS42_0110C6_32KB_hatrix_E85_V0.4.bin

I tested this map for a really short time. It has been made using the previous
1h30 log to infer a curve fore the load/IPW.
The values seemed a bit too rich (40% in some areas) but I decided to go with
it anyway.
Result: LTFT around -2.5. I decided to stop the test given that my assumptions
seemed to be true!
I will try a different fit or maybe I'll stick with the v0.3 for now.


### MS42_0110C6_32KB_hatrix_E85_V0.6.bin

Note on 2024-06-01, I've been using this map for two years now and it runs
great! It definitely is flex fuel as well, I've managed to use E5 without any
issue.
Cold start in the winter is just fine. Sometimes requires to crank twice but
quite rare.

