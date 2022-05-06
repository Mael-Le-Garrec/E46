# E46 323i Related Code

This is the git repository related to my 2000 BMW E46 323i.
I'm using this repository to keep track of coding and ECU data.

## Information

This E46 comes from Germany and has been made for the French market.
It thus has the european options by default.

Being a 323i with a M52TUB25 engine, the ECU is an MS42, with the version `0110C6`.
The version of each module gotten via NCS Expert is written in the file name.

The stock injectors are _Siemens VDO 13537546244_, with a flow rate of 215cc/min (~20.5lb/h).

## Directories

* E46_323i_backup
  * `/` contains the 32 and 512kb ROM files from the ECU. Extracted with 
    `Ms4x Flasher`
  * `/CODING` contains the stock module data. Extracted with `NCS Expert`
