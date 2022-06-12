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
and see if everything, from tuning, flashing to operation, is working properly.

* MS42_0110C6_32KB_hatrix_test_1.bin
  * Engine Speed Soft Limiter (AT & MT): 4000 RPM
  * Engine Speed Hard Limiter (AT & MT): 4100 RPM
  * Throttle Body Speed: 60, instead of 44


### E85

```
ECU/E85/
 - MS42_0110C6_32KB_hatrix_E85_V0.1.bin
 - MS42_0110C6_32KB_hatrix_E85_V0.2.bin
 - MS42_0110C6_32KB_hatrix_E85_V0.3.bin
 - MS42_0110C6_32KB_hatrix_E85_V0.4.bin
```

Each iteration is a modification upon the previous bin. The first one being
a difference to the stock bin.

#### MS42_0110C6_32KB_hatrix_E85_V0.1.bin

This is the first map for my E85 tune. The engine should start and run without
too much trouble.

* Fuel Maps -> Multiplying by 1.3
  * Fuel Injection before Cranking: +30%
  * Cranking Fuel at Cold Engine Start: values ranging from +130% to +50%
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
* After Start Enrichment -> values ranging from 65% to 10%


#### MS42_0110C6_32KB_hatrix_E85_V0.2.bin

* MPG Gauge Correction -> Reverted to original values


#### MS42_0110C6_32KB_hatrix_E85_V0.3.bin

* Alpha/n Injection Table -> +30%


#### MS42_0110C6_32KB_hatrix_E85_V0.4.bin

Applied the function `0.0325611168538154 x +  -0.14561668444972975` with `x`
being the load, on the following maps:

* Fuel Injection Base
* Fuel Injection Part Load Bank 1 Warm Engine
* Fuel Injection Part Load Bank 2 Warm Engine


#### MS42_0110C6_32KB_hatrix_E85_V0.5.bin

This map is based on the V0.3 version.

* Changed the LTFT (Multiplicative Fuel Learning) limit values:
  * Minimum Limit: -35%, to account for a possible change for regular gas
  * Maximum Limit: +10%, to trigger a fault if too much gas is needed


#### Improvements

Below are listed improvements that could be made on that map.

* Activate Full Load
* Multiplicative Fuel Learning - Min Load: ?
* Additive Fuel Learning - Max RPM: ?
* Idle Speed
  * Drive Engaged
  * Without Extra Load
  * With Drive + AC
  * With AC
* Fuel Injection Warmup Enrichment
* Correct Full Load Enrichment to match E85 Max Power Rich AFR
