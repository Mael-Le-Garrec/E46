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
