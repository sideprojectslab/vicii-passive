# VIC-II Graphics Generator Notes

## Latching Strobe

A certain strobe is selected for latching in relevant properties of a character, hereinafter the "latching strobe". In this implementation such strobe should be 15 or 1 (of the next cycle)

Values latched on the latching strobe are:

* xscroll (register)
* matrix data (color info equal for all lines of a character starting from the badline). This info is read repeatedly from the video matrix RAM
* memory data (dot information, different for each line). This data comes directly from the memory bus with each new character

Notes:

* memory_data => mem_data_s => shift_p
* matrix_data => mtx_data_s => colors_p
* xscroll => xscroll_p

## Loading Strobe

When the raster is equal to the scroll value, we have the "loading strobe". On the loading strobe more values are latched:

* graphics data is loaded into the shift register
* multicolor flag is saved bmm
* colors_p => colors => colors_d => color-out
* bsel_d can be taken directly from colors_d instead of creating another delay
* while colors_p is used to determine color-out, colors is used to determine the multi-color flag on the fly within multicolor modes
* shift_p => shreg => bits_d => color-out
